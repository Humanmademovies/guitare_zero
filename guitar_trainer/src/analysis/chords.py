import numpy as np
import aubio

# Accordage standard : corde -> note MIDI à vide
# 6=E2(40) 5=A2(45) 4=D3(50) 3=G3(55) 2=B3(59) 1=E4(64)
OPEN_STRING_MIDI = {6: 40, 5: 45, 4: 50, 3: 55, 2: 59, 1: 64}

def position_to_freq(string: int, fret: int) -> float:
    """Fréquence fondamentale d'une position (corde, case)."""
    midi = OPEN_STRING_MIDI[string] + fret
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)

class ChordDetector:
    """Validation spectrale d'un accord ATTENDU — pas de transcription aveugle.

    Le jeu sait quel accord doit être joué : on mesure la saillance spectrale
    de chaque note attendue (pic FFT proche de sa fondamentale, au-dessus du
    plancher de bruit médian) et l'accord est présent si TOUTES les notes le
    sont simultanément.

    - Fenêtre glissante de `window_size` échantillons (8192 @ 44,1 kHz
      ~ 186 ms, 5,4 Hz/bin) alimentée bloc par bloc via push().
    - Interpolation parabolique du pic (log-magnitude) : précision sous-bin,
      nécessaire pour séparer E2 (82,4 Hz) de F2 (87,3 Hz).
    - Limitation connue : un power chord joué à l'octave supérieure peut
      valider l'accord grave (ses notes coïncident avec les harmoniques) —
      acceptable pour la campagne power chords qui n'utilise que les formes
      graves.
    """

    def __init__(self, sample_rate: int = 44100, window_size: int = 8192,
                 threshold_db: float = 15.0, cents_tol: float = 50.0,
                 rms_threshold: float = 0.003, hop_size: int = 512):
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.threshold_db = threshold_db
        self.cents_tol = cents_tol
        self.rms_threshold = rms_threshold
        self.hop_size = hop_size
        self._ring = np.zeros(window_size, dtype=np.float32)
        self._filled = 0
        self._hann = np.hanning(window_size).astype(np.float32)

        # Détection d'attaques (coups de médiator) : un accord TENU ne doit
        # pas pouvoir valider plusieurs cibles — chaque validation consomme
        # une attaque. HFC = référence pour les transitoires de pincement.
        self.onset_count = 0
        self._samples_pushed = 0
        self._last_onset_sample = -1
        self._onset_buf = np.zeros(0, dtype=np.float32)
        self._make_onset()

    def _make_onset(self) -> None:
        self._onset = aubio.onset("hfc", 1024, self.hop_size, self.sample_rate)
        self._onset.set_minioi_ms(150.0)   # fusionne le strum en UNE attaque
        self._onset.set_silence(-50.0)

    def reset(self) -> None:
        self._ring[:] = 0.0
        self._filled = 0
        self.onset_count = 0
        self._samples_pushed = 0
        self._last_onset_sample = -1
        self._onset_buf = np.zeros(0, dtype=np.float32)
        self._make_onset()

    def push(self, samples: np.ndarray) -> None:
        """Ajoute un bloc mono float32 à la fenêtre glissante."""
        n = len(samples)
        if n <= 0:
            return
        if n >= self.window_size:
            self._ring[:] = samples[-self.window_size:]
        else:
            self._ring = np.roll(self._ring, -n)
            self._ring[-n:] = samples
        self._filled = min(self.window_size, self._filled + n)
        self._samples_pushed += n

        # Détection d'attaques, hop par hop (reliquat bufferisé)
        buf = np.concatenate((self._onset_buf, samples.astype(np.float32, copy=False)))
        n_hops = len(buf) // self.hop_size
        for i in range(n_hops):
            hop = np.ascontiguousarray(buf[i * self.hop_size:(i + 1) * self.hop_size])
            if self._onset(hop)[0] > 0:
                self.onset_count += 1
                self._last_onset_sample = self._samples_pushed
        self._onset_buf = buf[n_hops * self.hop_size:]

    def seconds_since_onset(self) -> float:
        """Âge de la dernière attaque détectée (1e9 si aucune)."""
        if self._last_onset_sample < 0:
            return 1e9
        return (self._samples_pushed - self._last_onset_sample) / self.sample_rate

    def detect(self, positions: list[tuple[int, int]]) -> dict:
        """positions : liste de (corde, case) attendues.
        Retourne {present, rms, notes:[{string, fret, ok, peak_hz, cents, salience_db}]}."""
        result = {"present": False, "rms": 0.0, "notes": []}
        if self._filled < self.window_size or not positions:
            return result

        x = self._ring
        rms = float(np.sqrt(np.mean(x ** 2)))
        result["rms"] = rms
        if rms < self.rms_threshold:
            return result

        power = np.abs(np.fft.rfft(x * self._hann)) ** 2
        floor = float(np.median(power)) + 1e-20
        bin_hz = self.sample_rate / self.window_size

        all_ok = True
        for (string, fret) in positions:
            f0 = position_to_freq(int(string), int(fret))
            ok, info = self._note_salience(power, floor, bin_hz, f0)
            info["string"], info["fret"] = int(string), int(fret)
            info["target_hz"] = round(f0, 1)
            result["notes"].append(info)
            all_ok = all_ok and ok
        result["present"] = all_ok
        return result

    def _note_salience(self, power: np.ndarray, floor: float,
                       bin_hz: float, f0: float) -> tuple[bool, dict]:
        # Bande de recherche : ±6 % (~1 demi-ton), au moins ±2 bins
        half = max(f0 * 0.06, 2.0 * bin_hz)
        lo = max(1, int((f0 - half) / bin_hz))
        hi = min(len(power) - 2, int((f0 + half) / bin_hz) + 1)
        if hi <= lo:
            return False, {"ok": False, "peak_hz": 0.0, "cents": 9999.0, "salience_db": 0.0}

        k = lo + int(np.argmax(power[lo:hi + 1]))

        # Interpolation parabolique sur le log-magnitude : position sous-bin du pic
        a = float(np.log(power[k - 1] + 1e-20))
        b = float(np.log(power[k] + 1e-20))
        c = float(np.log(power[k + 1] + 1e-20))
        denom = a - 2.0 * b + c
        delta = 0.5 * (a - c) / denom if abs(denom) > 1e-12 else 0.0
        delta = float(np.clip(delta, -0.5, 0.5))
        peak_hz = (k + delta) * bin_hz

        salience_db = 10.0 * float(np.log10((power[k] + 1e-20) / floor))
        cents = 1200.0 * float(np.log2(peak_hz / f0)) if peak_hz > 0 else 9999.0
        ok = bool(salience_db >= self.threshold_db and abs(cents) <= self.cents_tol)
        return ok, {"ok": ok, "peak_hz": round(peak_hz, 1),
                    "cents": round(cents, 1), "salience_db": round(salience_db, 1)}
