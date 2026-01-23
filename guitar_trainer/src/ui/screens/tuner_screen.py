import pygame
import numpy as np
from .base import Screen

# --- CORRECTION DES IMPORTS ---
# On importe chaque widget depuis son fichier spécifique
from ..widgets.spectrogram import SpectrogramWidget
from ..widgets.oscilloscope import OscilloscopeWidget
from ..widgets.text import TextLabel
from ..widgets.vu_meter import VUMeter
from ..widgets.status_light import StatusLight
from ..widgets.knob import Knob

class TunerScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        
        W, H = cfg.window_size
        CX = W // 2
        
        MARGIN_X = int(W * 0.05)
        VIZ_Y    = int(H * 0.30)
        VIZ_H    = int(H * 0.40)
        CTRL_Y   = int(H * 0.75)
        CTRL_H   = int(H * 0.20)

        self.rect_viz = pygame.Rect(MARGIN_X, VIZ_Y, W - (2 * MARGIN_X), VIZ_H)
        self.rect_ctrl = pygame.Rect(MARGIN_X, CTRL_Y, W - (2 * MARGIN_X), CTRL_H)

        font_big_size = int(H * 0.12)  
        font_small_size = int(H * 0.03)
        self.font_big = pygame.font.SysFont("monospace", font_big_size, bold=True)
        self.font_small = pygame.font.SysFont("monospace", font_small_size)

        self.spectro_widget = SpectrogramWidget(self.rect_viz, max_history=state.max_history)
        self.oscillo_widget = OscilloscopeWidget(self.rect_viz)

        self.lbl_note = TextLabel(self.font_big, (CX, int(H * 0.12)), align="center")
        self.lbl_info = TextLabel(self.font_small, (CX, int(H * 0.23)), align="center")
        
        # VU Meter
        vu_w = 40
        vu_h = int(self.rect_ctrl.height * 0.7)
        vu_x = self.rect_ctrl.x + 30
        vu_y = self.rect_ctrl.centery - (vu_h // 2)
        
        self.vu_meter = VUMeter(vu_x, vu_y, vu_w, vu_h)
        self.lbl_vu = TextLabel(self.font_small, (vu_x + vu_w//2, vu_y + vu_h + 10), align="center")
        self.lbl_vu.set_text("MIC")
        
        # --- 5 POTARDS ---
        start_x = self.rect_ctrl.x + 120
        width_available = self.rect_ctrl.width - 140
        knob_y = self.rect_ctrl.centery
        knob_radius = int(self.rect_ctrl.height * 0.22)
        
        step = width_available / 5
        
        # 1. GATE
        k1_x = start_x + step * 0.5
        self.knob_gate = Knob(int(k1_x), knob_y, knob_radius, "GATE", cfg.rms_threshold, 0.0, 1.0)
        
        # 2. PURITY
        k2_x = start_x + step * 1.5
        self.knob_pure = Knob(int(k2_x), knob_y, knob_radius, "PURE", cfg.flatness_threshold, 0.0, 1.0)

        # 3. DRIVE
        k3_x = start_x + step * 2.5
        self.knob_drive = Knob(int(k3_x), knob_y, knob_radius, "DRIVE", 0.0, 0.0, 1.0)
        
        # 4. TONE
        k4_x = start_x + step * 3.5
        self.knob_tone = Knob(int(k4_x), knob_y, knob_radius, "TONE", 0.8, 0.0, 1.0)

        # 5. VOLUME
        k5_x = start_x + step * 4.5
        self.knob_vol = Knob(int(k5_x), knob_y, knob_radius, "VOL", 0.8, 0.0, 1.0)

        self.status_light = StatusLight((W - 50, 50), 20)
        self.lbl_stable = TextLabel(self.font_small, (W - 80, 40), align="topright")
        self.lbl_stable.set_text("STABLE")

    def handle_event(self, event):
        # Gestion des potards
        if self.knob_gate.handle_event(event):
            self.controller.set_audio_gate(self.knob_gate.val)

        self.knob_pure.handle_event(event)
        
        if self.knob_drive.handle_event(event):
            self.controller.set_audio_drive(self.knob_drive.val)
        
        if self.knob_tone.handle_event(event):
            self.controller.set_audio_tone(self.knob_tone.val)
            
        if self.knob_vol.handle_event(event):
            self.controller.set_audio_volume(self.knob_vol.val)

        # Clavier
        if event.type == pygame.KEYDOWN:
            # --- NAVIGATION RETOUR ---
            if event.key == pygame.K_ESCAPE:
                self.app.change_screen("menu")
            # -------------------------

            if event.key == pygame.K_SPACE:
                self.controller.toggle_audio()
            
            # Changement Micros
            if event.key == pygame.K_RIGHT:
                self.controller.cycle_input_device(1)
            if event.key == pygame.K_LEFT:
                self.controller.cycle_input_device(-1)

            # Changement Enceintes
            if event.key == pygame.K_UP:
                self.controller.cycle_output_device(1)
            if event.key == pygame.K_DOWN:
                self.controller.cycle_output_device(-1)

    def update(self, dt: float):
        feats = self.state.get_features_snapshot()
        if feats is None:
            return
        
        # Mise à jour de la config via les potards
        self.cfg.rms_threshold = self.knob_gate.val
        self.cfg.flatness_threshold = self.knob_pure.val
        
        # Mise à jour des widgets visuels
        self.vu_meter.set_value(feats.rms)
        self.vu_meter.threshold = self.cfg.rms_threshold
        self.status_light.set_active(feats.stable)
        
        if feats.is_voiced and feats.note_name:
            # Vert si juste (< 10 cents), Blanc sinon
            color = (0, 255, 0) if abs(feats.cents) < 10 else (255, 255, 255)
            self.lbl_note.set_text(feats.note_name, color)
            self.lbl_info.set_text(f"{feats.f0_hz:.1f} Hz  |  {feats.cents:+.0f} cts")
        else:
            self.lbl_note.set_text("...", (100, 100, 100))
            self.lbl_info.set_text("No Signal")

    def draw(self, surface):
        surface.fill((15, 15, 20))
        
        # Cadres
        pygame.draw.rect(surface, (40, 40, 50), self.rect_viz, 2, border_radius=10)
        pygame.draw.rect(surface, (40, 40, 50), self.rect_ctrl, 2, border_radius=10)
        
        # Widgets Graphiques
        history = self.state.get_spectrogram_history()
        self.spectro_widget.draw(surface, history)

        feats = self.state.get_features_snapshot()
        if feats:
            self.oscillo_widget.draw(surface, feats.samples)
            
            # Glow vert autour de la zone de viz si stable
            if feats.stable:
                glow_color = (0, 255, 100)
                pygame.draw.rect(surface, glow_color, self.rect_viz, 6, border_radius=10)

        # Widgets Texte & Status
        self.lbl_note.draw(surface)
        self.lbl_info.draw(surface)
        self.vu_meter.draw(surface)
        self.lbl_vu.draw(surface)
        self.status_light.draw(surface)
        self.lbl_stable.draw(surface)
        
        # Potards
        self.knob_gate.draw(surface)
        self.knob_pure.draw(surface)
        self.knob_drive.draw(surface)
        self.knob_tone.draw(surface)
        self.knob_vol.draw(surface)

        # Affichage des infos Périphériques (En bas à droite)
        self._draw_device_info(surface)

    def _draw_device_info(self, surface):
        """Helper pour afficher proprement les infos de périphériques"""
        in_id = self.cfg.device_name_or_index
        out_id = self.cfg.output_device_name_or_index
        
        # Récupération du nom lisible pour l'INPUT
        in_name = str(in_id)
        for d in self.state.get_input_devices():
            if d['index'] == in_id: 
                in_name = d['name']
                break
        
        # Récupération du nom lisible pour l'OUTPUT
        out_name = str(out_id) if out_id is not None else "System Default"
        for d in self.state.get_output_devices():
            if d['index'] == out_id: 
                out_name = d['name']
                break

        txt_in = self.font_small.render(f"In (L/R): {in_name}", True, (150, 150, 150))
        txt_out = self.font_small.render(f"Out (U/D): {out_name}", True, (150, 150, 150))
        
        bottom_margin = 10
        right_margin = 20
        
        # Positionnement
        surface.blit(txt_out, (self.rect_ctrl.right - txt_out.get_width() - right_margin, self.rect_ctrl.bottom - bottom_margin))
        surface.blit(txt_in, (self.rect_ctrl.right - txt_in.get_width() - right_margin, self.rect_ctrl.bottom - bottom_margin - 30))