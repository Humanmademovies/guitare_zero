import pygame

class StatusLight:
    def __init__(self, center: tuple[int, int], radius: int):
        self.center = center
        self.radius = radius
        self.active = False

    def set_active(self, active: bool) -> None:
        self.active = active

    def draw(self, surface: pygame.Surface) -> None:
        # Vert vif si actif, Rouge sombre si inactif
        color = (0, 255, 0) if self.active else (50, 0, 0)
        
        # Disque coloré
        pygame.draw.circle(surface, color, self.center, self.radius)
        # Contour
        pygame.draw.circle(surface, (200, 200, 200), self.center, self.radius, 2)