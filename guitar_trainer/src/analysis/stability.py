import time
from collections import deque
from ..core.types import Features

class StabilityTracker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.buffer = deque()
        # Calcul du nombre de frames nécessaires pour la fenêtre de temps
        self.required_frames = int((cfg.stable_window_ms / 1000.0) * (cfg.sample_rate / cfg.block_size))

    def update(self, feats: Features) -> bool:
        # RÉACTION IMMÉDIATE : Si les conditions des potards ne sont plus remplies
        # (Volume trop bas ou Son trop sale), on vide le tampon instantanément.
        if not feats.is_voiced:
            self.buffer.clear()
            return False

        # Ajout de l'écart (cents) actuel
        self.buffer.append(feats.cents)

        # On garde uniquement la fenêtre définie dans la config
        if len(self.buffer) > self.required_frames:
            self.buffer.popleft()

        # Pour être stable, il faut avoir assez de données et être dans la tolérance
        if len(self.buffer) < self.required_frames:
            return False

        # Vérification si tous les échantillons du tampon sont dans la cible
        is_stable = all(abs(c) <= self.cfg.stable_cents_tolerance for c in self.buffer)
        return is_stable

    def _reset(self):
        self.current_note_name = None
        self.stable_start_time = None
        self.is_stable = False
        self.stable_ms = 0.0