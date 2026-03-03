import pygame
from .base import Screen
from ..widgets.text import TextLabel

class CampaignMenuScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.08), bold=True)
        self.font_item = pygame.font.SysFont("monospace", int(H * 0.05))
        
        self.lbl_title = TextLabel(self.font_title, (W//2, int(H * 0.1)), align="center")
        self.lbl_title.set_text("CHOIX DE LA CAMPAGNE", (0, 255, 255))
        
        self.campaign_rects = []
        self._build_list()

    def _build_list(self):
        W, H = self.cfg.window_size
        manager = self.controller.campaign_manager
        y_offset = int(H * 0.25)
        
        for camp_id, camp_data in manager.campaigns.items():
            rect = pygame.Rect(W * 0.2, y_offset, W * 0.6, H * 0.1)
            label = TextLabel(self.font_item, rect.center, align="center")
            label.set_text(camp_data["name"], (255, 255, 255))
            self.campaign_rects.append({"rect": rect, "label": label, "id": camp_id})
            y_offset += int(H * 0.15)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.change_screen("menu")
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for item in self.campaign_rects:
                if item["rect"].collidepoint(event.pos):
                    self.state.selected_campaign_id = item["id"]
                    self.app.change_screen("quest_list")

    def draw(self, surface):
        surface.fill((20, 25, 35))
        self.lbl_title.draw(surface)
        
        for item in self.campaign_rects:
            color = (50, 60, 80)
            if item["rect"].collidepoint(pygame.mouse.get_pos()):
                color = (70, 90, 120)
            pygame.draw.rect(surface, color, item["rect"], border_radius=10)
            pygame.draw.rect(surface, (0, 255, 255), item["rect"], 2, border_radius=10)
            item["label"].draw(surface)
