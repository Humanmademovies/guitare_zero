from dataclasses import dataclass

@dataclass
class AppConfig:
    # --- Audio ---
    sample_rate: int = 44100
    block_size: int = 1024
    channels: int = 1
    device_name_or_index: str | int | None = "H4"
    
    # --- Analyse (Pitch & Features) ---
    fmin: float = 40.0
    fmax: float = 2000.0
    confidence_threshold: float = 0.2
    rms_threshold: float = 0.001
    flatness_threshold: float = 0.15   # Seuil de pureté : < 0.15 = Note, > 0.15 = Bruit
    
    # --- Stabilité (Gameplay) ---
    stable_window_ms: float = 500.0
    stable_cents_tolerance: float = 15.0
    
    # --- UI ---
    window_title: str = "Guitar Trainer MVP"
    window_size: tuple[int, int] = (1600, 1200)
    fps: int = 60
    font_size_main: int = 48
    font_size_debug: int = 24

def load_config() -> AppConfig:
    return AppConfig()

def validate_config(cfg: AppConfig) -> None:
    if cfg.block_size <= 0:
        raise ValueError("Block size must be positive")
    if cfg.sample_rate <= 0:
        raise ValueError("Sample rate must be positive")
    if cfg.fmin >= cfg.fmax:
        raise ValueError("fmin must be lower than fmax")