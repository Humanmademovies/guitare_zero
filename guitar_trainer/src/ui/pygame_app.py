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

        # --- RÉSOLUTION LOGIQUE ---
        # Les écrans dessinent tous en cfg.window_size sur ce canvas,
        # qui est ensuite mis à l'échelle vers la fenêtre réelle à chaque frame.
        logical_w, logical_h = self.cfg.window_size

        # Fenêtre initiale : la plus grande taille au même ratio qui tient
        # sur le bureau (marges pour les barres et décorations du WM).
        try:
            desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
        except Exception:
            desktop_w, desktop_h = logical_w, logical_h
        avail_w, avail_h = desktop_w - 80, desktop_h - 120
        s = min(avail_w / logical_w, avail_h / logical_h, 1.0)
        win_size = (int(logical_w * s), int(logical_h * s))

        self.screen_surface = pygame.display.set_mode(
            win_size,
            pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        pygame.display.set_caption(self.cfg.window_title)

        self.canvas = pygame.Surface(self.cfg.window_size).convert()
        self._scaled = None

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

    def _view_params(self) -> tuple[float, int, int]:
        """Échelle et offsets (letterbox) du canvas logique dans la fenêtre réelle."""
        win_w, win_h = self.screen_surface.get_size()
        logical_w, logical_h = self.cfg.window_size
        s = min(win_w / logical_w, win_h / logical_h)
        ox = (win_w - int(logical_w * s)) // 2
        oy = (win_h - int(logical_h * s)) // 2
        return s, ox, oy

    def _map_event_to_canvas(self, event, s: float, ox: int, oy: int):
        """Convertit les coordonnées souris fenêtre réelle -> canvas logique."""
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            return event
        attrs = dict(event.__dict__)
        x, y = event.pos
        attrs["pos"] = (int((x - ox) / s), int((y - oy) / s))
        if event.type == pygame.MOUSEMOTION:
            rx, ry = event.rel
            attrs["rel"] = (int(round(rx / s)), int(round(ry / s)))
        return pygame.event.Event(event.type, attrs)

    def _handle_events(self) -> None:
        s, ox, oy = self._view_params()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.VIDEORESIZE:
                self.screen_surface = pygame.display.get_surface()
                continue

            event = self._map_event_to_canvas(event, s, ox, oy)
            if self.current_screen:
                self.current_screen.handle_event(event)

    def _update(self, dt: float) -> None:

        self.controller.update(dt)
        if self.current_screen:
            self.current_screen.update(dt)

    def _draw(self) -> None:
        self.canvas.fill((10, 10, 10))
        if self.current_screen:
            self.current_screen.draw(self.canvas)

        s, ox, oy = self._view_params()
        logical_w, logical_h = self.cfg.window_size
        target_size = (int(logical_w * s), int(logical_h * s))

        self.screen_surface.fill((0, 0, 0))
        if target_size == self.canvas.get_size():
            self.screen_surface.blit(self.canvas, (ox, oy))
        else:
            if self._scaled is None or self._scaled.get_size() != target_size:
                self._scaled = pygame.Surface(target_size).convert()
            pygame.transform.smoothscale(self.canvas, target_size, self._scaled)
            self.screen_surface.blit(self._scaled, (ox, oy))
        pygame.display.flip()
