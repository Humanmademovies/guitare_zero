import pygame
import numpy as np

class SpectrogramWidget:
    """Spectrogramme défilant, rendu vectorisé.

    L'ancienne version dessinait chaque cellule avec pygame.draw.rect :
    jusqu'à 300 colonnes x 120 bins = 36 000 itérations Python PAR FRAME à
    60 FPS, ce qui affamait le callback audio (GIL) et faisait cracker le son
    dans l'accordeur. Ici : toute la matrice est calculée d'un bloc en numpy,
    convertie en surface 1 pixel/cellule puis étirée en un seul appel C.
    """

    def __init__(self, rect: pygame.Rect, max_history: int, num_bins: int = 120):
        self.rect = rect
        self.max_history = max_history
        self.num_bins = num_bins

    def draw(self, surface: pygame.Surface, history: list[np.ndarray]) -> None:
        if not history:
            return

        n = len(history)

        # Matrice (colonnes, bins) des valeurs spectrales
        arr = np.zeros((n, self.num_bins), dtype=np.float32)
        for i, spec in enumerate(history):
            m = min(self.num_bins, len(spec))
            arr[i, :m] = spec[:m]

        # Intensité logarithmique (même formule que l'ancien rendu), seuil à 10
        intensity = np.minimum(np.log1p(arr) * 50.0, 255.0)
        intensity[intensity <= 10.0] = 0.0
        intensity = intensity.astype(np.uint8)

        # Couleurs cyan sombre -> blanc (R = I/2, G = I, B = I/4),
        # basses fréquences en bas (flip de l'axe des bins)
        rgb = np.empty((n, self.num_bins, 3), dtype=np.uint8)
        rgb[..., 0] = intensity // 2
        rgb[..., 1] = intensity
        rgb[..., 2] = intensity // 4
        rgb = rgb[:, ::-1, :]

        # 1 pixel par cellule, puis étirement vers la zone occupée
        # (largeur proportionnelle à n/max_history : même défilement qu'avant)
        img = pygame.surfarray.make_surface(np.ascontiguousarray(rgb))
        target_w = max(1, int(self.rect.width * n / self.max_history))
        scaled = pygame.transform.scale(img, (target_w, self.rect.height))
        surface.blit(scaled, (self.rect.x, self.rect.y))
