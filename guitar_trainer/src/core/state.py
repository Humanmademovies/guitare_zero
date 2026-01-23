import threading
from dataclasses import replace
from .types import Features, AppEvents
import numpy as np

class AppState:
    def __init__(self):
        self._features = None
        self._lock = threading.Lock()
        self._events = AppEvents()
        
        # Données historiques (gérées en interne maintenant)
        self._spectrogram_history = [] 
        self.max_history = 300

        # Stockage des périphériques
        self._input_devices = []
        self._output_devices = []

    def update_features(self, f: Features) -> None:
        """
        Appelé par le thread d'analyse.
        Met à jour les features courantes ET gère l'historique du spectrogramme.
        """
        with self._lock:
            self._features = f
            
            # Gestion centralisée de l'historique
            if f.spectrum is not None:
                self._spectrogram_history.append(f.spectrum)
                # On garde une taille fixe
                if len(self._spectrogram_history) > self.max_history:
                    self._spectrogram_history.pop(0)

    def get_features_snapshot(self) -> Features | None:
        with self._lock:
            if self._features is None:
                return None
            return replace(self._features)

    def get_spectrogram_history(self) -> list[np.ndarray]:
        """Retourne une copie sécurisée de l'historique pour l'affichage."""
        with self._lock:
            # On renvoie une copie de la liste pour éviter les conflits de lecture/écriture
            return list(self._spectrogram_history)

    def reset_history(self) -> None:
        """Vide l'historique (utile lors du changement de périphérique/SR)."""
        with self._lock:
            self._spectrogram_history.clear()

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
    
    def set_output_devices(self, devices: list[dict]) -> None:
        with self._lock:
            self._output_devices = devices

    def get_output_devices(self) -> list[dict]:
        with self._lock:
            return list(self._output_devices)