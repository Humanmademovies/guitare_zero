import numpy as np
import aubio
from ..core.config import AppConfig

class PitchTracker:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        # Aubio attend un buffer size (window) et un hop size (step).
        # Hop size doit correspondre à la taille de nos blocs audio (1024).
        # Buffer size est généralement 2x ou 4x le hop size pour une bonne FFT.
        self.buf_size = cfg.block_size * 2
        self.hop_size = cfg.block_size
        
        # Initialisation de l'objet pitch d'Aubio
        # Méthodes possibles : "yin", "mcomb", "fcomb", "schmitt", "yinfft"
        # "yinfft" est souvent un bon compromis précision/stabilité pour instruments
        self.pitch_o = aubio.pitch("yinfft", self.buf_size, self.hop_size, cfg.sample_rate)
        
        self.pitch_o.set_unit("Hz")
        self.pitch_o.set_tolerance(cfg.confidence_threshold)
        
        # FIX: Aubio attend des dB ici (ex: -40), pas une amplitude linéaire (0.01).
        # On met une valeur standard (-50dB) pour éviter le crash.
        # Le vrai filtrage de silence se fera dans features.py via rms_threshold.
        self.pitch_o.set_silence(-50.0)

    def process(self, samples: np.ndarray) -> tuple[float | None, float]:
        """
        Traite un bloc d'échantillons et retourne (Féquence, Confiance).
        Retourne (None, 0.0) si aucune fréquence fiable n'est trouvée.
        """
        # Aubio attend un tableau de float32 contigu
        if samples.shape[0] != self.hop_size:
            # Sécurité si le dernier bloc est incomplet
            return None, 0.0

        # Appel C++ optimisé d'Aubio
        prediction = self.pitch_o(samples)[0]
        confidence = self.pitch_o.get_confidence()

        # Filtrage basique
        if prediction < self.cfg.fmin or prediction > self.cfg.fmax:
            return None, 0.0
            
        return float(prediction), float(confidence)