import threading
from dataclasses import replace
from .types import Features, AppEvents

class AppState:
    """
    Stockage thread-safe de l'état de l'application.
    L'audio écrit ici, l'UI lit ici.
    """
    def __init__(self):
        self._lock = threading.Lock()
        
        # État initial
        self._features = Features()
        self._events = AppEvents()

    def update_features(self, f: Features) -> None:
        """Appelé par le thread d'analyse pour mettre à jour les données."""
        with self._lock:
            self._features = f

    def get_features_snapshot(self) -> Features:
        """Appelé par l'UI pour récupérer les dernières données sans bloquer."""
        with self._lock:
            # On retourne une copie pour éviter les modifications concurrentes
            return replace(self._features)

    def set_audio_running(self, running: bool) -> None:
        with self._lock:
            self._events.audio_running = running

    def is_audio_running(self) -> bool:
        with self._lock:
            return self._events.audio_running

    def set_error(self, message: str | None) -> None:
        with self._lock:
            self._events.last_error = message
            if message:
                print(f"[ERROR] {message}")