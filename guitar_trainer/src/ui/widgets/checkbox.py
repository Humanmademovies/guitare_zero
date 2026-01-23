import pygame

class Checkbox:
    def __init__(self, x, y, size, label, checked=False, text_color=(200, 200, 200)):
        self.rect = pygame.Rect(x, y, size, size)
        self.label = label
        self.checked = checked
        self.text_color = text_color
        
        self.font = pygame.font.SysFont("monospace", int(size * 0.8))
        self.color_active = (0, 255, 0)      # Vert quand coché
        self.color_inactive = (100, 100, 100) # Gris quand vide
        self.color_bg = (30, 30, 40)
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                return True # L'événement a été consommé
        return False

    def draw(self, surface):
        # 1. Dessiner la boîte
        color_border = (255, 255, 255) if self.hovered else self.color_inactive
        if self.checked:
            color_border = self.color_active
            
        pygame.draw.rect(surface, self.color_bg, self.rect)
        pygame.draw.rect(surface, color_border, self.rect, 2)
        
        # 2. Dessiner le 'Check' (Carré plein au centre)
        if self.checked:
            inner_size = int(self.rect.width * 0.6)
            inner_rect = pygame.Rect(0, 0, inner_size, inner_size)
            inner_rect.center = self.rect.center
            pygame.draw.rect(surface, self.color_active, inner_rect)
            
        # 3. Dessiner le Texte
        lbl_surf = self.font.render(self.label, True, self.text_color)
        # Centrer verticalement par rapport à la case
        lbl_y = self.rect.centery - lbl_surf.get_height() // 2
        surface.blit(lbl_surf, (self.rect.right + 10, lbl_y))