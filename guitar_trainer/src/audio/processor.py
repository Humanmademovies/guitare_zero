import numpy as np

class SoftGate:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.threshold = 0.0
        self._envelope = 1.0
        self._attack_coeff = 1.0 - np.exp(-1.0 / (0.005 * sample_rate))
        self._release_coeff = 1.0 - np.exp(-1.0 / (0.05 * sample_rate))

    def set_threshold(self, value):
        self.threshold = value * 0.1

    def process(self, samples):
        if self.threshold <= 0.0:
            return samples
        rms = np.sqrt(np.mean(samples ** 2))
        target = 1.0 if rms > self.threshold else 0.0
        coeff = self._attack_coeff if target > self._envelope else self._release_coeff
        out = np.empty_like(samples)
        env = self._envelope
        for i in range(len(samples)):
            env += coeff * (target - env)
            out[i] = samples[i] * env
        self._envelope = env
        return out


class Distortion:
    def __init__(self):
        self.drive = 1.0

    def set_drive(self, value):
        self.drive = 1.0 + value * 20.0

    def process(self, samples):
        if self.drive <= 1.01:
            return samples
        driven = samples * self.drive
        return np.tanh(driven) * (1.0 / np.tanh(self.drive))


class ToneFilter:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self._prev = 0.0
        self.set_cutoff(10000.0)

    def set_cutoff(self, freq_hz):
        freq_hz = max(20.0, min(freq_hz, self.sample_rate * 0.49))
        rc = 1.0 / (2.0 * np.pi * freq_hz)
        dt = 1.0 / self.sample_rate
        self._alpha = dt / (rc + dt)

    def set_tone(self, value):
        cutoff = 400.0 + (value * 11600.0)
        self.set_cutoff(cutoff)

    def process(self, samples):
        out = np.empty_like(samples)
        prev = self._prev
        alpha = self._alpha
        for i in range(len(samples)):
            prev = prev + alpha * (samples[i] - prev)
            out[i] = prev
        self._prev = prev
        return out


class SimpleReverb:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.wet = 0.2
        self.room_size = 0.5

        comb_delays_ms = [29.7, 37.1, 41.1, 43.7]
        self._comb_buffers = []
        self._comb_indices = []
        self._comb_feedbacks = []
        for delay_ms in comb_delays_ms:
            size = int(delay_ms * sample_rate / 1000.0)
            self._comb_buffers.append(np.zeros(size, dtype=np.float32))
            self._comb_indices.append(0)
            self._comb_feedbacks.append(0.7 * self.room_size)

        allpass_delays_ms = [5.0, 1.7]
        self._ap_buffers = []
        self._ap_indices = []
        self._ap_gain = 0.5
        for delay_ms in allpass_delays_ms:
            size = int(delay_ms * sample_rate / 1000.0)
            self._ap_buffers.append(np.zeros(size, dtype=np.float32))
            self._ap_indices.append(0)

    def process(self, samples):
        if self.wet <= 0.01:
            return samples

        n = len(samples)
        wet_signal = np.zeros(n, dtype=np.float32)

        for c in range(len(self._comb_buffers)):
            buf = self._comb_buffers[c]
            idx = self._comb_indices[c]
            fb = self._comb_feedbacks[c]
            buf_len = len(buf)
            for i in range(n):
                delayed = buf[idx]
                buf[idx] = samples[i] + delayed * fb
                idx = (idx + 1) % buf_len
                wet_signal[i] += delayed
            self._comb_indices[c] = idx

        wet_signal *= (1.0 / len(self._comb_buffers))

        for a in range(len(self._ap_buffers)):
            buf = self._ap_buffers[a]
            idx = self._ap_indices[a]
            g = self._ap_gain
            buf_len = len(buf)
            for i in range(n):
                delayed = buf[idx]
                inp = wet_signal[i]
                buf[idx] = inp + delayed * g
                wet_signal[i] = delayed - inp * g
                idx = (idx + 1) % buf_len
            self._ap_indices[a] = idx

        return samples * (1.0 - self.wet) + wet_signal * self.wet


class AudioProcessor:
    def __init__(self, sample_rate: int, block_size: int):
        self.sample_rate = sample_rate
        self.block_size = block_size

        self.gate = SoftGate(sample_rate)
        self.distortion = Distortion()
        self.tone = ToneFilter(sample_rate)
        self.reverb = SimpleReverb(sample_rate)
        self.gain_db = 0.0
        self._gain_linear = 1.0

    def process(self, input_audio: np.ndarray) -> np.ndarray:
        mono = input_audio[0] if input_audio.ndim == 2 else input_audio

        out = self.gate.process(mono)
        out = self.distortion.process(out)
        out = self.tone.process(out)
        out = self.reverb.process(out)
        out = out * self._gain_linear

        out = np.clip(out, -1.0, 1.0)

        if input_audio.ndim == 2:
            return out.reshape(1, -1)
        return out

    def set_gate_threshold(self, value: float) -> None:
        self.gate.set_threshold(value)

    def set_drive(self, value: float) -> None:
        self.distortion.set_drive(value)

    def set_tone(self, value: float) -> None:
        self.tone.set_tone(value)

    def set_volume(self, value: float) -> None:
        if value <= 0.01:
            self.gain_db = -100.0
        else:
            self.gain_db = 20 * np.log10(value)
        self._gain_linear = 10 ** (self.gain_db / 20.0)
