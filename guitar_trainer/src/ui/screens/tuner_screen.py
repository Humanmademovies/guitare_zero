import pygame
from .base import Screen
from ..widgets.text import TextLabel
from ..widgets.vu_meter import VUMeter
from ..widgets.status_light import StatusLight

class TunerScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        
        # Initialisation des Polices (Fallback sur monospace si arial absent)
        self.font_big = pygame.font.SysFont("monospace", 120, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 30)
        
        W, H = cfg.window_size
        CX, CY = W // 2, H // 2

        # --- Création des Widgets ---
        
        # 1. Note Principale (au centre)
        self.lbl_note = TextLabel(self.font_big, (CX, CY - 50), align="center")
        
        # 2. Infos techniques (Hz / Cents) - sous la note
        self.lbl_info = TextLabel(self.font_small, (CX, CY + 60), align="center")
        
        # 3. VU Mètre (sur le côté gauche)
        self.vu_meter = VUMeter(20, H - 220, 30, 200)
        self.lbl_vu = TextLabel(self.font_small, (35, H - 250), align="center")
        self.lbl_vu.set_text("MIC")
        
        # 4. Voyant de stabilité (Coin haut droit)
        self.status_light = StatusLight((W - 50, 50), 20)
        
        # CORRECTION ICI : align="topright" au lieu de "right"
        self.lbl_stable = TextLabel(self.font_small, (W - 100, 40), align="topright")
        self.lbl_stable.set_text("STABLE")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Espace = Toggle Mute (pour tester le start/stop audio)
            if event.key == pygame.K_SPACE:
                self.controller.toggle_audio()

    def update(self, dt: float):
        # Récupération instantanée de l'état (Thread-Safe)
        feats = self.state.get_features_snapshot()
        
        # 1. Mise à jour VU-mètre
        self.vu_meter.set_value(feats.rms)
        
        # 2. Mise à jour Note et Info
        if feats.is_voiced and feats.note_name:
            # Couleur dynamique : Vert si proche de 0 cents, Blanc sinon
            color = (0, 255, 0) if abs(feats.cents) < 10 else (255, 255, 255)
            
            self.lbl_note.set_text(feats.note_name, color)
            self.lbl_info.set_text(f"{feats.f0_hz:.1f} Hz  |  {feats.cents:+.0f} cts")
        else:
            # Silence
            self.lbl_note.set_text("...", (100, 100, 100))
            self.lbl_info.set_text("No Signal")

        # 3. Mise à jour Voyant Stabilité
        self.status_light.set_active(feats.stable)

    def draw(self, surface):
        # On dessine tous les composants
        self.lbl_note.draw(surface)
        self.lbl_info.draw(surface)
        
        self.vu_meter.draw(surface)
        self.lbl_vu.draw(surface)
        
        self.status_light.draw(surface)
        self.lbl_stable.draw(surface)