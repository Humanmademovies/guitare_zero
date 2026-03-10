import pygame
from .base import Screen

class StudioScreen(Screen):
    def __init__(self, cfg, state, controller):
        self.cfg = cfg
        self.state = state
        self.controller = controller
        self.font_main = pygame.font.SysFont(None, self.cfg.font_size_main)
        self.font_small = pygame.font.SysFont(None, 36)
        
    def on_enter(self):
        self.controller.set_active_mode("studio")
        self.controller.studio_engine.reset_recording()
        
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.app:
                    self.app.change_screen("menu")
            elif event.key == pygame.K_RIGHT:
                self.controller.studio_engine.next_target()
            elif event.key == pygame.K_LEFT:
                self.controller.studio_engine.prev_target()
            elif event.key == pygame.K_SPACE:
                self.controller.studio_engine.play_current_sample()
            elif event.key == pygame.K_r:
                self.controller.studio_engine.reset_recording()
                
    def update(self, dt):
        pass # La logique d'enregistrement est gérée par le StudioEngine via le Controller
        
    def draw(self, surface):
        surface.fill((20, 20, 20))
        
        engine = self.controller.studio_engine
        target = engine.get_current_target()
        
        # Titre et instructions
        title = self.font_main.render("MODE STUDIO (Échantillonnage)", True, (200, 200, 200))
        surface.blit(title, (50, 50))
        
        inst = self.font_small.render("Flèches G/D pour naviguer | Echap pour quitter", True, (100, 100, 100))
        surface.blit(inst, (50, 100))
        
        if not target:
            done_txt = self.font_main.render("Toutes les notes sont enregistrées !", True, (100, 255, 100))
            surface.blit(done_txt, (50, 200))
            return
            
        # Affichage de la cible
        target_txt = self.font_main.render(f"Joue : Corde {target['string']} | Case {target['fret']} ({target['note']})", True, (255, 200, 0))
        surface.blit(target_txt, (50, 250))
        
        # Statut de l'enregistrement
        status_color = (100, 100, 100)
        if engine.state == "WAITING":
            if engine.pre_record_timer > 0:
                status_txt = "MAINTIENS LA NOTE PROPREMENT..."
                status_color = (255, 200, 50)
            else:
                status_txt = "En attente d'une note stable, pure et juste (<3 cents)..."
        elif engine.state == "RECORDING":
            status_txt = "ENREGISTREMENT EN COURS !"
            status_color = (255, 50, 50)
        else:
            status_txt = "SAUVEGARDÉ ! (-> Suivant | ESPACE: Écouter | R: Refaire)"
            status_color = (50, 255, 50)
            
        status_render = self.font_main.render(status_txt, True, status_color)
        surface.blit(status_render, (50, 350))
        
        # Barre de progression
        if engine.state == "WAITING" and engine.pre_record_timer > 0:
            progress = min(1.0, engine.pre_record_timer / engine.pre_record_duration)
            bar_rect = pygame.Rect(50, 450, 600, 40)
            pygame.draw.rect(surface, (50, 50, 50), bar_rect)
            fill_rect = pygame.Rect(50, 450, int(600 * progress), 40)
            pygame.draw.rect(surface, (255, 200, 50), fill_rect) # Barre orange de chauffe
            pygame.draw.rect(surface, (255, 255, 255), bar_rect, 2)
            
        elif engine.state == "RECORDING":
            progress = min(1.0, engine.record_timer / engine.record_duration)
            bar_rect = pygame.Rect(50, 450, 600, 40)
            pygame.draw.rect(surface, (50, 50, 50), bar_rect)
            fill_rect = pygame.Rect(50, 450, int(600 * progress), 40)
            pygame.draw.rect(surface, (255, 50, 50), fill_rect) # Barre rouge d'enregistrement
            pygame.draw.rect(surface, (255, 255, 255), bar_rect, 2)
        
        # Diagnostic en temps réel
        features = self.state.get_features_snapshot()
        if features and features.is_voiced:
            purity_str = "OUI" if features.is_pure else "NON (Bruit)"
            info = self.font_small.render(
                f"Entendu: {features.note_name} | Cents: {features.cents:.1f} | Pur: {purity_str}", 
                True, (150, 150, 255)
            )
            surface.blit(info, (50, 550))
