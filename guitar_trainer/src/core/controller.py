import queue
from .config import AppConfig
from .state import AppState
from ..audio.stream import AudioStream
from ..analysis.features import FeatureExtractor

class AppController:
    def __init__(self, cfg: AppConfig, state: AppState, audio: AudioStream):
        self.cfg = cfg
        self.state = state
        self.audio = audio
        
        # Le contrôleur possède sa propre instance d'extracteur
        # car c'est lui qui effectue le travail de calcul
        self.extractor = FeatureExtractor(cfg)

    def start_audio(self) -> None:
        """Démarre le flux audio."""
        self.audio.start()
        self.state.set_audio_running(True)

    def stop_audio(self) -> None:
        """Arrête le flux audio."""
        self.audio.stop()
        self.state.set_audio_running(False)

    def toggle_audio(self) -> None:
        if self.audio.is_running():
            self.stop_audio()
        else:
            self.start_audio()

    def update(self) -> None:
        """
        À appeler à chaque frame de la boucle principale (UI).
        Consomme les données audio en attente et met à jour l'état.
        """
        audio_queue = self.audio.get_queue()
        
        # On traite TOUS les blocs en attente pour ne pas prendre de retard (drain queue)
        # Mais on ne met à jour l'état global qu'avec le dernier résultat pertinent
        # pour éviter de faire clignoter l'UI inutilement.
        last_features = None
        
        try:
            # On boucle tant qu'il y a des données
            while True:
                block = audio_queue.get_nowait()
                
                # C'est ici que la magie de l'analyse opère
                features = self.extractor.process(block)
                last_features = features
                
        except queue.Empty:
            # Plus rien à traiter pour l'instant
            pass

        # Si on a calculé de nouvelles features, on met à jour l'état partagé
        if last_features is not None:
            self.state.update_features(last_features)
    
    def cycle_input_device(self, direction: int) -> None:
        """Change le périphérique d'entrée et s'adapte à son Sample Rate natif."""
        devices = self.state.get_input_devices()
        if not devices:
            return

        # 1. Identifier l'index actuel
        current_idx = 0
        current_id = self.cfg.device_name_or_index
        
        for i, dev in enumerate(devices):
            if dev['index'] == current_id or dev['name'] == current_id:
                current_idx = i
                break
        
        # 2. Calculer le nouveau
        new_idx = (current_idx + direction) % len(devices)
        new_dev = devices[new_idx]
        
        # 3. Arrêt Audio
        was_running = self.audio.is_running()
        if was_running:
            self.stop_audio()
            
        # 4. Mise à jour Config (ID + Sample Rate)
        self.cfg.device_name_or_index = new_dev['index']
        
        # AJOUT : Adaptation automatique au taux d'échantillonnage du device
        new_sr = int(new_dev['samplerate'])
        if new_sr > 0 and new_sr != self.cfg.sample_rate:
            print(f"[CONTROLLER] Auto-adjusting Sample Rate: {self.cfg.sample_rate} -> {new_sr} Hz")
            self.cfg.sample_rate = new_sr
            # CRUCIAL : On doit recréer l'extracteur car Aubio est configuré à l'init avec le SR
            self.extractor = FeatureExtractor(self.cfg)
        
        print(f"[CONTROLLER] Switching input to: {new_dev['name']} (Index {new_dev['index']}, SR={new_sr})")
        
        # 5. Redémarrage
        if was_running:
            self.start_audio()
    
