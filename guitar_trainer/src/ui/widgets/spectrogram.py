import pygame
import math
import numpy as np

class SpectrogramWidget:
    def __init__(self, rect: pygame.Rect, max_history: int, num_bins: int = 120):
        self.rect = rect
        self.max_history = max_history
        self.num_bins = num_bins
        # Pré-calcul de la hauteur d'un bin pour éviter de le refaire à chaque frame
        self.bin_height = self.rect.height / self.num_bins

    def draw(self, surface: pygame.Surface, history: list[np.ndarray]) -> None:
        if not history:
            return

        # Largeur d'une colonne (dépend de la taille de l'historique max définie dans l'app)
        # On utilise max_history pour que le défilement soit fluide (la largeur ne saute pas au début)
        col_width = self.rect.width / self.max_history
        
        for i, spec in enumerate(history):
            x = self.rect.x + i * col_width
            
            # On parcourt les fréquences (bins)
            for j in range(self.num_bins):
                # Protection si le spectre est plus petit que prévu
                val = spec[j] if j < len(spec) else 0
                
                # Calcul de l'intensité (logarithmique pour mieux voir les sons faibles)
                intensity = min(255, int(math.log1p(val) * 50))
                
                if intensity > 10:
                    # Couleur : Cyan sombre -> Bleu -> Blanc
                    color = (intensity // 2, intensity, intensity // 4)
                    
                    # Position Y (le bas du rectangle correspond aux basses fréquences)
                    y = self.rect.bottom - (j * self.bin_height)
                    
                    # Dessin du point (rect)
                    # +1 sur les dimensions pour éviter les micro-espaces noirs entre les rectangles
                    pygame.draw.rect(
                        surface, 
                        color, 
                        (x, y - self.bin_height, col_width + 1, self.bin_height + 1)
                    )