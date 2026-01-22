import pygame

class VUMeter:
    def __init__(self, x, y, w, h, max_rms=0.5):
        self.rect = pygame.Rect(x, y, w, h)
        self.max_rms = max_rms
        self.current_h = 0
        self.threshold = 0.0

    def set_value(self, rms: float) -> None:
        # On plafonne la valeur pour ne pas dépasser le cadre
        val = min(rms, self.max_rms)
        # Produit en croix pour la hauteur
        ratio = val / self.max_rms
        self.current_h = int(ratio * self.rect.height)

    def draw(self, surface: pygame.Surface) -> None:
        # 1. Fond (gris foncé)
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        
        # 2. Barre de volume (verte)
        if self.current_h > 0:
            fill_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom - self.current_h,
                self.rect.width,
                self.current_h
            )
            pygame.draw.rect(surface, (0, 200, 0), fill_rect)
            
        # 3. Cadre (gris clair)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)

        # 4. Ligne de seuil (Noise Gate)
        # On calcule la position Y par rapport au bas du rectangle
        ratio_thresh = min(1.0, self.threshold / self.max_rms)
        thresh_y = self.rect.bottom - int(ratio_thresh * self.rect.height)
        pygame.draw.line(surface, (255, 0, 0), (self.rect.x - 5, thresh_y), (self.rect.right + 5, thresh_y), 3)