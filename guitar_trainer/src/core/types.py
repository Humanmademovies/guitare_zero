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
    timestamp: float
    f0_hz: float
    note_name: str
    cents: float
    rms: float
    flatness: float
    raw_f0: float
    raw_confidence: float
    is_voiced: bool
    is_pure: bool
    spectrum: np.ndarray # Nouveau : les magnitudes de la FFT
    samples: np.ndarray  # Nouveau : les échantillons temporels bruts
    stable: bool = False

@dataclass
class AppEvents:
    """Événements ponctuels pour l'UI (erreurs, changements d'état)."""
    last_error: str | None = None
    audio_running: bool = False

@dataclass
class PitchResult:
    frequency: float
    confidence: float
    note_name: str | None
    cents: float