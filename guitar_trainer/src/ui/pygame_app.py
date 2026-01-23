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
        
        pygame.init()
        pygame.font.init()
        
        self.screen_surface = pygame.display.set_mode(
            self.cfg.window_size, 
            pygame.DOUBLEBUF
        )
        pygame.display.set_caption(self.cfg.window_title)
        
        self.clock = pygame.time.Clock()
        self.running = False
        
        # --- SYSTÈME DE NAVIGATION ---
        self.screens: dict[str, Screen] = {}
        self.current_screen: Screen | None = None

    def register_screen(self, name: str, screen: Screen) -> None:
        """Enregistre un écran et lui donne accès à l'app."""
        screen.set_app(self)
        self.screens[name] = screen

    def change_screen(self, name: str) -> None:
        """Transition vers un autre écran."""
        if name not in self.screens:
            print(f"[UI ERROR] Screen '{name}' not found.")
            return

        # 1. Quitter l'ancien
        if self.current_screen:
            self.current_screen.on_exit()
        
        # 2. Changer
        self.current_screen = self.screens[name]
        print(f"[UI] Navigating to '{name}'")
        
        # 3. Entrer dans le nouveau
        if self.current_screen:
            self.current_screen.on_enter()

    def run(self) -> None:
        """Lance la boucle principale."""
        self.running = True
        self.controller.start_audio()
        
        while self.running:
            dt = self.clock.tick(self.cfg.fps) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()

        self.controller.stop_audio()
        pygame.quit()
        sys.exit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.current_screen:
                self.current_screen.handle_event(event)

    def _update(self, dt: float) -> None:

        self.controller.update(dt)
        if self.current_screen:
            self.current_screen.update(dt)

    def _draw(self) -> None:
        self.screen_surface.fill((10, 10, 10))
        if self.current_screen:
            self.current_screen.draw(self.screen_surface)
        pygame.display.flip()