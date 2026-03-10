import pygame
from .base import Screen
from ..widgets.text import TextLabel

class MenuScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)

        W, H = cfg.window_size
        CX = W // 2

        self.font_title = pygame.font.SysFont("monospace", int(H * 0.15), bold=True)
        self.font_btn = pygame.font.SysFont("monospace", int(H * 0.05))
        self.font_hint = pygame.font.SysFont("monospace", int(H * 0.02))

        self.lbl_title = TextLabel(self.font_title, (CX, int(H * 0.2)), align="center")
        self.lbl_title.set_text("GUITAR ZERO", (0, 255, 255))

        btn_w, btn_h = int(W * 0.3), int(H * 0.1)
        y_start = int(H * 0.4)
        spacing = int(H * 0.13)

        self.menu_items = [
            {"label": "L'ATELIER (Tuner)", "screen": "tuner", "color": (0, 255, 255)},
            {"label": "CAMPAGNE", "screen": "campaign_menu", "color": (0, 255, 255)},
            {"label": "ARCADE (Libre)", "screen": "setup", "color": (255, 200, 50)},
            {"label": "STUDIO (Samples)", "screen": "studio", "color": (200, 150, 255)},
        ]

        for i, item in enumerate(self.menu_items):
            item["rect"] = pygame.Rect(CX - btn_w // 2, y_start + i * spacing, btn_w, btn_h)

        self.selected_idx = 1

    def _move_cursor(self, direction):
        self.selected_idx = (self.selected_idx + direction) % len(self.menu_items)

    def _launch_selected(self):
        item = self.menu_items[self.selected_idx]
        self.app.change_screen(item["screen"])

    def _idx_from_mouse(self, pos):
        for i, item in enumerate(self.menu_items):
            if item["rect"].collidepoint(pos):
                return i
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._move_cursor(-1)
            elif event.key == pygame.K_DOWN:
                self._move_cursor(1)
            elif event.key == pygame.K_RETURN:
                self._launch_selected()

        elif event.type == pygame.MOUSEWHEEL:
            self._move_cursor(-event.y)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._idx_from_mouse(event.pos)
            if idx is not None:
                self.selected_idx = idx
                self._launch_selected()

        elif event.type == pygame.MOUSEMOTION:
            idx = self._idx_from_mouse(event.pos)
            if idx is not None:
                self.selected_idx = idx

    def draw(self, surface):
        W, H = self.cfg.window_size
        surface.fill((20, 20, 30))
        self.lbl_title.draw(surface)

        for i, item in enumerate(self.menu_items):
            rect = item["rect"]
            is_selected = (i == self.selected_idx)

            bg = (60, 60, 80) if is_selected else (30, 30, 40)
            border_color = item["color"] if is_selected else (60, 60, 70)
            border_w = 3 if is_selected else 1

            pygame.draw.rect(surface, bg, rect, border_radius=10)
            pygame.draw.rect(surface, border_color, rect, border_w, border_radius=10)

            text_color = (255, 255, 255) if is_selected else (150, 150, 150)
            txt = self.font_btn.render(item["label"], True, text_color)
            surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        hint = self.font_hint.render("Haut/Bas : naviguer  |  Entrée : choisir", True, (80, 80, 80))
        surface.blit(hint, (W // 2 - hint.get_width() // 2, int(H * 0.95)))
