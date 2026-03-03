import pygame
import math
from .base import Screen
from ..widgets.knob import Knob
from ..widgets.text import TextLabel
from ..widgets.status_light import StatusLight
from ..widgets.vu_meter import VUMeter

# Couleurs
COLOR_BG = (10, 10, 15)
COLOR_NECK = (40, 30, 30)
COLOR_FRET = (100, 100, 100)
COLOR_STRING = (150, 150, 150)
COLOR_NOTE_TARGET = (0, 255, 255) # Cyan
COLOR_NOTE_HIT = (0, 255, 0)      # Vert
COLOR_TEXT = (255, 255, 255)
COLOR_HEART = (255, 50, 50)       # Rouge Cœur

class GameScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        
        W, H = cfg.window_size
        self.W, self.H = W, H
        
        # --- ZONES D'ÉCRAN ---
        self.H_GAME = int(H * 0.8)
        self.H_CTRL = H - self.H_GAME
        self.rect_ctrl = pygame.Rect(0, self.H_GAME, W, self.H_CTRL)
        
        # Bouton Settings
        self.rect_settings = pygame.Rect(W - 60, 20, 40, 40)
        
        # --- CONFIGURATION DU "HIGHWAY" ---
        self.neck_bottom_w = int(W * 0.6)
        self.neck_top_w = int(W * 0.15)
        self.neck_top_y = int(H * 0.25) 
        self.neck_bottom_y = self.H_GAME
        self.cx = W // 2
        
        # --- FONTS ---
        self.font_score = pygame.font.SysFont("monospace", int(H * 0.08), bold=True)
        self.font_big = pygame.font.SysFont("monospace", int(H * 0.10), bold=True)
        self.font_info = pygame.font.SysFont("monospace", int(H * 0.04))
        self.font_tab = pygame.font.SysFont("monospace", int(H * 0.05), bold=True)
        self.font_small = pygame.font.SysFont("monospace", int(H * 0.03)) 
        
        # --- WIDGETS ---
        knob_y = self.rect_ctrl.centery
        knob_radius = int(self.H_CTRL * 0.35)
        start_x = int(W * 0.2)
        step_x = int(W * 0.15)
        
        
        self.lbl_detected = TextLabel(self.font_info, (self.cx, self.H_GAME + 25), align="center")
        self.lbl_detected.set_text("Waiting...", (100, 100, 100))
        # Garde seulement ça pour le dessin
        self.y_hit = int(self.neck_bottom_y * 0.9)

    def handle_event(self, event):
        engine = self.controller.game_engine

        # 1. Gestion des Écrans de Fin
        if engine.state in ["GAME_OVER", "VICTORY"]:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                target = "quest_result" if engine.quest_mode else "setup"
                self.app.change_screen(target)
                return

        # 2. Navigation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                engine.stop_game()
                target = "quest_list" if engine.quest_mode else "menu"
                self.app.change_screen(target)
                return
            
            # Audio Device
            if event.key == pygame.K_RIGHT: self.controller.cycle_input_device(1)
            if event.key == pygame.K_LEFT: self.controller.cycle_input_device(-1)
            if event.key == pygame.K_UP: self.controller.cycle_output_device(1)
            if event.key == pygame.K_DOWN: self.controller.cycle_output_device(-1)

        # 3. Settings
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect_settings.collidepoint(event.pos):
                engine.stop_game()
                self.app.change_screen("setup")
                return


    def update(self, dt: float):
        feats = self.state.get_features_snapshot()
        if feats:
            
            engine = self.controller.game_engine
            if feats.note_name:
                is_correct = (feats.note_name == engine.target_note)
                color = (0, 255, 0) if is_correct else (255, 50, 50)
                self.lbl_detected.set_text(f"ENTENDU : {feats.note_name}", color)
            else:
                self.lbl_detected.set_text("...", (80, 80, 80))

    def draw(self, surface):
        surface.fill(COLOR_BG)
        
        # 1. MANCHE
        self._draw_highway(surface)
        
        # 2. CIBLE
        self._draw_target(surface)
        
        # 3. HUD
        self._draw_hud(surface)

        # 4. AIDE
        self._draw_tab_helper(surface)
        
        # 5. CONTROLES (Le fond de la barre du bas)
        pygame.draw.rect(surface, (20, 20, 30), self.rect_ctrl)
        pygame.draw.line(surface, (50, 50, 50), (0, self.H_GAME), (self.W, self.H_GAME), 2)
        
        self.lbl_detected.draw(surface)
        
        # 6. SETTINGS
        pygame.draw.rect(surface, (100, 100, 120), self.rect_settings, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), self.rect_settings, 2, border_radius=5)
        s_txt = self.font_info.render("S", True, (255, 255, 255))
        surface.blit(s_txt, (self.rect_settings.centerx - s_txt.get_width()//2, 
                             self.rect_settings.centery - s_txt.get_height()//2))

        # 7. INFO AUDIO
        self._draw_device_info(surface)

        # --- 8. LE RADAR DE PRÉCISION ---
        # On l'appelle ici pour qu'il soit dessiné par-dessus tout le reste
        if self.controller.game_engine.quest_mode:
            self._draw_precision_radar(surface)

        # 9. OVERLAYS (FIN DE PARTIE)
        self._draw_game_over_overlay(surface)
    
    def _draw_precision_radar(self, surface):
        engine = self.controller.game_engine
        
        # Placement : Centré (cx) et dans la barre du bas (cy)
        cx = self.cx
        cy = self.H_GAME + (self.H_CTRL // 2)
        radar_size = int(self.H_CTRL * 0.7)
        
        # Fond du radar
        bg_rect = pygame.Rect(0, 0, radar_size + 40, radar_size + 30)
        bg_rect.center = (cx, cy)
        pygame.draw.rect(surface, (15, 20, 25), bg_rect, border_radius=10)
        pygame.draw.rect(surface, (0, 255, 255), bg_rect, 2, border_radius=10)
        
        # Croix du radar
        color_axis = (200, 200, 200)
        pygame.draw.line(surface, color_axis, (cx - radar_size//2, cy), (cx + radar_size//2, cy), 2)
        pygame.draw.line(surface, color_axis, (cx, cy - radar_size//2), (cx, cy + radar_size//2), 2)
        
        # Dessin du nuage de points (Persistance de 6 secondes)
        now = pygame.time.get_ticks()
        for i, hit in enumerate(engine.hit_history):
            age = now - hit["time"]
            if age > 6000: continue
            
            # Fondu beaucoup plus lent
            alpha = max(0, 255 - int((age / 6000.0) * 255))
            px = cx + int(hit["x"] * (radar_size // 2))
            py = cy + int(hit["y"] * (radar_size // 2))
            
            is_last = (i == len(engine.hit_history) - 1)
            color = (0, 255, 255) if is_last else (255, 100, 100)
            radius = 6 if is_last else 4
            
            # Point avec alpha
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (radius, radius), radius)
            surface.blit(s, (px - radius, py - radius))

        # Légendes
        f = pygame.font.SysFont("monospace", 12, bold=True)
        surface.blit(f.render("TÔT", True, color_axis), (cx - radar_size//2 - 35, cy - 6))
        surface.blit(f.render("TARD", True, color_axis), (cx + radar_size//2 + 5, cy - 6))
        surface.blit(f.render("HAUT", True, color_axis), (cx - 15, cy - radar_size//2 - 20))
        surface.blit(f.render("BAS", True, color_axis), (cx - 12, cy + radar_size//2 + 5))

    def _draw_highway(self, surface):
        points = [
            (self.cx - self.neck_top_w//2, self.neck_top_y),
            (self.cx + self.neck_top_w//2, self.neck_top_y),
            (self.cx + self.neck_bottom_w//2, self.neck_bottom_y),
            (self.cx - self.neck_bottom_w//2, self.neck_bottom_y)
        ]
        pygame.draw.polygon(surface, COLOR_NECK, points)
        
        for i in range(6):
            factor = i / 5.0
            x_top = (self.cx - self.neck_top_w//2) + (self.neck_top_w * factor)
            x_bot = (self.cx - self.neck_bottom_w//2) + (self.neck_bottom_w * factor)
            color = COLOR_STRING
            width = 3 if i < 3 else 1
            pygame.draw.line(surface, color, (x_top, self.neck_top_y), (x_bot, self.neck_bottom_y), width)
            
        y_hit = int(self.neck_bottom_y * 0.9)
        pygame.draw.line(surface, (200, 200, 200), 
                         (self.cx - self.neck_bottom_w//2, y_hit), 
                         (self.cx + self.neck_bottom_w//2, y_hit), 4)

    def _draw_target(self, surface):
        engine = self.controller.game_engine
        
        # En mode Arcade, on utilise l'ancienne logique de dessin unique
        if not engine.quest_mode:
            if engine.state == "IDLE" or not engine.target_position: return
            self._draw_single_note(surface, engine.target_position, engine.state, engine.state_timer)
            return

        # En mode Quête, on dessine tout le pipeline
        for n in engine.active_notes:
            beats_left = n["beat"] - engine.song_time_beats
            
            # Calcul Y : 4.0 beats de distance entre haut et impact
            # y_hit est la ligne d'impact, neck_top_y est le sommet
            pixels_per_beat = (self.y_hit - self.neck_top_y) / 4.0
            y = self.y_hit - (beats_left * pixels_per_beat)
            
            # Calcul Perspective X (0.0 en haut, 0.9 à l'impact)
            progress = max(0.0, 0.9 - (beats_left * 0.225)) # 0.9 / 4.0 = 0.225
            
            # Couleur selon statut
            if n["status"] == "hit": color = COLOR_NOTE_HIT
            elif n["status"] == "missed": color = (255, 0, 0)
            else: color = COLOR_NOTE_TARGET
            
            # Position X
            visual_string_idx = 6 - n["string"]
            current_neck_w = self.neck_top_w + (self.neck_bottom_w - self.neck_top_w) * progress
            x = (self.cx - current_neck_w//2) + (current_neck_w * (visual_string_idx / 5.0))
            
            # Dessin
            radius = 30
            if n["status"] == "hit": radius += int(math.sin(pygame.time.get_ticks()*0.02)*5)
            
            pygame.draw.circle(surface, color, (int(x), int(y)), radius)
            pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), radius, 2)
            
            # Chiffre de la frette à l'intérieur
            txt_f = self.font_small.render(str(n["fret"]), True, (0, 0, 0) if n["status"] == "hit" else (255, 255, 255))
            surface.blit(txt_f, (x - txt_f.get_width()//2, y - txt_f.get_height()//2))

    def _draw_single_note(self, surface, pos, state, timer):
        """Helper pour garder le mode Arcade fonctionnel."""
        engine = self.controller.game_engine
        string_idx, fret_idx = pos
        visual_string_idx = 6 - string_idx
        progress = min(1.0, timer / engine.settings.note_duration)
        if state == "SUCCESS": progress = 0.9
        elif state == "MISS": progress = 0.95
        
        y = self.neck_top_y + (self.neck_bottom_y - self.neck_top_y) * progress
        current_neck_w = self.neck_top_w + (self.neck_bottom_w - self.neck_top_w) * progress
        x = (self.cx - current_neck_w//2) + (current_neck_w * ((6-string_idx) / 5.0))
        
        color = COLOR_NOTE_HIT if state == "SUCCESS" else (255, 0, 0) if state == "MISS" else COLOR_NOTE_TARGET
        pygame.draw.circle(surface, color, (int(x), int(y)), 30)
        pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), 30, 2)

    def _draw_tab_helper(self, surface):
        engine = self.controller.game_engine
        if not engine.target_position: return

        string_num, fret_num = engine.target_position 
        note_name = engine.target_note
        
        panel_w = int(self.W * 0.4)
        panel_h = int(self.H * 0.15)
        panel_x = self.cx - panel_w // 2
        panel_y = int(self.H * 0.05) 
        
        rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (10, 30, 40), rect, border_radius=15)
        pygame.draw.rect(surface, (0, 200, 200), rect, 2, border_radius=15)
        
        # 1. LA NOTE (TOUJOURS VISIBLE)
        txt_note = self.font_score.render(f"NOTE: {note_name}", True, (255, 255, 255))
        surface.blit(txt_note, (self.cx - txt_note.get_width()//2, panel_y + 10))
        
        # 2. L'AIDE (CONDITIONNELLE)
        if engine.settings.show_helper:
            # Mode Normal : On donne la solution
            helper_str = f"CORDE {string_num}   |   CASE {fret_num}"
            txt_col = (0, 255, 0) if engine.state == "SUCCESS" else (255, 200, 50)
            if engine.state == "MISS": txt_col = (255, 0, 0)
        else:
            # Mode Aveugle : On cache la solution
            helper_str = "? ? ?"
            txt_col = (255, 50, 50) # Rouge pour montrer que c'est Hardcore

        txt_help = self.font_tab.render(helper_str, True, txt_col)
        surface.blit(txt_help, (self.cx - txt_help.get_width()//2, panel_y + panel_h//2 + 10))

    def _draw_hud(self, surface):
        engine = self.controller.game_engine
        stats = engine.stats
        settings = engine.settings
        
        score_txt = self.font_score.render(f"{stats.score}", True, (255, 255, 0))
        surface.blit(score_txt, (50, 50))
        
        mult_txt = self.font_info.render(f"x{stats.multiplier}", True, (200, 200, 200))
        surface.blit(mult_txt, (50 + score_txt.get_width() + 10, 70))
        
        lbl_score = self.font_info.render("SCORE", True, (150, 150, 150))
        surface.blit(lbl_score, (50, 30))
        
        lives_str = "♥ " * stats.lives
        lives_txt = self.font_score.render(lives_str, True, COLOR_HEART)
        surface.blit(lives_txt, (self.W - lives_txt.get_width() - 50, 50))
        
        prog_str = f"NOTE: {stats.notes_played} / {settings.total_notes}"
        prog_txt = self.font_info.render(prog_str, True, (100, 200, 255))
        surface.blit(prog_txt, (self.W - prog_txt.get_width() - 50, 110))

        if engine.state == "SUCCESS":
            msg = self.font_score.render("PARFAIT !", True, (0, 255, 0))
            surface.blit(msg, (self.cx - msg.get_width()//2, 20)) # Tout en haut
        elif engine.state == "MISS":
            msg = self.font_score.render("RATÉ !", True, (255, 0, 0))
            surface.blit(msg, (self.cx - msg.get_width()//2, self.H_GAME * 0.6))

    def _draw_device_info(self, surface):
        in_id = self.cfg.device_name_or_index
        out_id = self.cfg.output_device_name_or_index
        
        in_name = str(in_id)
        for d in self.state.get_input_devices():
            if d['index'] == in_id: 
                in_name = d['name']
                break
        
        out_name = str(out_id) if out_id is not None else "System Default"
        for d in self.state.get_output_devices():
            if d['index'] == out_id: 
                out_name = d['name']
                break

        txt_in = self.font_small.render(f"In (L/R): {in_name}", True, (100, 100, 100))
        txt_out = self.font_small.render(f"Out (U/D): {out_name}", True, (100, 100, 100))
        
        surface.blit(txt_out, (self.W - txt_out.get_width() - 20, self.H - 10))
        surface.blit(txt_in, (self.W - txt_in.get_width() - 20, self.H - 30))

    def _draw_game_over_overlay(self, surface):
        engine = self.controller.game_engine
        
        if engine.state not in ["GAME_OVER", "VICTORY"]:
            return
            
        # Fond sombre
        overlay = pygame.Surface((self.W, self.H))
        overlay.set_alpha(240) # Très sombre pour bien lire
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # --- 1. TITRE ---
        if engine.state == "VICTORY":
            title_text = "VICTOIRE !"
            color = (0, 255, 0)
        else:
            title_text = "GAME OVER"
            color = (255, 0, 0)
            
        txt_title = self.font_big.render(title_text, True, color)
        surface.blit(txt_title, (self.cx - txt_title.get_width()//2, int(self.H * 0.1)))
        
        # --- 2. SCORE ACTUEL ---
        txt_score = self.font_score.render(f"SCORE FINAL: {engine.stats.score}", True, (255, 255, 255))
        surface.blit(txt_score, (self.cx - txt_score.get_width()//2, int(self.H * 0.2)))
        
        # --- 3. TABLEAU DES HIGHSCORES ---
        lbl_top = self.font_info.render("--- MEILLEURS SCORES ---", True, (0, 255, 255))
        surface.blit(lbl_top, (self.cx - lbl_top.get_width()//2, int(self.H * 0.35)))
        
        scores = engine.hs_manager.get_top_scores()
        start_y = int(self.H * 0.42)
        step_y = int(self.H * 0.05)
        
        for i, entry in enumerate(scores):
            # Couleur dorée pour le 1er, argent pour le 2e, etc.
            if i == 0: col = (255, 215, 0)
            elif i == 1: col = (192, 192, 192)
            elif i == 2: col = (205, 127, 50)
            else: col = (150, 150, 150)
            
            # Format:  1. 15000 pts  |  24/01 14:30  |  x3.5
            line_str = f"{i+1}. {entry.score} pts   |   {entry.date}   |   {entry.difficulty}"
            txt_line = self.font_small.render(line_str, True, col)
            surface.blit(txt_line, (self.cx - txt_line.get_width()//2, start_y + i * step_y))
        
        # --- 4. INSTRUCTION ---
        txt_info = self.font_info.render("Appuyer sur une touche pour continuer", True, (255, 255, 255))
        
        # Clignotement
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            surface.blit(txt_info, (self.cx - txt_info.get_width()//2, self.H - 80))
