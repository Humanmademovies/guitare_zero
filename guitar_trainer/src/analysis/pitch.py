import numpy as np
import aubio
from ..core.config import AppConfig
from ..core.types import PitchResult
import math

class PitchTracker:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        # Buffer size (Fenêtre d'analyse)
        self.buf_size = cfg.block_size * 2
        self.hop_size = cfg.block_size
        
        # 1. CHANGEMENT ALGO : On passe de "yinfft" (Spectral) à "yin" (Temporel)
        # "yin" est beaucoup plus stable pour la guitare et la voix.
        self.pitch_o = aubio.pitch("yin", self.buf_size, self.hop_size, cfg.sample_rate)
        
        self.pitch_o.set_unit("Hz")
        
        # Tolérance de l'algorithme (0.15 est un bon standard pour Yin)
        # On utilise la valeur de config si elle est proche, sinon 0.15 par défaut
        self.pitch_o.set_tolerance(cfg.confidence_threshold)
        
        # 2. CHANGEMENT SILENCE : On ouvre les vannes (-90dB)
        # On ne veut pas qu'Aubio décide ce qui est du silence, c'est le rôle du RMS dans features.py
        self.pitch_o.set_silence(-90.0)

    def process(self, audio_block) -> PitchResult:
        """Process an audio block to extract pitch info."""
        # CORRECTION : On extrait le tableau numpy de l'objet AudioBlock
        # et on le convertit en float32 pour Aubio
        samples = audio_block.samples.astype('float32')

        # Aubio nécessite que le bloc fasse exactement la taille 'hop_size'
        if samples.shape[0] != self.hop_size:
            return PitchResult(0.0, 0.0, None, 0.0)

        # Calcul du pitch avec Aubio
        pitch = self.pitch_o(samples)[0]
        confidence = self.pitch_o.get_confidence()
        
        note_name = None
        cents = 0.0
        if pitch > 0:
            note_name, cents = self._hz_to_note(pitch)
            
        return PitchResult(
            frequency=pitch,
            confidence=confidence,
            note_name=note_name,
            cents=cents
        )
    
    def _hz_to_note(self, f0: float) -> tuple[str, float]:
        """Convertit une fréquence en Hz en nom de note (ex: 'E2') et cents."""
        if f0 <= 0:
            return "...", 0.0

        # Calcul du numéro MIDI (A4 = 440Hz = MIDI 69)
        midi = 12 * math.log2(f0 / 440.0) + 69
        rounded_midi = round(midi)
        
        # Calcul de l'écart en cents (justesse)
        cents = (midi - rounded_midi) * 100
        
        # Mapping des noms de notes
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        note_name = names[rounded_midi % 12]
        octave = (rounded_midi // 12) - 1
        
        return f"{note_name}{octave}", cents