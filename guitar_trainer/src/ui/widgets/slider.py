import pygame

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label, is_int=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.is_int = is_int # Si True, force des nombres entiers (pour les Cases)
        
        self.dragging = False
        
        self.font = pygame.font.SysFont("monospace", int(h * 0.8))
        self.color_track = (60, 60, 70)
        self.color_fill = (0, 200, 255) # Cyan
        self.color_handle = (255, 255, 255)
        
    def handle_event(self, event):
        change = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.inflate(10, 10).collidepoint(event.pos):
                self.dragging = True
                self._update_val(event.pos[0])
                change = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._update_val(event.pos[0])
                change = True
                
        return change

    def _update_val(self, mouse_x):
        # Limiter la souris à la largeur du slider
        x = max(self.rect.left, min(mouse_x, self.rect.right))
        
        # Calcul du pourcentage (0.0 à 1.0)
        norm = (x - self.rect.left) / self.rect.width
        
        # Conversion en valeur réelle
        raw_val = self.min_val + (norm * (self.max_val - self.min_val))
        
        if self.is_int:
            self.val = int(round(raw_val))
        else:
            self.val = raw_val

    def draw(self, surface):
        # 1. Label et Valeur au-dessus
        val_str = f"{int(self.val)}" if self.is_int else f"{self.val:.1f}s"
        text = f"{self.label}: {val_str}"
        lbl = self.font.render(text, True, (200, 200, 200))
        surface.blit(lbl, (self.rect.x, self.rect.y - 25))
        
        # 2. La piste (Track)
        pygame.draw.rect(surface, self.color_track, self.rect, border_radius=4)
        
        # 3. La partie remplie (Fill)
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val) if (self.max_val > self.min_val) else 0
        fill_width = int(ratio * self.rect.width)
        fill_rect = pygame.Rect(self.rect.left, self.rect.top, fill_width, self.rect.height)
        pygame.draw.rect(surface, self.color_fill, fill_rect, border_radius=4)
        
        # 4. La poignée (Handle)
        handle_x = self.rect.left + fill_width
        handle_radius = self.rect.height // 2 + 4
        pygame.draw.circle(surface, self.color_handle, (handle_x, self.rect.centery), handle_radius)