class Screen:
    """
    Classe de base pour tous les écrans de l'application.
    Définit les méthodes que chaque écran doit implémenter.
    """
    def __init__(self, cfg, state, controller):
        self.cfg = cfg
        self.state = state
        self.controller = controller

    def on_enter(self) -> None:
        """Appelé quand l'écran devient actif."""
        pass

    def on_exit(self) -> None:
        """Appelé quand on quitte cet écran."""
        pass

    def handle_event(self, event) -> None:
        """Gère un événement Pygame (clavier, souris)."""
        pass

    def update(self, dt: float) -> None:
        """
        Mise à jour logique (animations, timers).
        dt = temps écoulé depuis la dernière frame en secondes.
        """
        pass

    def draw(self, surface) -> None:
        """Dessine l'écran sur la surface principale."""
        pass