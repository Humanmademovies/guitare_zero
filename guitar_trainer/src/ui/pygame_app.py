import pygame
import sys
from ..core.config import AppConfig
from ..core.state import AppState
from ..core.controller import AppController
from .screens.base import Screen

class PygameApp:
    def __init__(self, cfg: AppConfig, state: AppState, controller: AppController):
        self.cfg = cfg
        self.state = state
        self.controller = controller
        
        # Initialisation Pygame
        pygame.init()
        pygame.font.init()
        
        self.screen_surface = pygame.display.set_mode(
            self.cfg.window_size, 
            pygame.DOUBLEBUF
        )
        pygame.display.set_caption(self.cfg.window_title)
        
        self.clock = pygame.time.Clock()
        self.running = False
        self.current_screen: Screen | None = None

    def set_screen(self, screen: Screen) -> None:
        """Change l'écran actif."""
        if self.current_screen:
            self.current_screen.on_exit()
        
        self.current_screen = screen
        
        if self.current_screen:
            self.current_screen.on_enter()

    def run(self) -> None:
        """Lance la boucle principale."""
        self.running = True
        
        # On s'assure que l'audio démarre
        self.controller.start_audio()
        
        while self.running:
            # dt = Delta Time en secondes (ex: 0.016 pour 60fps)
            dt = self.clock.tick(self.cfg.fps) / 1000.0
            
            self._handle_events()
            self._update(dt)
            self._draw()

        # Nettoyage à la sortie
        self.controller.stop_audio()
        pygame.quit()
        sys.exit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Passe l'événement à l'écran actif
            if self.current_screen:
                self.current_screen.handle_event(event)

    def _update(self, dt: float) -> None:
        # 1. Mise à jour du backend (Audio/Analyse)
        self.controller.update()
        
        # 2. Mise à jour de l'UI
        if self.current_screen:
            self.current_screen.update(dt)

    def _draw(self) -> None:
        # Fond noir par défaut
        self.screen_surface.fill((10, 10, 10))
        
        if self.current_screen:
            self.current_screen.draw(self.screen_surface)
            
        pygame.display.flip()