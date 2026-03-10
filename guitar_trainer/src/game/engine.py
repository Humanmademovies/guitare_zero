import random
import time
from dataclasses import dataclass
from .guitar_map import GUITAR_MAP
from .settings import GameSettings
from ..core.highscore import HighScoreManager

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

        # Historique pour le Radar (x=timing, y=pitch, time=ticks)
        self.hit_history = []
        
    def load_quest(self, campaign_id, quest_data):
        self.quest_mode = True
        self.quest_data = quest_data
        self.current_campaign_id = campaign_id
        self.active_notes = []
        self.next_note_idx = 0
        self.song_time_beats = -4.0
        
        self.start_game()
        self.stats.lives = quest_data["params"].get("max_lives", 0)
        
        count = len(quest_data["params"].get("sequence", []))
        self.max_quest_score = (count * 300) + (self.stats.lives * 500)
        
        self.hit_history = [] # Reset du radar à chaque début de quête
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
            self._update_quest_mode(features, dt)
        else:
            self._update_arcade_mode(features, dt)

    def _update_quest_mode(self, features, dt: float):
        bpm = self.quest_data["params"]["tempo"]
        self.song_time_beats += dt * (bpm / 60.0)
        tol_t = self.quest_data["params"]["tolerance_timing"]
        tol_p = self.quest_data["params"]["tolerance_pitch"]
        seq = self.quest_data["params"]["sequence"]

        while self.next_note_idx < len(seq):
            n = seq[self.next_note_idx]
            if self.song_time_beats + 4.0 >= n["beat"]:
                note_name = "???"
                for name, pos_list in GUITAR_MAP.items():
                    if (n["string"], n["fret"]) in pos_list:
                        note_name = name
                        break
                
                self.active_notes.append({
                    "string": n["string"], "fret": n["fret"],
                    "note": note_name, "beat": n["beat"],
                    "status": "pending"
                })
                self.next_note_idx += 1
            else:
                break

        for n in self.active_notes:
            if n["status"] == "pending" and self.song_time_beats > n["beat"] + tol_t:
                n["status"] = "missed"
                self._handle_miss()

        target = next((n for n in self.active_notes if n["status"] == "pending"), None)
        if target:
            self.target_note = target["note"]
            self.target_position = (target["string"], target["fret"])
            
            if features.note_name == target["note"] and features.stable:
                timing_err = self.song_time_beats - target["beat"]
                if abs(timing_err) <= tol_t:
                    target["status"] = "hit"
                    self._handle_success(timing_err=timing_err, pitch_err=features.cents)

        self.active_notes = [n for n in self.active_notes if self.song_time_beats < n["beat"] + 1.0]
        
        if self.next_note_idx >= len(seq) and not self.active_notes:
            self._handle_victory()

    def _update_arcade_mode(self, features, dt: float):
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
            
            # Normalisation de l'erreur entre 0 et 1 pour le score
            norm_err = (abs(timing_err) / tol_t + abs(pitch_err) / tol_p) / 2.0
            bonus = int(200 * (1.0 - norm_err))
            self.stats.score += (100 + max(0, bonus))

            # Ajout au radar (normalisé entre -1.0 et 1.0)

            self.hit_history.append({
                "x": timing_err / tol_t,
                "y": pitch_err / tol_p,
                "time": time.time() * 1000
            })
            # On garde les 10 derniers points pour le nuage
            if len(self.hit_history) > 30:
                self.hit_history.pop(0)
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
            
            # Sauvegarde du score (toujours)
            manager.save_quest_score(camp_id, quest_id, self.quest_percent)
            
            # Vérification des conditions de victoire pour débloquer la suite
            requirements = self.quest_data.get("params", {}).get("requirements", {})
            min_percent = requirements.get("min_percent", 0)
            
            if self.quest_percent >= min_percent:
                if self.quest_data.get("next_quest"):
                    manager.unlock_quest(camp_id, self.quest_data["next_quest"])
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
