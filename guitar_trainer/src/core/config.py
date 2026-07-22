import json
import os
from dataclasses import dataclass, asdict, fields

# Overrides utilisateur, relatif au cwd de lancement (guitar_trainer/).
# Non versionné : contient des réglages propres à la machine (périphériques, gain).
CONFIG_PATH = "config.json"

@dataclass
class AppConfig:
    # --- Audio ---
    sample_rate: int = 44100
    block_size: int = 512  # compromis latence/stabilité : 256 = xruns (GIL disputé avec l'UI 60 FPS)
    channels: int = 1

    # Entrée (Micro / Câble Guitare) — index, ou nom partiel (stable entre reboots)
    device_name_or_index: str | int | None = 2

    # Sortie (Enceintes PC)
    output_device_name_or_index: str | int | None = None

    # Effets / Traitement
    input_gain: float = 2.0  # Gain logiciel d'entrée (guitare passive -> signal faible)
    gate_threshold: float = 0.05
    tone: float = 0.6    # Coupure du filtre : 400 + v*11600 Hz (0.6 ~ 7,4 kHz)
    drive: float = 0.0   # 0 = disto hors chaîne
    volume: float = 0.8  # Gain de sortie du monitoring

    # --- Analyse (Pitch & Features) ---
    fmin: float = 40.0
    fmax: float = 2000.0
    confidence_threshold: float = 0.2
    rms_threshold: float = 0.003
    flatness_threshold: float = 0.15

    # --- Stabilité ---
    stable_window_ms: float = 500.0
    stable_cents_tolerance: float = 15.0

    # --- UI ---
    window_title: str = "Guitar Trainer MVP"
    window_size: tuple[int, int] = (1600, 1200)
    fps: int = 60
    font_size_main: int = 48
    font_size_debug: int = 24

def load_config() -> AppConfig:
    """Valeurs par défaut du dataclass, surchargées par config.json s'il existe."""
    cfg = AppConfig()
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            known = {fld.name for fld in fields(AppConfig)}
            for key, value in data.items():
                if key in known:
                    setattr(cfg, key, value)
            cfg.window_size = tuple(cfg.window_size)
            print(f"[CONFIG] Overrides chargés depuis {CONFIG_PATH}")
    except Exception as e:
        print(f"[CONFIG] Lecture de {CONFIG_PATH} impossible ({e}) — valeurs par défaut")
        cfg = AppConfig()
    return cfg

def save_config(cfg: AppConfig) -> None:
    """Persiste la config courante (appelé à la fermeture, en sortie d'accordeur
    et après un changement de périphérique réussi)."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(cfg), f, indent=2, ensure_ascii=False)
        print(f"[CONFIG] Sauvegardé dans {CONFIG_PATH}")
    except Exception as e:
        print(f"[CONFIG] Échec de sauvegarde : {e}")

def validate_config(cfg: AppConfig) -> None:
    if cfg.block_size <= 0:
        raise ValueError("Block size must be positive")
    if cfg.sample_rate <= 0:
        raise ValueError("Sample rate must be positive")
    if cfg.fmin >= cfg.fmax:
        raise ValueError("fmin must be lower than fmax")
    if cfg.input_gain <= 0:
        raise ValueError("input_gain must be positive")
