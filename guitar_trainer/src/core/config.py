from dataclasses import dataclass

@dataclass
class AppConfig:
    # --- Audio ---
    sample_rate: int = 44100   # On garde 48k pour le H4n
    block_size: int = 1024
    channels: int = 1
    
    # LA MODIF EST ICI : On met le nom exact renvoyé par le système
    device_name_or_index: str | int | None = "H4"
    
    # --- Analyse (Pitch & Features) ---
    fmin: float = 40.0
    
    # --- Analyse (Pitch & Features) ---
    fmin: float = 40.0    # E1 (Guitare basse = 41Hz)
    fmax: float = 2000.0  # C7 (Guitare haute ~1kHz + harmoniques)
    confidence_threshold: float = 0.2  # Seuil de confiance Aubio (0.0 à 1.0)
    rms_threshold: float = 0.001        # Noise gate (silence)
    
    # --- Stabilité (Gameplay) ---
    stable_window_ms: float = 500.0    # Temps nécessaire pour valider une note
    stable_cents_tolerance: float = 15.0 # Tolérance de justesse (+/- cents)
    
    # --- UI ---
    window_title: str = "Guitar Trainer MVP"
    window_size: tuple[int, int] = (800, 600)
    fps: int = 60
    font_size_main: int = 48
    font_size_debug: int = 24

def load_config() -> AppConfig:
    # Pour l'instant, on retourne la config par défaut.
    # Plus tard, on pourra charger un fichier YAML ici.
    return AppConfig()

def validate_config(cfg: AppConfig) -> None:
    if cfg.block_size <= 0:
        raise ValueError("Block size must be positive")
    if cfg.sample_rate <= 0:
        raise ValueError("Sample rate must be positive")
    if cfg.fmin >= cfg.fmax:
        raise ValueError("fmin must be lower than fmax")