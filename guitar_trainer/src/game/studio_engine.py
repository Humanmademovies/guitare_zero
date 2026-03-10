import os
import wave
import numpy as np
from collections import deque
from .guitar_map import GUITAR_MAP

class StudioEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.samples_dir = "data/samples"
        os.makedirs(self.samples_dir, exist_ok=True)

        self.targets = self._generate_targets()
        self.current_idx = 0

        self.state = "WAITING"
        self.record_timer = 0.0
        self.record_duration = 2.5
        self.confirm_timer = 0.0
        self.confirm_duration = 0.3

        self.ring_buffer = deque()
        self.ring_max_blocks = int((0.5 * cfg.sample_rate) / cfg.block_size)
        self.accumulated_samples = []

        self._scan_existing()
        self._advance_to_first_undone()

    def _generate_targets(self):
        positions = set()
        for note_name, pos_list in GUITAR_MAP.items():
            for string, fret in pos_list:
                positions.add((string, fret, note_name))

        grouped = {}
        for string, fret, note_name in positions:
            key = (string, fret)
            if key not in grouped:
                grouped[key] = note_name

        targets = []
        for (string, fret), note_name in sorted(grouped.items(), key=lambda x: (-x[0][0], x[0][1])):
            targets.append({
                "string": string,
                "fret": fret,
                "note": note_name,
                "done": False
            })
        return targets

    def _scan_existing(self):
        for target in self.targets:
            path = self._get_sample_path(target)
            if os.path.exists(path):
                target["done"] = True

    def _advance_to_first_undone(self):
        for i, target in enumerate(self.targets):
            if not target["done"]:
                self.current_idx = i
                return
        self.current_idx = 0

    def _get_sample_path(self, target):
        return os.path.join(self.samples_dir, f"{target['string']}_{target['fret']}.wav")

    def get_current_target(self):
        if 0 <= self.current_idx < len(self.targets):
            return self.targets[self.current_idx]
        return None

    def get_progress(self):
        done = sum(1 for t in self.targets if t["done"])
        return done, len(self.targets)

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
        self.confirm_timer = 0.0
        self.accumulated_samples = []
        self.ring_buffer.clear()

    def get_last_saved_path(self):
        target = self.get_current_target()
        if target and target["done"]:
            path = self._get_sample_path(target)
            if os.path.exists(path):
                return path
        return None

    def update(self, features, dt):
        target = self.get_current_target()
        if not target or self.state == "DONE":
            return

        if features.samples is not None:
            self.ring_buffer.append(features.samples.copy())
            if len(self.ring_buffer) > self.ring_max_blocks:
                self.ring_buffer.popleft()

        if self.state == "WAITING":
            is_good = (
                features.note_name == target["note"]
                and features.is_voiced
                and abs(features.cents) < 10
            )
            if is_good:
                self.confirm_timer += dt
                if self.confirm_timer >= self.confirm_duration:
                    self.state = "RECORDING"
                    for block in self.ring_buffer:
                        self.accumulated_samples.append(block)
                    self.ring_buffer.clear()
            else:
                self.confirm_timer = 0.0

        elif self.state == "RECORDING":
            self.record_timer += dt
            if features.samples is not None:
                self.accumulated_samples.append(features.samples.copy())

            if self.record_timer >= self.record_duration:
                self._save_sample(target)
                self.state = "DONE"

    def _save_sample(self, target):
        if not self.accumulated_samples:
            return

        audio_data = np.concatenate(self.accumulated_samples)

        fade_samples = int(0.2 * self.cfg.sample_rate)
        if fade_samples > 0 and len(audio_data) > fade_samples:
            fade_curve = np.linspace(1.0, 0.0, fade_samples)
            audio_data[-fade_samples:] *= fade_curve

        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        audio_int16 = np.int16(audio_data * 32767)

        path = self._get_sample_path(target)
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.cfg.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        target["done"] = True
        print(f"[STUDIO] Sample saved: {path}")
