import pygame
import math

class Knob:
    def __init__(self, x, y, radius, label, initial_val=0.0, min_val=0.0, max_val=1.0):
        self.x = x
        self.y = y
        self.radius = radius
        self.label = label
        self.val = initial_val
        self.min_val = min_val
        self.max_val = max_val
        
        self.dragging = False
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        
        self.font = pygame.font.SysFont("monospace", 20)

    def handle_event(self, event) -> bool:
        """Retourne True si la valeur a changé, sinon False."""
        changed = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Sensibilité : on change la valeur selon le mouvement Y de la souris
                # Monter la souris = Augmenter la valeur
                dy = event.rel[1]
                
                # Vitesse de changement
                step = 0.01
                self.val -= dy * step
                
                # Bornage
                if self.val < self.min_val: self.val = self.min_val
                if self.val > self.max_val: self.val = self.max_val
                
                changed = True

        # --- C'EST ICI QUE ÇA MANQUAIT ---
        return changed

    def draw(self, surface):
        # Fond
        pygame.draw.circle(surface, (50, 50, 60), (self.x, self.y), self.radius)
        
        # Indicateur (Aiguille)
        # Angle : 0% = -135deg, 100% = +135deg
        normalized = (self.val - self.min_val) / (self.max_val - self.min_val)
        angle = -135 + (normalized * 270)
        rad = math.radians(angle - 90) # -90 pour corriger l'orientation mathématique
        
        end_x = self.x + math.cos(rad) * (self.radius * 0.8)
        end_y = self.y + math.sin(rad) * (self.radius * 0.8)
        
        line_color = (0, 255, 255) # Cyan
        pygame.draw.line(surface, line_color, (self.x, self.y), (end_x, end_y), 3)
        
        # Label
        lbl = self.font.render(self.label, True, (200, 200, 200))
        surface.blit(lbl, (self.x - lbl.get_width()//2, self.y + self.radius + 10))
        
        # Valeur numérique (Optionnel mais pratique pour debug)
        val_txt = f"{self.val:.2f}"
        lbl_val = self.font.render(val_txt, True, (150, 150, 150))
        surface.blit(lbl_val, (self.x - lbl_val.get_width()//2, self.y + self.radius + 30))