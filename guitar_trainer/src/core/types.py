from dataclasses import dataclass
import numpy as np

@dataclass
class AudioBlock:
    """Représente un paquet d'échantillons audio bruts."""
    samples: np.ndarray  # float32
    sample_rate: int
    timestamp: float     # temps système

@dataclass
class Features:
    """Résultat de l'analyse d'un bloc audio."""
    timestamp: float = 0.0
    rms: float = 0.0
    
    # Pitch info
    f0_hz: float | None = None
    note_name: str | None = "-"
    cents: float | None = 0.0
    confidence: float = 0.0
    
    # États calculés
    is_voiced: bool = False  # Y a-t-il du son (au-dessus du seuil) ?
    stable: bool = False     # La note est-elle tenue assez longtemps ?
    stable_ms: float = 0.0   # Depuis combien de temps la note est tenue

@dataclass
class AppEvents:
    """Événements ponctuels pour l'UI (erreurs, changements d'état)."""
    last_error: str | None = None
    audio_running: bool = False