import queue
import time
import numpy as np
import sounddevice as sd
from ..core.config import AppConfig
from ..core.types import AudioBlock

class AudioStream:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.queue: "queue.Queue[AudioBlock]" = queue.Queue()
        self.stream = None
        self.running = False
        self._last_rms = 0.0

    def start(self) -> None:
        if self.running:
            return
        
        device_index = self.cfg.device_name_or_index
        if isinstance(device_index, str):
            # Petit fix temporaire si resolve n'est pas appelé avant
            from .devices import resolve_input_device
            device_index = resolve_input_device(device_index)

        try:
            self.stream = sd.InputStream(
                device=device_index,
                channels=self.cfg.channels,
                samplerate=self.cfg.sample_rate,
                blocksize=self.cfg.block_size,
                dtype='float32',  # Important pour l'analyse
                callback=self._callback
            )
            self.stream.start()
            self.running = True
            print(f"[AUDIO] Stream started on device {device_index} (SR={self.cfg.sample_rate})")
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
        """Pour affichage VU-mètre rapide (accédé par UI)."""
        return self._last_rms

    def _callback(self, indata, frames, time_info, status):
        """
        Appelé par le thread audio système. 
        Doit être ULTRA RAPIDE : pas de print lourds, pas de calculs complexes.
        """
        if status:
            print(f"[AUDIO XRUN] {status}")

        # On aplatit le tableau pour avoir un vecteur 1D propre (ex: [1024])
        # .copy() est obligatoire car indata est recyclé par le driver
        samples = indata.flatten().copy()
        
        # Calcul RMS léger immédiat pour retour visuel
        self._last_rms = self._compute_rms(samples)

        # On empile pour l'analyseur (qui tournera dans son thread)
        block = AudioBlock(
            samples=samples,
            sample_rate=self.cfg.sample_rate,
            timestamp=time.time()
        )
        try:
            self.queue.put_nowait(block)
        except queue.Full:
            pass # Si l'analyse traîne, on jette les frames (drop) plutôt que crasher l'audio

    def _compute_rms(self, samples: np.ndarray) -> float:
        # Root Mean Square simple
        return float(np.sqrt(np.mean(samples**2)))