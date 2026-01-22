import pygame
import math

class Knob:
    def __init__(self, x, y, radius, label, initial_val, min_val, max_val):
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        self.center = (x, y)
        self.radius = radius
        self.label = label
        self.val = initial_val
        self.min_val = min_val
        self.max_val = max_val
        self.dragging = False
        self.font = pygame.font.SysFont("monospace", 20)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx = event.pos[0] - self.center[0]
            dy = event.pos[1] - self.center[1]
            angle = math.degrees(math.atan2(dy, dx))
            # Normalisation de l'angle pour obtenir une valeur entre 0 et 1
            norm_val = (angle + 180) / 360
            self.val = self.min_val + norm_val * (self.max_val - self.min_val)
            self.val = max(self.min_val, min(self.max_val, self.val))

    def draw(self, surface):
        # Dessin du corps du potard
        pygame.draw.circle(surface, (60, 60, 70), self.center, self.radius)
        pygame.draw.circle(surface, (100, 100, 110), self.center, self.radius, 2)
        
        # Dessin de l'indicateur (ligne)
        angle = ((self.val - self.min_val) / (self.max_val - self.min_val) * 360) - 180
        rad = math.radians(angle)
        end_x = self.center[0] + math.cos(rad) * self.radius
        end_y = self.center[1] + math.sin(rad) * self.radius
        pygame.draw.line(surface, (255, 200, 0), self.center, (end_x, end_y), 3)
        
        # Libellé et valeur
        lbl_surf = self.font.render(f"{self.label}", True, (200, 200, 200))
        val_surf = self.font.render(f"{self.val:.4f}", True, (255, 255, 255))
        surface.blit(lbl_surf, (self.center[0] - lbl_surf.get_width()//2, self.center[1] + self.radius + 10))
        surface.blit(val_surf, (self.center[0] - val_surf.get_width()//2, self.center[1] + self.radius + 30))