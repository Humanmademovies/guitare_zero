import queue
from .config import AppConfig
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
        self.audio.start()
        self.state.set_audio_running(True)

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
                self.studio_engine.update(last_features, dt)
    
    def cycle_input_device(self, direction: int) -> None:
        devices = self.state.get_input_devices()
        if not devices:
            return

        current_idx = 0
        current_id = self.cfg.device_name_or_index
        
        for i, dev in enumerate(devices):
            if dev['index'] == current_id or dev['name'] == current_id:
                current_idx = i
                break
        
        new_idx = (current_idx + direction) % len(devices)
        new_dev = devices[new_idx]
        
        was_running = self.audio.is_running()
        if was_running:
            self.stop_audio()
            
        self.cfg.device_name_or_index = new_dev['index']
        
        new_sr = int(new_dev['samplerate'])
        if new_sr > 0 and new_sr != self.cfg.sample_rate:
            print(f"[CONTROLLER] Auto-adjusting Sample Rate: {self.cfg.sample_rate} -> {new_sr} Hz")
            self.cfg.sample_rate = new_sr
            self.extractor = FeatureExtractor(self.cfg)
        
        self.state.reset_history()
        print(f"[CONTROLLER] Switching input to: {new_dev['name']} (Index {new_dev['index']}, SR={new_sr})")
        
        if was_running:
            self.start_audio()
    
    def cycle_output_device(self, direction: int) -> None:
        devices = self.state.get_output_devices()
        if not devices:
            return

        current_idx = 0
        current_id = self.cfg.output_device_name_or_index
        
        for i, dev in enumerate(devices):
            if dev['index'] == current_id or dev['name'] == current_id:
                current_idx = i
                break
        
        new_idx = (current_idx + direction) % len(devices)
        new_dev = devices[new_idx]
        
        was_running = self.audio.is_running()
        if was_running:
            self.stop_audio()
            
        self.cfg.output_device_name_or_index = new_dev['index']

        new_sr = int(new_dev['samplerate'])
        if new_sr > 0 and new_sr != self.cfg.sample_rate:
            print(f"[CONTROLLER] Auto-adjusting Sample Rate for OUTPUT: {self.cfg.sample_rate} -> {new_sr} Hz")
            self.cfg.sample_rate = new_sr
            self.extractor = FeatureExtractor(self.cfg)

        self.state.reset_history()
        print(f"[CONTROLLER] Switching OUTPUT to: {new_dev['name']} (Index {new_dev['index']})")
        
        if was_running:
            self.start_audio()

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
