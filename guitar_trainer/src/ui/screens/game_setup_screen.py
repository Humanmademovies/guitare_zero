import pygame
from .base import Screen
from ..widgets.text import TextLabel
from ..widgets.checkbox import Checkbox
from ..widgets.slider import Slider
from ...game.settings import GameSettings # Nécessaire pour simuler le multiplicateur

class GameSetupScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        CX = W // 2
        
        # Titre
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.06), bold=True)
        self.lbl_title = TextLabel(self.font_title, (CX, int(H * 0.08)), align="center")
        self.lbl_title.set_text("CONFIGURATION ARCADE", (0, 255, 255))
        
        # Récupération des settings actuels (pour pré-remplir)
        current_settings = self.controller.game_engine.settings
        
        # --- 1. CORDES (Checkboxes) ---
        self.chk_strings = []
        string_names = ["E (6)", "A (5)", "D (4)", "G (3)", "B (2)", "e (1)"]
        string_ids = [6, 5, 4, 3, 2, 1]
        
        start_x = int(W * 0.15)
        y_strings = int(H * 0.18)
        spacing_x = int(W * 0.13)
        
        for i, name in enumerate(string_names):
            s_id = string_ids[i]
            is_checked = s_id in current_settings.active_strings
            chk = Checkbox(start_x + (i * spacing_x), y_strings, 30, name, checked=is_checked)
            chk.string_id = s_id 
            self.chk_strings.append(chk)
            
        # --- 2. SLIDERS (PHYSIQUE) ---
        slider_w = int(W * 0.35)
        slider_h = 20
        col1_x = int(W * 0.25) - slider_w // 2
        col2_x = int(W * 0.75) - slider_w // 2
        
        y_sliders = int(H * 0.35)
        y_step = int(H * 0.1)
        
        # Colonne Gauche : Physique
        self.sld_speed = Slider(col1_x, y_sliders, slider_w, slider_h, 
                                1.0, 5.0, current_settings.note_duration, "Vitesse (sec)")
        
        self.sld_fret = Slider(col1_x, y_sliders + y_step, slider_w, slider_h, 
                               3, 12, current_settings.max_fret, "Case Max", is_int=True)
                               
        self.sld_jump = Slider(col1_x, y_sliders + y_step*2, slider_w, slider_h, 
                               0, 12, current_settings.max_jump, "Saut Max (Cases)", is_int=True)

        # --- 3. RÈGLES DU JEU (NOUVEAU) ---
        # Colonne Droite : Règles
        self.sld_notes = Slider(col2_x, y_sliders, slider_w, slider_h, 
                                5, 100, current_settings.total_notes, "Total Notes", is_int=True)
                                
        self.sld_lives = Slider(col2_x, y_sliders + y_step, slider_w, slider_h, 
                                1, 10, current_settings.max_lives, "Vies (Erreurs Max)", is_int=True)
        
        # Checkbox Mode Aveugle (Aide Visuelle)
        self.chk_helper = Checkbox(col2_x, y_sliders + y_step*2, 30, "Afficher Aide (Tablature)", 
                                   checked=current_settings.show_helper)

        # --- 4. MULTIPLICATEUR DE SCORE (NOUVEAU) ---
        self.font_mult = pygame.font.SysFont("monospace", int(H * 0.05), bold=True)
        self.lbl_mult = TextLabel(self.font_mult, (CX, int(H * 0.75)), align="center")
        
        # --- 5. BOUTON JOUER ---
        btn_w, btn_h = int(W * 0.3), int(H * 0.1)
        self.rect_play = pygame.Rect(CX - btn_w//2, int(H * 0.85), btn_w, btn_h)
        self.font_btn = pygame.font.SysFont("monospace", int(H * 0.06), bold=True)
        self.lbl_play = TextLabel(self.font_btn, self.rect_play.center, align="center")
        self.lbl_play.set_text("JOUER !", (0, 0, 0))
        
        # Initialisation du texte du multiplicateur
        self._update_multiplier_preview()

    def handle_event(self, event):
        changed = False
        
        # Checkboxes Cordes
        for chk in self.chk_strings:
            if chk.handle_event(event): changed = True
            
        # Sliders
        if self.sld_speed.handle_event(event): changed = True
        if self.sld_fret.handle_event(event): changed = True
        if self.sld_jump.handle_event(event): changed = True
        
        # Sliders Règles
        if self.sld_notes.handle_event(event): changed = True
        if self.sld_lives.handle_event(event): changed = True
        
        # Checkbox Helper
        if self.chk_helper.handle_event(event): changed = True
        
        # Mise à jour du multiplicateur si changement
        if changed:
            self._update_multiplier_preview()
        
        # Bouton Play
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect_play.collidepoint(event.pos):
                self._save_and_play()
                
        # Touche Entrée
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._save_and_play()
            
    def _update_multiplier_preview(self):
        """Simule les settings pour calculer le score futur."""
        # On crée un objet settings temporaire
        temp = GameSettings()
        
        # On remplit avec les valeurs des widgets
        active = [chk.string_id for chk in self.chk_strings if chk.checked]
        if not active: active = [6]
        
        temp.active_strings = active
        temp.note_duration = self.sld_speed.val
        temp.max_fret = int(self.sld_fret.val)
        temp.max_jump = int(self.sld_jump.val)
        temp.total_notes = int(self.sld_notes.val)
        temp.max_lives = int(self.sld_lives.val)
        temp.show_helper = self.chk_helper.checked
        
        mult = temp.get_multiplier()
        self.lbl_mult.set_text(f"DIFFICULTÉ : x{mult}", (255, 200, 50))

    def _save_and_play(self):
        """Sauvegarde la config dans le moteur réel et lance le jeu."""
        engine = self.controller.game_engine
        
        # 1. Cordes
        active = [chk.string_id for chk in self.chk_strings if chk.checked]
        if not active: active = [6]
        engine.settings.active_strings = active
        
        # 2. Physique
        engine.settings.note_duration = self.sld_speed.val
        engine.settings.max_fret = int(self.sld_fret.val)
        engine.settings.max_jump = int(self.sld_jump.val)
        
        # 3. Règles
        engine.settings.total_notes = int(self.sld_notes.val)
        engine.settings.max_lives = int(self.sld_lives.val)
        engine.settings.show_helper = self.chk_helper.checked
        
        # 4. Go
        engine.initialized = True 
        engine.start_game()
        self.app.change_screen("game")

    def draw(self, surface):
        surface.fill((20, 20, 30))
        self.lbl_title.draw(surface)
        
        # Cordes
        for chk in self.chk_strings:
            chk.draw(surface)
            
        # Colonne 1
        self.sld_speed.draw(surface)
        self.sld_fret.draw(surface)
        self.sld_jump.draw(surface)
        
        # Colonne 2
        self.sld_notes.draw(surface)
        self.sld_lives.draw(surface)
        self.chk_helper.draw(surface)
        
        # Multiplicateur
        self.lbl_mult.draw(surface)
        
        # Bouton Play
        pygame.draw.rect(surface, (0, 255, 200), self.rect_play, border_radius=15)
        pygame.draw.rect(surface, (255, 255, 255), self.rect_play, 3, border_radius=15)
        self.lbl_play.draw(surface)