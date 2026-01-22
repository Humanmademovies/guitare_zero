import threading
from dataclasses import replace
from .types import Features, AppEvents

class AppState:
    def __init__(self):
        self._features = None
        self._lock = threading.Lock()
        self._events = AppEvents()    # RESTAURATION : indispensable pour le contrôleur
        self.is_running = True
        self.spectrogram_history = [] # Pour la Phase 4
        self.max_history = 300        # Pour la Phase 4

    def update_features(self, f: Features) -> None:
        """Appelé par le thread d'analyse pour mettre à jour les données."""
        with self._lock:
            self._features = f

    def get_features_snapshot(self) -> Features | None:
        with self._lock:
            if self._features is None:
                return None
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
                
    def set_input_devices(self, devices: list[dict]) -> None:
        with self._lock:
            self._input_devices = devices

    def get_input_devices(self) -> list[dict]:
        with self._lock:
            return list(self._input_devices)