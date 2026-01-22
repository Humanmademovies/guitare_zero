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
    def __init__(self, cfg):
        self.cfg = cfg
        # On ré-intègre les trackers ici pour que la classe soit autonome
        self.pitch_tracker = PitchTracker(cfg)
        self.stability_tracker = StabilityTracker(cfg)

    def process(self, audio_block) -> Features:
        """Analyse complète d'un bloc audio."""
        samples = audio_block.samples
        
        # 1. Calcul du Pitch (On utilise le bon nom de méthode : process)
        pitch_result = self.pitch_tracker.process(audio_block)
        f0 = pitch_result.frequency
        conf = pitch_result.confidence
        
        # 2. Calcul du volume (RMS)
        rms = np.sqrt(np.mean(samples**2)) if len(samples) > 0 else 0.0

        # 3. Calcul de la Pureté (Flatness)
        flatness = 1.0
        power_spectrum = np.zeros(len(samples)//2 + 1)
        if len(samples) > 0 and rms > 1e-5:
            fft_magnitude = np.abs(np.fft.rfft(samples))
            power_spectrum = fft_magnitude**2
            power_spectrum = np.where(power_spectrum == 0, 1e-10, power_spectrum)
            arithmetic_mean = np.mean(power_spectrum)
            geometric_mean = np.exp(np.mean(np.log(power_spectrum)))
            flatness = geometric_mean / arithmetic_mean

        # 4. Indicateurs binaires
        is_pure = flatness < self.cfg.flatness_threshold
        is_voiced = (f0 > 0) and (conf > self.cfg.confidence_threshold) and (rms > self.cfg.rms_threshold) and is_pure

        # 5. Création de l'objet Features temporaire
        feats_temp = Features(
            timestamp=audio_block.timestamp,
            f0_hz=f0,
            note_name=pitch_result.note_name,
            cents=pitch_result.cents,
            rms=rms,
            flatness=flatness,
            raw_f0=f0,
            raw_confidence=conf,
            is_voiced=is_voiced,
            is_pure=is_pure,
            spectrum=power_spectrum,
            samples=samples,
            stable=False
        )

        # 6. Calcul de la Stabilité
        stable = self.stability_tracker.update(feats_temp)
        feats_temp.stable = stable

        return feats_temp