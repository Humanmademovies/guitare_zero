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