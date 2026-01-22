import pygame

class VUMeter:
    def __init__(self, x, y, w, h, max_rms=0.5):
        self.rect = pygame.Rect(x, y, w, h)
        self.max_rms = max_rms
        self.current_h = 0

    def set_value(self, rms: float) -> None:
        # On plafonne la valeur pour ne pas dépasser le cadre
        val = min(rms, self.max_rms)
        # Produit en croix pour la hauteur
        ratio = val / self.max_rms
        self.current_h = int(ratio * self.rect.height)

    def draw(self, surface: pygame.Surface) -> None:
        # Fond (gris foncé)
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        
        if self.current_h > 0:
            # Barre de volume (verte en bas)
            # On dessine du bas vers le haut
            fill_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom - self.current_h,
                self.rect.width,
                self.current_h
            )
            pygame.draw.rect(surface, (0, 200, 0), fill_rect)
            
        # Cadre (gris clair)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)