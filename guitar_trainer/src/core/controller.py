import queue
from .config import AppConfig, save_config
from .state import AppState
from ..audio.stream import AudioStream
from ..analysis.features import FeatureExtractor
from .campaign import CampaignManager
from ..game.engine import GameEngine
from ..game.studio_engine import StudioEngine

class AppController:
    def __init__(self, cfg: AppConfig, state: AppState, audio: AudioStream):
        self.cfg = cfg
        self.state = state
        self.audio = audio
        self.extractor = FeatureExtractor(cfg)
        self.game_engine = GameEngine(cfg, controller=self)
        self.studio_engine = StudioEngine(cfg)
        self.campaign_manager = CampaignManager()	
        self.active_mode = "game" # 'game' ou 'studio'
	
    def start_audio(self) -> None:
        ok = self.audio.start()
        self.state.set_audio_running(ok)
        if ok:
            self.state.set_error(None)
        else:
            self.state.set_error(f"Audio KO : {self.audio.last_error or 'erreur inconnue'}")

    def stop_audio(self) -> None:
        self.audio.stop()
        self.state.set_audio_running(False)

    def toggle_audio(self) -> None:
        if self.audio.is_running():
            self.stop_audio()
        else:
            self.start_audio()

    def update(self, dt: float = 0.016) -> None:
        audio_queue = self.audio.get_queue()
        last_features = None
        

        try:
            while True:
                block = audio_queue.get_nowait()
                features = self.extractor.process(block)
                last_features = features
        except queue.Empty:
            pass

        if last_features is not None:
            self.state.update_features(last_features)

        if self.active_mode == "game":
            self.game_engine.update(last_features, dt)
        elif self.active_mode == "studio":
            if last_features is not None:
                self.studio_engine.update(last_features, dt)
    
    def cycle_input_device(self, direction: int) -> None:
        new_dev = self._next_device(self.state.get_input_devices(),
                                    self.cfg.device_name_or_index, direction)
        if new_dev is None:
            return
        print(f"[CONTROLLER] Switching input to: {new_dev['name']} (Index {new_dev['index']})")
        # On mémorise le NOM (sans suffixe hw:x,y) plutôt que l'index :
        # les index ALSA changent d'un reboot à l'autre, pas les noms.
        self._apply_device_change(f"entrée '{new_dev['name']}'",
                                  input_id=new_dev['name'].split(" (hw:")[0],
                                  samplerate=int(new_dev['samplerate']))

    def cycle_output_device(self, direction: int) -> None:
        new_dev = self._next_device(self.state.get_output_devices(),
                                    self.cfg.output_device_name_or_index, direction)
        if new_dev is None:
            return
        print(f"[CONTROLLER] Switching OUTPUT to: {new_dev['name']} (Index {new_dev['index']})")
        self._apply_device_change(f"sortie '{new_dev['name']}'",
                                  output_id=new_dev['name'].split(" (hw:")[0],
                                  samplerate=int(new_dev['samplerate']))

    def _next_device(self, devices: list[dict], current_id, direction: int) -> dict | None:
        if not devices:
            return None
        current_idx = 0
        for i, dev in enumerate(devices):
            if dev['index'] == current_id or (isinstance(current_id, str) and current_id in dev['name']):
                current_idx = i
                break
        return devices[(current_idx + direction) % len(devices)]

    _KEEP = object()

    def _apply_device_change(self, label: str, input_id=_KEEP, output_id=_KEEP,
                             samplerate: int | None = None) -> None:
        """Applique un changement de périphérique. Le flux est TOUJOURS redémarré ;
        si l'ouverture échoue, retour au périphérique précédent + erreur affichée."""
        prev = (self.cfg.device_name_or_index,
                self.cfg.output_device_name_or_index,
                self.cfg.sample_rate)

        self.stop_audio()
        if input_id is not AppController._KEEP:
            self.cfg.device_name_or_index = input_id
        if output_id is not AppController._KEEP:
            self.cfg.output_device_name_or_index = output_id
        if samplerate and samplerate > 0 and samplerate != self.cfg.sample_rate:
            print(f"[CONTROLLER] Auto-adjusting Sample Rate: {self.cfg.sample_rate} -> {samplerate} Hz")
            self.cfg.sample_rate = samplerate
            self.extractor = FeatureExtractor(self.cfg)
        self.state.reset_history()

        self.start_audio()
        if self.audio.is_running():
            save_config(self.cfg)
        else:
            cause = self.audio.last_error or "erreur inconnue"
            (self.cfg.device_name_or_index,
             self.cfg.output_device_name_or_index,
             self.cfg.sample_rate) = prev
            self.extractor = FeatureExtractor(self.cfg)
            self.state.reset_history()
            self.start_audio()
            self.state.set_error(f"Échec {label} ({cause}) — retour au périphérique précédent")

    def set_audio_input_gain(self, value: float) -> None:
        self.cfg.input_gain = value
        self.audio.set_input_gain(value)

    def save_config(self) -> None:
        save_config(self.cfg)

    def set_audio_gate(self, value: float) -> None:
        self.audio.set_gate_threshold(value)

    def set_audio_drive(self, value: float) -> None:
        self.audio.set_drive(value)

    def set_audio_volume(self, value: float) -> None:
        self.audio.set_volume(value)
    
    def set_audio_tone(self, value: float) -> None:
        self.audio.set_tone(value)
    
    def set_active_mode(self, mode: str) -> None:
        """Permet à l'UI de router les features vers le bon moteur ('game' ou 'studio')."""
        self.active_mode = mode
        print(f"[CONTROLLER] Mode set to: {self.active_mode}")
    
    def play_sample(self, samples) -> None:
        self.audio.play_sample(samples)
