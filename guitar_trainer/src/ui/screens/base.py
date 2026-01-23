class Screen:
    """
    Classe de base pour tous les écrans de l'application.
    """
    def __init__(self, cfg, state, controller):
        self.cfg = cfg
        self.state = state
        self.controller = controller
        self.app = None  # Référence vers PygameApp pour la navigation

    def set_app(self, app) -> None:
        """Permet à l'écran de piloter la navigation."""
        self.app = app

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_event(self, event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        pass