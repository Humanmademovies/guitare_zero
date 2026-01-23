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
        
        self.knob_gate  = Knob(start_x + step_x*0, knob_y, knob_radius, "GATE", cfg.rms_threshold, 0.0, 1.0)
        self.knob_drive = Knob(start_x + step_x*1, knob_y, knob_radius, "DRIVE", 0.0, 0.0, 1.0)
        self.knob_vol   = Knob(start_x + step_x*2, knob_y, knob_radius, "VOL", 0.8, 0.0, 1.0)
        
        self.status_light = StatusLight((W - 50, self.H_GAME + 50), 20)
        
        # Feedback Visuel
        self.vu_meter = VUMeter(W - 30, self.H_GAME + 20, 15, self.H_CTRL - 40)
        
        self.lbl_detected = TextLabel(self.font_info, (self.cx, self.H_GAME + 25), align="center")
        self.lbl_detected.set_text("Waiting...", (100, 100, 100))

    def handle_event(self, event):
        engine = self.controller.game_engine

        # 1. Gestion des Écrans de Fin
        if engine.state in ["GAME_OVER", "VICTORY"]:
            # Clic ou Touche = Retour Setup
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self.app.change_screen("setup")
            return

        # 2. Navigation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                engine.stop_game()
                self.app.change_screen("menu")
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

        # 4. Potards
        if self.knob_gate.handle_event(event):
            self.controller.set_audio_gate(self.knob_gate.val)
        if self.knob_drive.handle_event(event):
            self.controller.set_audio_drive(self.knob_drive.val)
        if self.knob_vol.handle_event(event):
            self.controller.set_audio_volume(self.knob_vol.val)

    def update(self, dt: float):
        feats = self.state.get_features_snapshot()
        if feats:
            self.status_light.set_active(feats.stable)
            self.knob_gate.val = self.cfg.rms_threshold
            self.vu_meter.set_value(feats.rms)
            self.vu_meter.threshold = self.cfg.rms_threshold
            
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
        if self.controller.game_engine.settings.show_helper:
            self._draw_tab_helper(surface)
        else:
            txt = self.font_small.render("[MODE AVEUGLE]", True, (255, 200, 50))
            surface.blit(txt, (self.cx - txt.get_width()//2, int(self.H * 0.15)))
        
        # 5. CONTROLES
        pygame.draw.rect(surface, (20, 20, 30), self.rect_ctrl)
        pygame.draw.line(surface, (50, 50, 50), (0, self.H_GAME), (self.W, self.H_GAME), 2)
        
        self.knob_gate.draw(surface)
        self.knob_drive.draw(surface)
        self.knob_vol.draw(surface)
        self.status_light.draw(surface)
        
        self.vu_meter.draw(surface)
        self.lbl_detected.draw(surface)
        
        # 6. SETTINGS
        pygame.draw.rect(surface, (100, 100, 120), self.rect_settings, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), self.rect_settings, 2, border_radius=5)
        s_txt = self.font_info.render("S", True, (255, 255, 255))
        surface.blit(s_txt, (self.rect_settings.centerx - s_txt.get_width()//2, 
                             self.rect_settings.centery - s_txt.get_height()//2))

        # 7. INFO AUDIO
        self._draw_device_info(surface)

        # 8. OVERLAYS (FIN DE PARTIE + HIGHSCORES)
        self._draw_game_over_overlay(surface)

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
        if engine.state == "IDLE" or (engine.target_position is None and engine.state != "MISS"):
            return
            
        if not engine.target_position: return

        string_idx, fret_idx = engine.target_position
        visual_string_idx = 6 - string_idx 
        
        progress = min(1.0, engine.state_timer / engine.settings.note_duration)
        
        if engine.state == "SUCCESS":
            progress = 0.9
            color = COLOR_NOTE_HIT
            radius = 35 + int(math.sin(pygame.time.get_ticks()*0.02)*5)
        elif engine.state == "MISS":
            progress = 0.95
            color = (255, 0, 0)
            radius = 30
        else:
            color = COLOR_NOTE_TARGET
            radius = 30
            
        y = self.neck_top_y + (self.neck_bottom_y - self.neck_top_y) * progress
        current_neck_w = self.neck_top_w + (self.neck_bottom_w - self.neck_top_w) * progress
        factor = visual_string_idx / 5.0
        x = (self.cx - current_neck_w//2) + (current_neck_w * factor)
        
        pygame.draw.circle(surface, color, (int(x), int(y)), radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), radius, 3)

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
        
        txt_note = self.font_score.render(f"NOTE: {note_name}", True, (255, 255, 255))
        surface.blit(txt_note, (self.cx - txt_note.get_width()//2, panel_y + 10))
        
        helper_str = f"CORDE {string_num}   |   CASE {fret_num}"
        txt_col = (0, 255, 0) if engine.state == "SUCCESS" else (255, 200, 50)
        if engine.state == "MISS": txt_col = (255, 0, 0)
        
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
            surface.blit(msg, (self.cx - msg.get_width()//2, self.H_GAME * 0.6))
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