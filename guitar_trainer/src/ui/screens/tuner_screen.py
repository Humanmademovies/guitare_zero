import pygame
from .base import Screen
from ..widgets.text import TextLabel
from ..widgets.vu_meter import VUMeter
from ..widgets.status_light import StatusLight
from ..widgets.knob import Knob
import math

class TunerScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        
        # Initialisation des Polices (Agrandies pour la nouvelle résolution)
        self.font_big = pygame.font.SysFont("monospace", 150, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 35)
        
        W, H = cfg.window_size # (1600, 1200)
        CX, CY = W // 2, H // 2

        # --- Définition des Zones (Phase 1) ---
        
        # Zone Visualisation (Centre) - Rectangle pour accueillir Spectro/Oscillo
        self.rect_viz = pygame.Rect(50, 350, W - 100, 500)
        
        # Zone Contrôles (Bas) - Rectangle pour accueillir Potards/VU
        self.rect_ctrl = pygame.Rect(50, 900, W - 100, 250)

        # --- Création et repositionnement des Widgets ---
        
        # 1. Note Principale (Haut - Zone Feedback)
        self.lbl_note = TextLabel(self.font_big, (CX, 150), align="center")
        
        # 2. Infos techniques (Hz / Cents) - sous la note
        self.lbl_info = TextLabel(self.font_small, (CX, 280), align="center")
        
        # 3. VU Mètre (déplacé dans la zone de contrôle)
        self.vu_meter = VUMeter(80, 950, 40, 180)
        self.lbl_vu = TextLabel(self.font_small, (100, 920), align="center")
        self.lbl_vu.set_text("MIC")
        
        # 4. Voyant de stabilité (Repositionné en haut à droite)
        self.status_light = StatusLight((W - 80, 80), 25)
        self.lbl_stable = TextLabel(self.font_small, (W - 130, 65), align="topright")
        self.lbl_stable.set_text("STABLE")
        # Potards de contrôle (Valeurs optimisées pour guitare électrique)
        # Gate Vol : 0.0 à 0.02 (le signal d'une guitare est souvent très bas en RMS)
        self.knob_vol = Knob(400, 1025, 60, "NOISE GATE", cfg.rms_threshold, 0.0, 1.0)
        # Purity : 0.0 (Pure) à 0.5 (Bruit) - La zone utile dépasse rarement 0.3
        self.knob_pure = Knob(650, 1025, 60, "PURITY", cfg.flatness_threshold, 0.0, 1.0)

    def handle_event(self, event):
        # Gestion des potards (Phase 3)
        self.knob_vol.handle_event(event)
        self.knob_pure.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.controller.toggle_audio()
            # --- RETOUR AU CODE D'ORIGINE ---
            if event.key == pygame.K_RIGHT:
                self.controller.cycle_input_device(1)
            if event.key == pygame.K_LEFT:
                self.controller.cycle_input_device(-1)

    def update(self, dt: float):
        # Récupération instantanée de l'état (Thread-Safe)
        feats = self.state.get_features_snapshot()
        
        # GARDE : On attend que le moteur audio produise des données
        if feats is None:
            return
        
        # Mise à jour de l'historique du spectrogramme
        if feats.spectrum is not None:
            self.state.spectrogram_history.append(feats.spectrum)
            if len(self.state.spectrogram_history) > self.state.max_history:
                self.state.spectrogram_history.pop(0)

        # Les mises à jour de seuils et de labels restent identiques
        self.cfg.rms_threshold = self.knob_vol.val
        self.cfg.flatness_threshold = self.knob_pure.val
        self.vu_meter.set_value(feats.rms)
        self.vu_meter.threshold = self.cfg.rms_threshold
        self.status_light.set_active(feats.stable)
        
        # 2. Mise à jour Note et Info
        if feats.is_voiced and feats.note_name:
            color = (0, 255, 0) if abs(feats.cents) < 10 else (255, 255, 255)
            self.lbl_note.set_text(feats.note_name, color)
            self.lbl_info.set_text(f"{feats.f0_hz:.1f} Hz  |  {feats.cents:+.0f} cts")
        else:
            self.lbl_note.set_text("...", (100, 100, 100))
            self.lbl_info.set_text("No Signal")

        # 3. Mise à jour Voyant Stabilité
        self.status_light.set_active(feats.stable)

    def draw(self, surface):
        # Fond sombre
        surface.fill((15, 15, 20))
        
        # Récupération sécurisée du snapshot
        feats = self.state.get_features_snapshot()
        
        # Dessin des cadres de zones
        pygame.draw.rect(surface, (40, 40, 50), self.rect_viz, 2, border_radius=10)
        pygame.draw.rect(surface, (40, 40, 50), self.rect_ctrl, 2, border_radius=10)
        
        # 1. Dessin du Spectrogramme
        history = self.state.spectrogram_history
        if history:
            num_cols = len(history)
            col_width = self.rect_viz.width / self.state.max_history
            num_bins = 120 
            bin_height = self.rect_viz.height / num_bins
            
            for i, spec in enumerate(history):
                x = self.rect_viz.x + i * col_width
                for j in range(num_bins):
                    intensity = min(255, int(math.log1p(spec[j]) * 50))
                    if intensity > 10:
                        color = (intensity // 2, intensity, intensity // 4)
                        y = self.rect_viz.bottom - (j * bin_height)
                        pygame.draw.rect(surface, color, (x, y - bin_height, int(col_width) + 1, int(bin_height) + 1))

        # 2. Dessin de l'Oscilloscope
        if feats and feats.samples is not None and len(feats.samples) > 0:
            points = []
            step = self.rect_viz.width / len(feats.samples)
            center_y = self.rect_viz.centery
            amp = self.rect_viz.height * 0.4
            for i in range(0, len(feats.samples), 2):
                px = self.rect_viz.x + i * step
                py = center_y + feats.samples[i] * amp
                points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(surface, (0, 255, 255), False, points, 2)

        # 3. Effet visuel de STABILITÉ
        if feats and feats.stable:
            glow_color = (0, 255, 100)
            pygame.draw.rect(surface, glow_color, self.rect_viz, 6, border_radius=10)

        # Labels et Widgets
        self.lbl_note.draw(surface)
        self.lbl_info.draw(surface)
        self.vu_meter.draw(surface)
        self.lbl_vu.draw(surface)
        self.status_light.draw(surface)
        self.lbl_stable.draw(surface)
        self.knob_vol.draw(surface)
        self.knob_pure.draw(surface)

        # --- CODE D'ORIGINE REPOSITIONNÉ ---
        dev_name = str(self.cfg.device_name_or_index)
        txt_dev = self.font_small.render(f"Micro: {dev_name} (Arrows to change)", True, (150, 150, 150))
        surface.blit(txt_dev, (850, 1100))
    
    def _update_device_label(self):
        # Récupère le nom lisible du device actuel
        dev_id = self.cfg.device_name_or_index
        devices = self.state.get_input_devices()
        
        dev_name = "Unknown"
        # Si c'est un string (ex: 'H4'), on l'affiche direct
        if isinstance(dev_id, str):
            dev_name = dev_id
        else:
            # Sinon on cherche dans la liste
            for d in devices:
                if d['index'] == dev_id:
                    dev_name = d['name']
                    break
                    
        self.lbl_device.set_text(f"< {dev_name} >", (100, 200, 255))