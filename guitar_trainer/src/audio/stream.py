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

    def start(self) -> None:
        if self.running:
            return
        
        # Résolution des périphériques
        from .devices import resolve_device_index
        
        dev_in = resolve_device_index(self.cfg.device_name_or_index, 'input')
        dev_out = resolve_device_index(self.cfg.output_device_name_or_index, 'output')
        
        print(f"[AUDIO START] Requesting Devices -> In: {dev_in}, Out: {dev_out} @ {self.cfg.sample_rate}Hz")

        # --- Recharger le Processeur ---
        # On utilise self.cfg ici !
        print("[DEBUG] Attempting to load AudioProcessor...")
        self.processor = AudioProcessor(self.cfg.sample_rate, self.cfg.block_size)
        self.processor.set_gate_threshold(self.cfg.gate_threshold)
        self.processor.set_tone(self.cfg.tone)
        print("[AUDIO] Pedalboard Processor initialized SUCCESS.")
        # -------------------------------

        try:
            self.stream = sd.Stream(
                device=(dev_in, dev_out),
                channels=self.cfg.channels,
                samplerate=self.cfg.sample_rate,
                blocksize=self.cfg.block_size,
                dtype='float32',
                callback=self._callback
            )
            self.stream.start()
            self.running = True
            
            latency = self.stream.latency[1] * 1000 if self.stream.latency else 0
            print(f"[AUDIO] Stream started. Output Latency: ~{latency:.2f} ms")
            
        except Exception as e:
            print(f"[AUDIO CRITICAL] Failed to start stream: {e}")
            self.running = False

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
        if status:
            pass # Ignorer les erreurs xrun pour l'instant

        # 1. Copie pour Analyse
        samples = indata.flatten().copy()
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
        mix = np.array(indata, dtype='float32', copy=True)
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
                outdata[:] = mix
        else:
            outdata[:] = mix

    def _compute_rms(self, samples: np.ndarray) -> float:
        return float(np.sqrt(np.mean(samples**2)))
    
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
