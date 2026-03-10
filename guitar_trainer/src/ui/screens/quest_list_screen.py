import pygame
from .base import Screen
from ..widgets.text import TextLabel
from ...core.scoring import get_tier_info

class QuestListScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.08), bold=True)
        self.font_item = pygame.font.SysFont("monospace", int(H * 0.035))
        self.font_tier = pygame.font.SysFont("monospace", int(H * 0.025), bold=True)
        self.font_hint = pygame.font.SysFont("monospace", int(H * 0.02))

        self.lbl_title = TextLabel(self.font_title, (W // 2, int(H * 0.1)), align="center")
        self.quest_items = []
        self.selected_idx = 0
        self.scroll_offset = 0

        self.list_top = int(H * 0.22)
        self.list_bottom = int(H * 0.92)
        self.item_height = int(H * 0.09)
        self.item_margin = int(H * 0.01)
        self.item_total_h = self.item_height + self.item_margin
        self.max_visible = (self.list_bottom - self.list_top) // self.item_total_h

    def on_enter(self):
        W, H = self.cfg.window_size
        manager = self.controller.campaign_manager
        camp_id = self.state.selected_campaign_id
        campaign = manager.get_campaign(camp_id)

        self.lbl_title.set_text(campaign["name"].upper(), (0, 255, 255))
        self.quest_items = []

        for q in campaign.get("quests", []):
            unlocked = manager.is_unlocked(camp_id, q["id"])
            score = manager.get_quest_score(camp_id, q["id"])
            tier_name, tier_color = get_tier_info(score)

            display_name = q["name"] if unlocked else "??? (Verrouillé)"
            color = (255, 255, 255) if unlocked else (80, 80, 80)

            name_surf = self.font_item.render(display_name, True, color)
            tier_surf = None
            if unlocked and tier_name:
                tier_surf = self.font_tier.render(tier_name, True, tier_color)

            self.quest_items.append({
                "name_surf": name_surf,
                "tier_surf": tier_surf,
                "id": q["id"],
                "unlocked": unlocked
            })

        last_unlocked = 0
        for i, item in enumerate(self.quest_items):
            if item["unlocked"]:
                last_unlocked = i
        self.selected_idx = last_unlocked
        self.scroll_offset = 0
        self._clamp_scroll()

    def _clamp_scroll(self):
        if self.selected_idx < self.scroll_offset:
            self.scroll_offset = self.selected_idx
        if self.selected_idx >= self.scroll_offset + self.max_visible:
            self.scroll_offset = self.selected_idx - self.max_visible + 1
        max_scroll = max(0, len(self.quest_items) - self.max_visible)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def _move_cursor(self, direction):
        if not self.quest_items:
            return
        self.selected_idx = (self.selected_idx + direction) % len(self.quest_items)
        self._clamp_scroll()

    def _launch_selected(self):
        if not self.quest_items:
            return
        item = self.quest_items[self.selected_idx]
        if not item["unlocked"]:
            return

        self.state.selected_quest_id = item["id"]
        q_data = self.controller.campaign_manager.get_quest(
            self.state.selected_campaign_id,
            item["id"]
        )

        if q_data["type"] == "tuner":
            self.app.change_screen("tuner")
        else:
            self.controller.game_engine.load_quest(
                self.state.selected_campaign_id,
                q_data
            )
            self.app.change_screen("game")

    def _idx_from_mouse(self, pos):
        mx, my = pos
        W = self.cfg.window_size[0]
        item_x = int(W * 0.1)
        item_w = int(W * 0.8)

        for i in range(self.max_visible):
            abs_idx = self.scroll_offset + i
            if abs_idx >= len(self.quest_items):
                break
            y = self.list_top + i * self.item_total_h
            rect = pygame.Rect(item_x, y, item_w, self.item_height)
            if rect.collidepoint(pos):
                return abs_idx
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.change_screen("campaign_menu")
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
                self._clamp_scroll()
                self._launch_selected()

        elif event.type == pygame.MOUSEMOTION:
            idx = self._idx_from_mouse(event.pos)
            if idx is not None:
                self.selected_idx = idx
                self._clamp_scroll()

    def draw(self, surface):
        surface.fill((15, 20, 30))
        self.lbl_title.draw(surface)

        W, H = self.cfg.window_size
        item_x = int(W * 0.1)
        item_w = int(W * 0.8)

        for i in range(self.max_visible):
            abs_idx = self.scroll_offset + i
            if abs_idx >= len(self.quest_items):
                break

            item = self.quest_items[abs_idx]
            y = self.list_top + i * self.item_total_h
            rect = pygame.Rect(item_x, y, item_w, self.item_height)

            is_selected = (abs_idx == self.selected_idx)

            if not item["unlocked"]:
                bg = (25, 25, 30)
                border_color = (40, 40, 50)
            elif is_selected:
                bg = (50, 65, 90)
                border_color = (0, 255, 255)
            else:
                bg = (35, 40, 55)
                border_color = (60, 70, 90)

            pygame.draw.rect(surface, bg, rect, border_radius=8)
            border_w = 3 if is_selected else 1
            pygame.draw.rect(surface, border_color, rect, border_w, border_radius=8)

            surface.blit(item["name_surf"], (rect.x + 20, rect.centery - item["name_surf"].get_height() // 2))

            if item["tier_surf"]:
                x_tier = rect.right - item["tier_surf"].get_width() - 20
                surface.blit(item["tier_surf"], (x_tier, rect.centery - item["tier_surf"].get_height() // 2))

        total = len(self.quest_items)
        if total > self.max_visible:
            track_x = item_x + item_w + 10
            track_y = self.list_top
            track_h = self.max_visible * self.item_total_h
            track_w = 6

            pygame.draw.rect(surface, (40, 40, 50), (track_x, track_y, track_w, track_h), border_radius=3)

            thumb_h = max(20, int(track_h * (self.max_visible / total)))
            thumb_y = track_y + int((track_h - thumb_h) * (self.scroll_offset / max(1, total - self.max_visible)))
            pygame.draw.rect(surface, (0, 200, 200), (track_x, thumb_y, track_w, thumb_h), border_radius=3)

        hint = self.font_hint.render("Haut/Bas : naviguer  |  Entrée : lancer  |  Echap : retour", True, (80, 80, 80))
        surface.blit(hint, (W // 2 - hint.get_width() // 2, int(H * 0.95)))
