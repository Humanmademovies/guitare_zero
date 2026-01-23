import numpy as np
from pedalboard import Pedalboard, NoiseGate, Compressor, Distortion, Reverb, Gain, LowpassFilter

class AudioProcessor:
    def __init__(self, sample_rate: int, block_size: int):
        self.sample_rate = sample_rate
        self.block_size = block_size
        
        # Chaîne : Gate -> Comp -> Disto -> TONE (Filtre) -> Reverb -> Volume
        self.board = Pedalboard([
            NoiseGate(threshold_db=-60),
            Compressor(threshold_db=-20, ratio=4),
            Distortion(drive_db=0),
            LowpassFilter(cutoff_frequency_hz=10000), # Par défaut ouvert à 10kHz
            Reverb(room_size=0.2, wet_level=0.2),
            Gain(gain_db=0)
        ])

    def process(self, input_audio: np.ndarray) -> np.ndarray:
        return self.board(input_audio, self.sample_rate)

    def set_gate_threshold(self, value: float) -> None:
        threshold_db = -100.0 + (value * 80.0)
        for plugin in self.board:
            if isinstance(plugin, NoiseGate):
                plugin.threshold_db = threshold_db
                break

    def set_drive(self, value: float) -> None:
        drive_db = value * 40.0
        for plugin in self.board:
            if isinstance(plugin, Distortion):
                plugin.drive_db = drive_db
                break
    
    def set_tone(self, value: float) -> None:
        """
        value 0.0 -> 400 Hz (Très sourd / Jazz)
        value 1.0 -> 12000 Hz (Très brillant / Hiss audible)
        Le 'Sweet Spot' anti-souffle sera vers 0.4 - 0.6
        """
        # Mapping linéaire simple pour commencer
        cutoff = 400.0 + (value * 11600.0) 
        
        for plugin in self.board:
            if isinstance(plugin, LowpassFilter):
                plugin.cutoff_frequency_hz = cutoff
                break

    def set_volume(self, value: float) -> None:
        if value <= 0.01:
            vol_db = -100.0
        else:
            vol_db = 20 * np.log10(value)
        
        for plugin in self.board:
            if isinstance(plugin, Gain):
                plugin.gain_db = vol_db
                break