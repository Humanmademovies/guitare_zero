import os
import wave
import numpy as np

class PreviewPlayer:
    """Sampler de prévisualisation des quêtes (Phase B d'Archi.md).

    Charge les samples enregistrés en mode Studio (data/samples/{corde}_{case}.wav)
    et assemble la piste audio d'une séquence de quête :
    - les beats sont convertis en secondes via le tempo de la quête ;
    - les notes partageant le même beat sont jouées en strumming
      (micro-décalage corde grave -> aiguë), ce qui permet de générer des
      accords à partir de notes individuelles ;
    - une corde ne sonne qu'une note à la fois : rejouer une corde coupe
      sa note précédente (court fondu), comme sur un vrai manche.
    """

    STRUM_DELAY_S = 0.012   # décalage entre cordes d'un même beat
    NOTE_GAIN = 0.9
    CUT_FADE_SAMPLES = 256  # ~6 ms de fondu quand une corde est recoupée

    def __init__(self, samples_dir: str = "data/samples", sample_rate: int = 44100):
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.samples_dir = os.path.join(base, samples_dir)
        self.sample_rate = sample_rate  # NB: les samples studio sont en 44100
        self._bank: dict[tuple[int, int], np.ndarray] = {}
        self._real_keys: set[tuple[int, int]] = set()  # samples issus de vrais wav
        self._loaded = False

    # ------------------------------------------------------------------ #

    def _ensure_loaded(self) -> None:
        """Charge la banque au premier usage (pas au lancement du jeu)."""
        if self._loaded:
            return
        self._loaded = True
        if not os.path.isdir(self.samples_dir):
            print(f"[PREVIEW] Dossier samples introuvable : {self.samples_dir}")
            return
        count = 0
        for name in sorted(os.listdir(self.samples_dir)):
            if not name.endswith(".wav"):
                continue
            try:
                string_s, fret_s = os.path.splitext(name)[0].split("_")
                key = (int(string_s), int(fret_s))
            except ValueError:
                continue
            try:
                self._bank[key] = self._load_wav(os.path.join(self.samples_dir, name))
                self._real_keys.add(key)
                count += 1
            except Exception as e:
                print(f"[PREVIEW] Échec de lecture {name} : {e}")
        print(f"[PREVIEW] {count} samples chargés depuis {self.samples_dir}")

    def _load_wav(self, path: str) -> np.ndarray:
        with wave.open(path, "rb") as w:
            if w.getsampwidth() != 2:
                raise ValueError("seul le PCM 16 bits est supporté")
            data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
            data = data.astype(np.float32) / 32768.0
            if w.getnchannels() > 1:
                data = data.reshape(-1, w.getnchannels()).mean(axis=1)
            return data

    # ------------------------------------------------------------------ #

    def _get_sample(self, string: int, fret: int) -> np.ndarray | None:
        """Sample exact, ou pitch-shift du plus proche voisin sur la même corde
        (rééchantillonnage linéaire — le repli disparaît dès que la note est
        enregistrée en mode Studio)."""
        sample = self._bank.get((string, fret))
        if sample is not None:
            return sample
        # Voisin cherché parmi les VRAIS samples uniquement, pour ne pas
        # chaîner des pitch-shifts déjà interpolés
        frets = [f for (s, f) in self._real_keys if s == string]
        if not frets:
            return None
        nearest = min(frets, key=lambda f: abs(f - fret))
        src = self._bank[(string, nearest)]
        ratio = 2.0 ** ((fret - nearest) / 12.0)
        n_out = max(1, int(len(src) / ratio))
        shifted = np.interp(np.arange(n_out) * ratio,
                            np.arange(len(src)), src).astype(np.float32)
        self._bank[(string, fret)] = shifted  # mis en cache
        print(f"[PREVIEW] ({string},{fret}) absent -> pitch-shift depuis ({string},{nearest})")
        return shifted

    def can_preview(self, quest: dict | None) -> bool:
        return bool(quest and quest.get("type") == "rhythm"
                    and quest.get("params", {}).get("sequence"))

    def render_quest(self, quest: dict) -> np.ndarray | None:
        """Construit la piste mono float32 de la séquence, ou None."""
        if not self.can_preview(quest):
            return None
        self._ensure_loaded()
        if not self._bank:
            return None

        params = quest["params"]
        tempo = float(params.get("tempo", 60)) or 60.0
        spb = 60.0 / tempo
        seq = params["sequence"]
        first_beat = min(float(n["beat"]) for n in seq)

        # Strumming : groupes par beat, cordes graves d'abord
        by_beat: dict[float, list[dict]] = {}
        for n in seq:
            by_beat.setdefault(float(n["beat"]), []).append(n)

        per_string: dict[int, list[tuple[int, np.ndarray]]] = {}
        missing = 0
        for beat in sorted(by_beat):
            notes = sorted(by_beat[beat], key=lambda n: -int(n["string"]))
            for i, n in enumerate(notes):
                sample = self._get_sample(int(n["string"]), int(n["fret"]))
                if sample is None:
                    missing += 1
                    continue
                t0 = (beat - first_beat) * spb + i * self.STRUM_DELAY_S
                off = int(t0 * self.sample_rate)
                per_string.setdefault(int(n["string"]), []).append((off, sample))
        if missing:
            print(f"[PREVIEW] {missing} note(s) sans sample correspondant")
        if not per_string:
            return None

        # Une corde coupe sa note précédente quand elle rejoue
        events: list[tuple[int, np.ndarray]] = []
        end = 0
        for string, notes in per_string.items():
            notes.sort(key=lambda e: e[0])
            for i, (off, sample) in enumerate(notes):
                dur = len(sample)
                if i + 1 < len(notes):
                    dur = min(dur, max(1, notes[i + 1][0] - off))
                seg = sample[:dur]
                if dur < len(sample):
                    seg = seg.copy()
                    fade = min(self.CUT_FADE_SAMPLES, dur)
                    seg[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
                events.append((off, seg))
                end = max(end, off + len(seg))

        track = np.zeros(end, dtype=np.float32)
        for off, seg in events:
            track[off:off + len(seg)] += seg * self.NOTE_GAIN

        # Normalisation de sécurité : les superpositions peuvent dépasser 1
        peak = float(np.max(np.abs(track)))
        if peak > 0.9:
            track *= 0.9 / peak
        return track
