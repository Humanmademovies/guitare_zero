import os
import wave
import numpy as np
import pygame
from .guitar_map import GUITAR_MAP

class StudioEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.targets = self._generate_targets()
        self.current_idx = 0
        
        self.state = "WAITING" # WAITING, RECORDING, DONE
        self.record_timer = 0.0
        self.record_duration = 2.5
        self.pre_record_timer = 0.0
        self.pre_record_duration = 0.5 # 0.5 sec de note parfaite avant de lancer l'enregistrement
        
        self.accumulated_samples = []
        self.last_saved_file = None
        
        os.makedirs("data/samples", exist_ok=True)

    def _generate_targets(self):
        targets = []
        for string in [6, 5, 4, 3, 2, 1]:
            for fret in range(5):
                note_name = None
                for name, positions in GUITAR_MAP.items():
                    if (string, fret) in positions:
                        note_name = name
                        break
                if note_name:
                    targets.append({"string": string, "fret": fret, "note": note_name})
        return targets

    def get_current_target(self):
        if 0 <= self.current_idx < len(self.targets):
            return self.targets[self.current_idx]
        return None

    def next_target(self):
        if self.current_idx < len(self.targets) - 1:
            self.current_idx += 1
            self.reset_recording()

    def prev_target(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.reset_recording()

    def reset_recording(self):
        self.state = "WAITING"
        self.record_timer = 0.0
        self.pre_record_timer = 0.0
        self.accumulated_samples = []

    def play_current_sample(self):
        if self.state == "DONE" and self.last_saved_file and os.path.exists(self.last_saved_file):
            try:
                sound = pygame.mixer.Sound(self.last_saved_file)
                sound.play()
            except Exception as e:
                print(f"[STUDIO] Erreur lecture audio : {e}")

    def update(self, features, dt):
        target = self.get_current_target()
        if not target or self.state == "DONE":
            return

        if self.state == "WAITING":
            # On exige la perfection continue pendant "pre_record_duration"
            if features.note_name == target["note"] and features.stable and abs(features.cents) < 3 and features.is_pure:
                self.pre_record_timer += dt
                if self.pre_record_timer >= self.pre_record_duration:
                    self.state = "RECORDING"
                    self.accumulated_samples.append(features.samples)
            else:
                self.pre_record_timer = 0.0 # On reset au moindre défaut
        
        elif self.state == "RECORDING":
            self.record_timer += dt
            self.accumulated_samples.append(features.samples)
            
            if self.record_timer >= self.record_duration:
                self._save_sample(target)
                self.state = "DONE"

    def _save_sample(self, target):
        if not self.accumulated_samples:
            return
        
        audio_data = np.concatenate(self.accumulated_samples)
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        audio_int16 = np.int16(audio_data * 32767)
        
        self.last_saved_file = f"data/samples/{target['string']}_{target['fret']}.wav"
        
        with wave.open(self.last_saved_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.cfg.sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        print(f"[STUDIO] Sample saved: {self.last_saved_file}")
