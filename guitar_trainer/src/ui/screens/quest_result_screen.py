import pygame
from .base import Screen
from ..widgets.text import TextLabel
from ...core.scoring import get_tier_info

class QuestResultScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.06), bold=True)
        self.font_tier = pygame.font.SysFont("monospace", int(H * 0.12), bold=True)
        self.font_btn = pygame.font.SysFont("monospace", int(H * 0.05))
        self.font_hint = pygame.font.SysFont("monospace", int(H * 0.02))

        btn_w = int(W * 0.4)
        btn_h = int(H * 0.08)
        cx = W // 2

        self.buttons = [
            {"label": "CONTINUER", "rect": pygame.Rect(cx - btn_w // 2, int(H * 0.7), btn_w, btn_h), "action": "continue"},
            {"label": "REESSAYER", "rect": pygame.Rect(cx - btn_w // 2, int(H * 0.8), btn_w, btn_h), "action": "retry"},
        ]

        self.selected_idx = 0

    def on_enter(self):
        engine = self.controller.game_engine
        pct = engine.quest_percent

        quest_data = self.controller.campaign_manager.get_quest(
            self.state.selected_campaign_id,
            self.state.selected_quest_id
        )
        min_percent = 0
        if quest_data:
            min_percent = quest_data.get("params", {}).get("requirements", {}).get("min_percent", 0)

        if pct >= min_percent:
            self.selected_idx = 0
        else:
            self.selected_idx = 1

    def _move_cursor(self, direction):
        self.selected_idx = (self.selected_idx + direction) % len(self.buttons)

    def _launch_selected(self):
        action = self.buttons[self.selected_idx]["action"]
        if action == "continue":
            self.app.change_screen("quest_list")
        elif action == "retry":
            q = self.controller.campaign_manager.get_quest(
                self.state.selected_campaign_id,
                self.state.selected_quest_id
            )
            self.controller.game_engine.load_quest(self.state.selected_campaign_id, q)
            self.app.change_screen("game")

    def _idx_from_mouse(self, pos):
        for i, btn in enumerate(self.buttons):
            if btn["rect"].collidepoint(pos):
                return i
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.change_screen("quest_list")
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
        surface.fill((10, 15, 25))

        engine = self.controller.game_engine
        pct = engine.quest_percent
        tier_name, tier_color = get_tier_info(pct)

        txt_pct = self.font_title.render(f"PRECISION : {pct:.1f}%", True, (200, 200, 200))
        surface.blit(txt_pct, (W // 2 - txt_pct.get_width() // 2, 100))

        if tier_name:
            txt_tier = self.font_tier.render(tier_name, True, tier_color)
            surface.blit(txt_tier, (W // 2 - txt_tier.get_width() // 2, 200))

        for i, btn in enumerate(self.buttons):
            rect = btn["rect"]
            is_selected = (i == self.selected_idx)

            bg = (60, 70, 100) if is_selected else (40, 50, 80)
            border_color = (0, 255, 255) if is_selected else (60, 70, 90)
            border_w = 3 if is_selected else 1

            pygame.draw.rect(surface, bg, rect, border_radius=10)
            pygame.draw.rect(surface, border_color, rect, border_w, border_radius=10)

            text_color = (255, 255, 255) if is_selected else (150, 150, 150)
            txt = self.font_btn.render(btn["label"], True, text_color)
            surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        hint = self.font_hint.render("Haut/Bas : naviguer  |  Entrée : choisir  |  Echap : retour", True, (80, 80, 80))
        surface.blit(hint, (W // 2 - hint.get_width() // 2, int(H * 0.95)))
