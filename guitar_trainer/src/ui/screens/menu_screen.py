import pygame
from .base import Screen
from ..widgets.text import TextLabel

class MenuScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        
        W, H = cfg.window_size
        CX, CY = W // 2, H // 2
        
        # Polices
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.15), bold=True)
        self.font_btn = pygame.font.SysFont("monospace", int(H * 0.05))
        
        # Titre
        self.lbl_title = TextLabel(self.font_title, (CX, int(H * 0.2)), align="center")
        self.lbl_title.set_text("GUITAR ZERO", (0, 255, 255))
        
        # Boutons (Rectangles simples)
        btn_w, btn_h = int(W * 0.3), int(H * 0.1)
        self.btn_tuner = pygame.Rect(CX - btn_w//2, CY, btn_w, btn_h)
        self.btn_arcade = pygame.Rect(CX - btn_w//2, CY + int(H * 0.15), btn_w, btn_h)
        
        self.lbl_tuner = TextLabel(self.font_btn, self.btn_tuner.center, align="center")
        self.lbl_tuner.set_text("L'ATELIER (Tuner)", (255, 255, 255))
        
        self.lbl_arcade = TextLabel(self.font_btn, self.btn_arcade.center, align="center")
        # COULEUR ACTIVE (Orange vif pour montrer que c'est jouable)
        self.lbl_arcade.set_text("ARCADE (Jeu)", (255, 200, 50))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Clic gauche
                if self.btn_tuner.collidepoint(event.pos):
                    # Navigation vers le Tuner
                    self.app.change_screen("tuner")
                
                elif self.btn_arcade.collidepoint(event.pos):
                    # --- LOGIQUE INTELLIGENTE ---
                    # Si le jeu a déjà été configuré (engine.initialized), on y va direct.
                    # Sinon, on passe par le Setup.
                    engine = self.controller.game_engine
                    
                    if hasattr(engine, 'initialized') and engine.initialized:
                        # Reprise directe
                        engine.start_game()
                        self.app.change_screen("game")
                    else:
                        # Première fois -> Setup
                        self.app.change_screen("setup")

    def draw(self, surface):
        surface.fill((20, 20, 30))
        
        self.lbl_title.draw(surface)
        
        # Dessin Bouton Tuner
        pygame.draw.rect(surface, (50, 50, 70), self.btn_tuner, border_radius=10)
        pygame.draw.rect(surface, (0, 255, 255), self.btn_tuner, 2, border_radius=10)
        self.lbl_tuner.draw(surface)
        
        # Dessin Bouton Arcade
        pygame.draw.rect(surface, (30, 30, 40), self.btn_arcade, border_radius=10)
        pygame.draw.rect(surface, (255, 200, 50), self.btn_arcade, 2, border_radius=10)
        self.lbl_arcade.draw(surface)