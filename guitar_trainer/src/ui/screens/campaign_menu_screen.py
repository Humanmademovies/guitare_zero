import pygame
from .base import Screen
from ..widgets.text import TextLabel

class CampaignMenuScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.08), bold=True)
        self.font_item = pygame.font.SysFont("monospace", int(H * 0.05))
        self.font_hint = pygame.font.SysFont("monospace", int(H * 0.02))

        self.lbl_title = TextLabel(self.font_title, (W // 2, int(H * 0.1)), align="center")
        self.lbl_title.set_text("CHOIX DE LA CAMPAGNE", (0, 255, 255))

        self.campaign_items = []
        self.selected_idx = 0

    def on_enter(self):
        W, H = self.cfg.window_size
        manager = self.controller.campaign_manager

        self.campaign_items = []
        for camp_id, camp_data in manager.campaigns.items():
            self.campaign_items.append({
                "id": camp_id,
                "name": camp_data["name"]
            })

        self.selected_idx = 0
        current_id = self.state.selected_campaign_id
        if current_id:
            for i, item in enumerate(self.campaign_items):
                if item["id"] == current_id:
                    self.selected_idx = i
                    break

    def _move_cursor(self, direction):
        if not self.campaign_items:
            return
        self.selected_idx = (self.selected_idx + direction) % len(self.campaign_items)

    def _launch_selected(self):
        if not self.campaign_items:
            return
        item = self.campaign_items[self.selected_idx]
        self.state.selected_campaign_id = item["id"]
        self.app.change_screen("quest_list")

    def _idx_from_mouse(self, pos):
        W, H = self.cfg.window_size
        for i, item in enumerate(self.campaign_items):
            rect = self._get_item_rect(i)
            if rect.collidepoint(pos):
                return i
        return None

    def _get_item_rect(self, idx):
        W, H = self.cfg.window_size
        y_start = int(H * 0.25)
        item_h = int(H * 0.1)
        spacing = int(H * 0.13)
        return pygame.Rect(W * 0.2, y_start + idx * spacing, W * 0.6, item_h)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.change_screen("menu")
            elif event.key == pygame.K_UP:
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
        surface.fill((20, 25, 35))
        self.lbl_title.draw(surface)

        for i, item in enumerate(self.campaign_items):
            rect = self._get_item_rect(i)
            is_selected = (i == self.selected_idx)

            bg = (70, 90, 120) if is_selected else (50, 60, 80)
            border_color = (0, 255, 255) if is_selected else (80, 90, 110)
            border_w = 3 if is_selected else 1

            pygame.draw.rect(surface, bg, rect, border_radius=10)
            pygame.draw.rect(surface, border_color, rect, border_w, border_radius=10)

            text_color = (255, 255, 255) if is_selected else (180, 180, 180)
            txt = self.font_item.render(item["name"], True, text_color)
            surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        hint = self.font_hint.render("Haut/Bas : naviguer  |  Entrée : choisir  |  Echap : retour", True, (80, 80, 80))
        surface.blit(hint, (W // 2 - hint.get_width() // 2, int(H * 0.95)))
