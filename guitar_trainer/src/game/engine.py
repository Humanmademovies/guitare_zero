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
    def __init__(self, cfg):
        self.cfg = cfg
        self.state = STATE_IDLE
        self.settings = GameSettings()
        self.stats = GameStats()
        
        # Gestionnaire de High Score intégré au moteur
        self.hs_manager = HighScoreManager()
        
        self.initialized = False 
        
        # Cible
        self.target_note = None     
        self.target_position = None 
        
        # Timers
        self.state_timer = 0.0      
        self.reaction_time = 0.0    

    def start_game(self):
        """Lance une session."""
        self.stats = GameStats()
        
        self.stats.lives = self.settings.max_lives
        self.stats.multiplier = self.settings.get_multiplier()
        
        self.state = STATE_PICK
        self.target_position = None
        
        print(f"[GAME] START! Multiplier: x{self.stats.multiplier}")

    def stop_game(self):
        self.state = STATE_IDLE

    def update(self, features, dt: float):
        if self.state in [STATE_IDLE, STATE_GAME_OVER, STATE_VICTORY]:
            return

        self.state_timer += dt

        # --- 1. VÉRIFICATION FIN DE PARTIE ---
        if self.state == STATE_PICK:
            if self.stats.notes_played >= self.settings.total_notes:
                self._handle_victory()
                return
            
            self._pick_smart_note()
            self.state = STATE_LISTEN
            self.state_timer = 0.0 

        # --- 2. JEU (ÉCOUTE) ---
        elif self.state == STATE_LISTEN:
            if features.note_name == self.target_note and features.stable:
                self.reaction_time = self.state_timer
                self._handle_success()
                return

            if self.state_timer > self.settings.note_duration:
                self._handle_miss()
                return

        # --- 3. TRANSITIONS ---
        elif self.state in [STATE_SUCCESS, STATE_MISS]:
            duration = 1.0 if self.state == STATE_SUCCESS else 0.5
            
            if self.state_timer > duration:
                if self.stats.lives > 0:
                    self.state = STATE_PICK
                else:
                    self._handle_game_over()

    def _handle_success(self):
        self.stats.notes_played += 1
        self.stats.correct_notes += 1
        self.stats.streak += 1
        
        speed_factor = 1.0 - (self.reaction_time / self.settings.note_duration)
        base_points = 100 + int(max(0, speed_factor * 200))
        final_points = int(base_points * self.stats.multiplier)
        
        self.stats.score += final_points
        self.state = STATE_SUCCESS
        self.state_timer = 0.0
        print(f"[GAME] SUCCESS! +{final_points} pts")

    def _handle_miss(self):
        self.stats.notes_played += 1
        self.stats.missed_notes += 1
        self.stats.streak = 0
        self.stats.lives -= 1
        
        self.state = STATE_MISS
        self.state_timer = 0.0
        print(f"[GAME] MISS! Lives left: {self.stats.lives}")

    def _handle_game_over(self):
        self.state = STATE_GAME_OVER
        # Sauvegarde du score
        self.hs_manager.add_score(self.stats.score, self.stats.multiplier)
        print("[GAME] GAME OVER - Score Saved")

    def _handle_victory(self):
        life_bonus = self.stats.lives * 500
        self.stats.score += life_bonus
        self.state = STATE_VICTORY
        # Sauvegarde du score
        self.hs_manager.add_score(self.stats.score, self.stats.multiplier)
        print(f"[GAME] VICTORY! Final Score: {self.stats.score}")

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