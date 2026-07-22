import math
import numpy as np
from pedalboard import Pedalboard, NoiseGate, Distortion, LowpassFilter, Reverb, Gain

class AudioProcessor:
    """Chaîne d'effets de monitoring : gate -> disto -> tone -> réverbe -> volume.

    Exécutée en C++ (JUCE) via pedalboard — le GIL est relâché pendant le
    traitement, coût mesuré ~0,03 ms par bloc de 1024 contre ~8 ms pour
    l'ancien DSP maison (boucles Python par échantillon, cf. historique git).

    L'API et les mappings sont ceux de l'ancien processeur : les potards
    envoient des valeurs linéaires 0-1, converties ici en dB/Hz.
    """

    def __init__(self, sample_rate: int, block_size: int):
        self.sample_rate = sample_rate
        self.block_size = block_size

        # Attack/release repris de l'ancien SoftGate (5 ms / 50 ms)
        self._gate = NoiseGate(threshold_db=-100.0, ratio=10.0,
                               attack_ms=5.0, release_ms=50.0)
        self._disto = Distortion(drive_db=0.0)
        self._tone = LowpassFilter(cutoff_frequency_hz=10000.0)
        self._reverb = Reverb(room_size=0.5, wet_level=0.2, dry_level=0.8, width=1.0)
        self._gain = Gain(gain_db=0.0)
        self.board = Pedalboard([self._gate, self._disto, self._tone,
                                 self._reverb, self._gain])

    def process(self, input_audio: np.ndarray) -> np.ndarray:
        """Entrée (1, N) float32 contigu, sortie même forme (état conservé entre blocs)."""
        out = self.board(input_audio, self.sample_rate, reset=False)
        return np.clip(out, -1.0, 1.0)

    def set_gate_threshold(self, value: float) -> None:
        # Héritage de l'ancien SoftGate : potard x0.1 = seuil linéaire
        # (potard 0.05 -> 0.005 RMS ~ -46 dB). 0 -> gate ouvert en permanence.
        linear = max(float(value) * 0.1, 1e-5)
        self._gate.threshold_db = 20.0 * math.log10(linear)

    def set_drive(self, value: float) -> None:
        # Ancien mapping : gain linéaire 1 + value*20 avant écrêtage tanh
        self._disto.drive_db = 20.0 * math.log10(1.0 + float(value) * 20.0)

    def set_tone(self, value: float) -> None:
        self._tone.cutoff_frequency_hz = 400.0 + float(value) * 11600.0

    def set_volume(self, value: float) -> None:
        if value <= 0.01:
            self._gain.gain_db = -100.0
        else:
            self._gain.gain_db = 20.0 * math.log10(float(value))
