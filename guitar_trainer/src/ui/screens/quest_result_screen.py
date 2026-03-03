import pygame
from .base import Screen
from ..widgets.text import TextLabel

class QuestResultScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.1), bold=True)
        self.font_btn = pygame.font.SysFont("monospace", int(H * 0.05))
        self.lbl_title = TextLabel(self.font_title, (W//2, H//3), align="center")
        btn_w, btn_h = int(W * 0.4), int(H * 0.08)
        self.btn_next = pygame.Rect(W//2 - btn_w//2, int(H * 0.55), btn_w, btn_h)
        self.btn_retry = pygame.Rect(W//2 - btn_w//2, int(H * 0.65), btn_w, btn_h)
        self.btn_menu = pygame.Rect(W//2 - btn_w//2, int(H * 0.75), btn_w, btn_h)

    def on_enter(self):
        self.lbl_title.set_text("QUÊTE RÉUSSIE !", (0, 255, 100))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_next.collidepoint(event.pos):
                self.app.change_screen("quest_list")
            elif self.btn_retry.collidepoint(event.pos):
                q = self.controller.campaign_manager.get_quest(self.state.selected_campaign_id, self.state.selected_quest_id)
                self.app.change_screen("tuner" if q["type"] == "tuner" else "game")
            elif self.btn_menu.collidepoint(event.pos):
                self.app.change_screen("quest_list")

    def draw(self, surface):
        surface.fill((10, 20, 10))
        self.lbl_title.draw(surface)
        for rect, label in [(self.btn_next, "CONTINUER"), (self.btn_retry, "REESSAYER"), (self.btn_menu, "RETOUR LISTE")]:
            pygame.draw.rect(surface, (30, 50, 30), rect, border_radius=10)
            pygame.draw.rect(surface, (0, 255, 100), rect, 2, border_radius=10)
            txt = self.font_btn.render(label, True, (255, 255, 255))
            surface.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
