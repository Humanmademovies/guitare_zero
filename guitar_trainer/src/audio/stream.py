import queue
import time
import numpy as np
import sounddevice as sd
from ..core.config import AppConfig
from ..core.types import AudioBlock

# On veut que ça plante si le fichier ou la librairie n'est pas là !
from .processor import AudioProcessor

class AudioStream:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.queue: "queue.Queue[AudioBlock]" = queue.Queue()
        self.stream = None
        self.running = False
        self._last_rms = 0.0
        self.processor = None
        self._playback_buffer = None
        self._playback_pos = 0
        self.last_error: str | None = None
        self._input_gain = float(cfg.input_gain)
        self._xruns = 0
        self._xruns_reported = 0
        # Instrumentation : crêtes/écrêtage accumulés dans le callback,
        # lus et remis à zéro par le thread principal via poll_meter()
        self._peak_in = 0.0
        self._peak_out = 0.0
        self._clip_count = 0

    def start(self) -> bool:
        if self.running:
            return True
        
        # Résolution des périphériques
        from .devices import resolve_device_index
        
        dev_in = resolve_device_index(self.cfg.device_name_or_index, 'input')
        dev_out = resolve_device_index(self.cfg.output_device_name_or_index, 'output')
        
        print(f"[AUDIO START] Requesting Devices -> In: {dev_in}, Out: {dev_out} @ {self.cfg.sample_rate}Hz")

        # --- Recharger le Processeur ---
        # On utilise self.cfg ici !
        print("[DEBUG] Attempting to load AudioProcessor...")
        self._input_gain = float(self.cfg.input_gain)
        self.processor = AudioProcessor(self.cfg.sample_rate, self.cfg.block_size)
        self.processor.set_gate_threshold(self.cfg.gate_threshold)
        self.processor.set_tone(self.cfg.tone)
        self.processor.set_drive(self.cfg.drive)
        self.processor.set_volume(self.cfg.volume)
        print("[AUDIO] Pedalboard Processor initialized SUCCESS.")
        # -------------------------------

        try:
            self.stream = sd.Stream(
                device=(dev_in, dev_out),
                channels=self.cfg.channels,
                samplerate=self.cfg.sample_rate,
                blocksize=self.cfg.block_size,
                dtype='float32',
                latency='high',  # 'low' imposait des echeances de 2,7 ms au serveur audio : fragile aux a-coups CPU
                callback=self._callback
            )
            self.stream.start()
            self.running = True
            self.last_error = None

            latency = self.stream.latency[1] * 1000 if self.stream.latency else 0
            print(f"[AUDIO] Stream started. Output Latency: ~{latency:.2f} ms")
            return True

        except Exception as e:
            print(f"[AUDIO CRITICAL] Failed to start stream: {e}")
            self.last_error = str(e)
            self.running = False
            return False

    def stop(self) -> None:
        if not self.running:
            return
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.running = False
        print("[AUDIO] Stream stopped")

    def is_running(self) -> bool:
        return self.running

    def get_queue(self) -> "queue.Queue[AudioBlock]":
        return self.queue

    def get_last_rms(self) -> float:
        return self._last_rms

    def _callback(self, indata, outdata, frames, time_info, status):
        # JAMAIS de print ici : toute I/O console peut bloquer le callback
        # au-delà de sa deadline et provoquer elle-même des dropouts.
        if status:
            self._xruns += 1

        # 0. Gain d'entrée logiciel (guitare passive -> signal faible)
        boosted = indata * self._input_gain

        # 1. Copie pour Analyse
        samples = boosted.flatten()
        self._last_rms = self._compute_rms(samples)

        block = AudioBlock(
            samples=samples,
            sample_rate=self.cfg.sample_rate,
            timestamp=time.time()
        )
        try:
            self.queue.put_nowait(block)
        except queue.Full:
            pass

        # 2. Mixage du sample en lecture dans le signal d'entrée
        # (boosted est déjà une copie fraîche, samples a été extrait par flatten)
        mix = boosted
        if self._playback_buffer is not None:
            buf = self._playback_buffer
            pos = self._playback_pos
            remaining = len(buf) - pos
            n = min(frames, remaining)
            mix[:n, 0] += buf[pos:pos + n]
            self._playback_pos += n
            if self._playback_pos >= len(buf):
                self._playback_buffer = None
                self._playback_pos = 0

        # 3. Traitement Audio
        if self.processor:
            try:
                input_contiguous = np.ascontiguousarray(mix.T, dtype='float32')
                processed_matrix = self.processor.process(input_contiguous)
                outdata[:] = processed_matrix.T
            except Exception:
                outdata[:] = np.clip(mix, -1.0, 1.0)
        else:
            outdata[:] = np.clip(mix, -1.0, 1.0)

        # --- Instrumentation : accumulation seule, affichage hors callback ---
        self._peak_in = max(self._peak_in, float(np.max(np.abs(samples))))
        self._peak_out = max(self._peak_out, float(np.max(np.abs(outdata))))
        self._clip_count += int(np.sum(np.abs(outdata) >= 0.999))

    def poll_meter(self) -> dict:
        """Relève et remet à zéro les compteurs (appelé ~1x/s par le thread principal)."""
        m = {
            "in_peak": self._peak_in,
            "out_peak": self._peak_out,
            "clipped": self._clip_count,
            "xruns": self._xruns - self._xruns_reported,
        }
        self._xruns_reported = self._xruns
        self._peak_in = 0.0
        self._peak_out = 0.0
        self._clip_count = 0
        return m

    def _compute_rms(self, samples: np.ndarray) -> float:
        return float(np.sqrt(np.mean(samples**2)))
    
    def set_input_gain(self, value: float) -> None:
        self._input_gain = max(0.1, float(value))

    def set_gate_threshold(self, value: float) -> None:
        if self.processor:
            self.processor.set_gate_threshold(value)

    def set_drive(self, value: float) -> None:
        print(f"[DEBUG] Setting Drive to {value:.2f} - Processor active? {self.processor is not None}")
        if self.processor:
            self.processor.set_drive(value)

    def set_volume(self, value: float) -> None:
        if self.processor:
            self.processor.set_volume(value)
    
    def set_tone(self, value: float) -> None:
        if self.processor:
            self.processor.set_tone(value)
    
    def play_sample(self, samples: np.ndarray) -> None:
        self._playback_buffer = samples.astype('float32')
        self._playback_pos = 0
