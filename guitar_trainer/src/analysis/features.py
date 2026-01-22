import numpy as np
import math
from ..core.config import AppConfig
from ..core.types import AudioBlock, Features
from .pitch import PitchTracker
from .stability import StabilityTracker

# Constantes musicales
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def hz_to_note_data(hz: float) -> tuple[str, float]:
    """
    Convertit Hz en (NomNote, Cents).
    Ex: 440 -> ("A4", 0.0)
    Ex: 445 -> ("A4", +19.5)
    """
    if hz <= 0:
        return "-", 0.0
        
    # Formule MIDI : 69 = A4 (440Hz)
    # pitch_midi = 12 * log2(fm / 440) + 69
    midi_float = 12 * np.log2(hz / 440.0) + 69
    
    midi_round = round(midi_float)
    cents = (midi_float - midi_round) * 100
    
    # Trouver le nom
    note_index = midi_round % 12
    octave = (midi_round // 12) - 1
    
    note_name = f"{NOTE_NAMES[note_index]}{octave}"
    return note_name, cents

class FeatureExtractor:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.pitch_tracker = PitchTracker(cfg)
        self.stability_tracker = StabilityTracker(cfg)

    def process(self, block: AudioBlock) -> Features:
        # 1. Calcul RMS (Volume)
        rms = np.sqrt(np.mean(block.samples**2))
        is_voiced = rms > self.cfg.rms_threshold
        
        # 2. Pitch Detection
        f0, conf = self.pitch_tracker.process(block.samples)
        
        # Si la confiance est mauvaise, on ignore le pitch
        if conf < self.cfg.confidence_threshold:
            f0 = None
            
        # 3. Conversion Hz -> Note
        note_name = None
        cents = 0.0
        if f0 is not None:
            note_name, cents = hz_to_note_data(f0)
            
        # 4. Stabilité
        stable, stable_ms = self.stability_tracker.update(
            note_name, cents, is_voiced, block.timestamp
        )

        # 5. Assemblage
        return Features(
            timestamp=block.timestamp,
            rms=float(rms),
            f0_hz=f0,
            note_name=note_name,
            cents=cents,
            confidence=conf,
            is_voiced=is_voiced,
            stable=stable,
            stable_ms=stable_ms
        )