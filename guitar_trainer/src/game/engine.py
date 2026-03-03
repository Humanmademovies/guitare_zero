import random
from dataclasses import dataclass
from .guitar_map import GUITAR_MAP
from .settings import GameSettings
from ..core.highscore import HighScoreManager  # Import du gestionnaire

# --- ÉTATS DU JEU ---
STATE_IDLE = "IDLE"           
STATE_PICK = "PICK_NOTE"      
STATE_LISTEN = "LISTENING"    
STATE_SUCCESS = "SUCCESS"     
STATE_MISS = "MISS"           
STATE_GAME_OVER = "GAME_OVER" 
STATE_VICTORY = "VICTORY"     

@dataclass
class GameStats:
    score: int = 0
    streak: int = 0
    notes_played: int = 0
    correct_notes: int = 0
    missed_notes: int = 0
    lives: int = 3          
    multiplier: float = 1.0 

class GameEngine:
    def __init__(self, cfg, controller=None):
        self.controller = controller
        self.state = STATE_IDLE
        self.settings = GameSettings()
        self.stats = GameStats()
        self.hs_manager = HighScoreManager()
        self.initialized = False 
        
        # Cibles (Pipeline)
        self.target_note = None     
        self.target_position = None 
        self.active_notes = [] # Liste des notes à l'écran
        
        # Timers et Rythme
        self.state_timer = 0.0      
        self.reaction_time = 0.0
        self.quest_mode = False
        self.quest_data = None
        self.current_campaign_id = None
        self.song_time_beats = 0.0
        self.next_note_idx = 0
	
	# scoring quêtes
        self.max_quest_score = 0
        self.quest_percent = 0.0
        
    def load_quest(self, campaign_id, quest_data):
        self.quest_mode = True
        self.quest_data = quest_data
        self.current_campaign_id = campaign_id
        self.active_notes = []
        self.next_note_idx = 0
        self.song_time_beats = -4.0
        
        # 1. On lance la remise à zéro des stats
        self.start_game()
        
        # 2. On injecte les vies du JSON (0 = infini)
        self.stats.lives = quest_data["params"].get("max_lives", 0)
        
        # 3. Sécurité : on récupère la séquence ou une liste vide si elle n'existe pas
        sequence = quest_data["params"].get("sequence", [])
        count = len(sequence)
        
        # 4. Calcul du score maximum (on évite le crash si count est 0)
        self.max_quest_score = (count * 300) + (self.stats.lives * 500)
        
        self.initialized = True

    def start_game(self):
        # Initialisation propre des statistiques
        self.stats = GameStats()
        
        if not self.quest_mode:
            self.stats.lives = self.settings.max_lives
        self.state = STATE_LISTEN if self.quest_mode else STATE_PICK
        self.stats.multiplier = self.settings.get_multiplier()
        self.target_position = None
        print(f"[GAME] START! Multiplier: x{self.stats.multiplier}")

    def update(self, features, dt: float):
        if self.state in [STATE_IDLE, STATE_GAME_OVER, STATE_VICTORY]:
            return

        self.state_timer += dt
        
        if self.quest_mode:
            # 1. Progression du temps musical
            bpm = self.quest_data["params"]["tempo"]
            self.song_time_beats += dt * (bpm / 60.0)
            tol_t = self.quest_data["params"]["tolerance_timing"]
            tol_p = self.quest_data["params"]["tolerance_pitch"]

            # 2. Injection des notes dans le pipeline (Anticipation de 4 beats)
            seq = self.quest_data["params"]["sequence"]
            while self.next_note_idx < len(seq):
                n = seq[self.next_note_idx]
                if self.song_time_beats + 4.0 >= n["beat"]:
                    # Identifier le nom de la note
                    note_name = "???"
                    for name, pos_list in GUITAR_MAP.items():
                        if (n["string"], n["fret"]) in pos_list:
                            note_name = name
                            break
                    
                    self.active_notes.append({
                        "string": n["string"], "fret": n["fret"],
                        "note": note_name, "beat": n["beat"],
                        "status": "pending" # pending, hit, missed
                    })
                    self.next_note_idx += 1
                else:
                    break

            # 3. Vérification des "Miss" (notes qui ont dépassé la ligne)
            for n in self.active_notes:
                if n["status"] == "pending" and self.song_time_beats > n["beat"] + tol_t:
                    n["status"] = "missed"
                    self._handle_miss()

            # 4. Vérification de l'entrée utilisateur sur la note la plus proche
            target = next((n for n in self.active_notes if n["status"] == "pending"), None)
            if target:
                # Mise à jour des variables pour l'affichage du HUD/Aide
                self.target_note = target["note"]
                self.target_position = (target["string"], target["fret"])
                
                if features.note_name == target["note"] and features.stable:
                    if abs(self.song_time_beats - target["beat"]) <= tol_t:
                            target["status"] = "hit"
                            # On passe les erreurs pour le calcul du score
                            t_err = self.song_time_beats - target["beat"]
                            p_err = features.cents
                            self._handle_success(timing_err=t_err, pitch_err=p_err)

            # 5. Nettoyage et Victoire
            # On garde les notes 1 beat après l'impact pour l'effet visuel
            self.active_notes = [n for n in self.active_notes if self.song_time_beats < n["beat"] + 1.0]
            
            if self.next_note_idx >= len(seq) and not self.active_notes:
                self._handle_victory()
                
        else:
            # --- LOGIQUE ARCADE CLASSIQUE (Inchangée) ---
            if self.state == STATE_PICK:
                if self.stats.notes_played >= self.settings.total_notes:
                    self._handle_victory()
                    return
                self._pick_smart_note()
                self.state = STATE_LISTEN
                self.state_timer = 0.0
            elif self.state == STATE_LISTEN:
                if features.note_name == self.target_note and features.stable:
                    self.reaction_time = self.state_timer
                    self._handle_success()
                elif self.state_timer > self.settings.note_duration:
                    self._handle_miss()
            elif self.state in [STATE_SUCCESS, STATE_MISS]:
                if self.state_timer > (1.0 if self.state == STATE_SUCCESS else 0.5):
                    if self.stats.lives > 0: self.state = STATE_PICK
                    else: self._handle_game_over()
                    
    def stop_game(self):
        self.state = STATE_IDLE
        
    def _handle_success(self, timing_err=0.0, pitch_err=0.0):
        self.stats.notes_played += 1
        self.stats.correct_notes += 1
        self.stats.streak += 1
        
        if self.quest_mode:
            tol_t = self.quest_data["params"]["tolerance_timing"]
            tol_p = self.quest_data["params"]["tolerance_pitch"]
            # Normalisation de l'erreur entre 0 et 1
            norm_err = (abs(timing_err) / tol_t + abs(pitch_err) / tol_p) / 2.0
            bonus = int(200 * (1.0 - norm_err))
            final_points = 100 + max(0, bonus)
        else:
            speed_factor = 1.0 - (self.reaction_time / self.settings.note_duration)
            final_points = int((100 + max(0, speed_factor * 200)) * self.stats.multiplier)
        
        self.stats.score += final_points
        self.state = STATE_SUCCESS
        self.state_timer = 0.0

    def _handle_miss(self):
        self.stats.notes_played += 1
        self.stats.missed_notes += 1
        self.stats.streak = 0
        
        # Si on a des vies configurées (> 0), on en perd une
        if self.stats.lives > 0:
            self.stats.lives -= 1
            # Si on tombe à zéro, c'est Game Over
            if self.stats.lives == 0:
                self._handle_game_over()
        
        self.state = STATE_MISS
        self.state_timer = 0.0
        print(f"[GAME] MISS! Lives left: {self.stats.lives}")

    def _handle_game_over(self):
        self.state = STATE_GAME_OVER
        if not self.quest_mode:
            self.hs_manager.add_score(self.stats.score, self.stats.multiplier)
        print("[GAME] GAME OVER")

    def _handle_victory(self):
        life_bonus = self.stats.lives * 500
        self.stats.score += life_bonus
        self.state = STATE_VICTORY
        
        if self.quest_mode:
            if self.max_quest_score > 0:
                self.quest_percent = (self.stats.score / self.max_quest_score) * 100
            
            manager = self.controller.campaign_manager
            camp_id = self.current_campaign_id
            quest_id = self.quest_data["id"]
            
            # Sauvegarde du score persistant
            manager.save_quest_score(camp_id, quest_id, self.quest_percent)
            
            # Déblocage de la suivante
            if self.quest_data.get("next_quest"):
                manager.unlock_quest(camp_id, self.quest_data["next_quest"])
            
            if hasattr(self.controller, 'app') and self.controller.app:
                self.controller.app.change_screen("quest_result")
        else:
            self.hs_manager.add_score(self.stats.score, self.stats.multiplier)
            
        print(f"[GAME] VICTORY! Final Score: {self.stats.score} ({self.quest_percent:.1f}%)")

    def _pick_smart_note(self):
        candidates = []
        for note_name, positions in GUITAR_MAP.items():
            valid_positions = []
            for (string, fret) in positions:
                if string in self.settings.active_strings:
                    if self.settings.min_fret <= fret <= self.settings.max_fret:
                        valid_positions.append((string, fret))
            if valid_positions:
                candidates.append((note_name, valid_positions[0]))

        if not candidates:
            self.state = STATE_IDLE
            return

        filtered_candidates = []
        if self.target_position and self.settings.max_jump > 0:
            prev_string, prev_fret = self.target_position
            for note, (s, f) in candidates:
                fret_distance = abs(f - prev_fret)
                if fret_distance <= self.settings.max_jump:
                    filtered_candidates.append((note, (s, f)))
        else:
            filtered_candidates = candidates

        if not filtered_candidates: filtered_candidates = candidates
        final_pool = [x for x in filtered_candidates if x[0] != self.target_note]
        if not final_pool: final_pool = filtered_candidates

        self.target_note, self.target_position = random.choice(final_pool)
