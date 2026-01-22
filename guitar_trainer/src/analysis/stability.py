from ..core.config import AppConfig

class StabilityTracker:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.current_note_name: str | None = None
        self.stable_start_time: float | None = None
        self.is_stable: bool = False
        self.stable_ms: float = 0.0

    def update(self, note_name: str | None, cents: float | None, voiced: bool, timestamp: float) -> tuple[bool, float]:
        """
        Met à jour l'état de stabilité.
        Retourne (is_stable, duration_ms).
        """
        # Si pas de son ou note indéterminée, on reset tout
        if not voiced or note_name is None or cents is None:
            self._reset()
            return False, 0.0

        # Vérification de tolérance (note identique et justesse acceptable)
        # Note : Pour l'instant on vérifie juste le nom de la note.
        # Plus tard, on pourra vérifier si 'cents' reste proche de 0.
        is_same_note = (note_name == self.current_note_name)
        is_in_tune = abs(cents) <= self.cfg.stable_cents_tolerance

        if is_same_note and is_in_tune:
            # La note est tenue
            if self.stable_start_time is None:
                self.stable_start_time = timestamp
            
            # Calcul durée
            duration_ms = (timestamp - self.stable_start_time) * 1000.0
            
            # Validation seuil
            if duration_ms >= self.cfg.stable_window_ms:
                self.is_stable = True
            
            self.stable_ms = duration_ms
            
        else:
            # Changement de note ou fausse note -> Reset partiel
            # On redémarre le tracking sur la NOUVELLE note
            self.current_note_name = note_name
            self.stable_start_time = timestamp
            self.is_stable = False
            self.stable_ms = 0.0

        return self.is_stable, self.stable_ms

    def _reset(self):
        self.current_note_name = None
        self.stable_start_time = None
        self.is_stable = False
        self.stable_ms = 0.0