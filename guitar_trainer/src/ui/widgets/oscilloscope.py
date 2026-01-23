import pygame
import numpy as np

class OscilloscopeWidget:
    def __init__(self, rect: pygame.Rect, color=(0, 255, 255), width=2):
        self.rect = rect
        self.color = color
        self.width = width
        self.center_y = rect.centery
        # Amplitude visuelle (0.4 = 40% de la hauteur totale vers le haut/bas)
        self.amp_scale = rect.height * 0.4

    def draw(self, surface: pygame.Surface, samples: np.ndarray | None) -> None:
        if samples is None or len(samples) == 0:
            return

        points = []
        # On répartit les points sur toute la largeur
        step = self.rect.width / len(samples)
        
        # Optimisation : On peut dessiner 1 point sur 2 si le tableau est très grand
        # Ici on prend tout pour la fluidité maximale sur petits buffers
        for i in range(0, len(samples), 2):
            px = self.rect.x + i * step
            # samples[i] est entre -1.0 et 1.0
            py = self.center_y + samples[i] * self.amp_scale
            points.append((px, py))

        if len(points) > 1:
            pygame.draw.lines(surface, self.color, False, points, self.width)