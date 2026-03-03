import pygame
from .base import Screen
from ..widgets.text import TextLabel

class QuestListScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.08), bold=True)
        self.font_item = pygame.font.SysFont("monospace", int(H * 0.04))
        self.lbl_title = TextLabel(self.font_title, (W//2, int(H * 0.1)), align="center")
        self.quest_items = []

    def on_enter(self):
        """Chargement dynamique des quêtes de la campagne sélectionnée."""
        W, H = self.cfg.window_size
        manager = self.controller.campaign_manager
        camp_id = self.state.selected_campaign_id
        campaign = manager.get_campaign(camp_id)
        
        self.lbl_title.set_text(campaign["name"].upper(), (0, 255, 255))
        self.quest_items = []
        
        y_offset = int(H * 0.25)
        for q in campaign.get("quests", []):
            unlocked = manager.is_unlocked(camp_id, q["id"])
            rect = pygame.Rect(W * 0.2, y_offset, W * 0.6, H * 0.08)
            label = TextLabel(self.font_item, rect.center, align="center")
            text = q["name"] if unlocked else "??? (Verrouillé)"
            color = (255, 255, 255) if unlocked else (100, 100, 100)
            label.set_text(text, color)
            
            self.quest_items.append({"rect": rect, "label": label, "id": q["id"], "unlocked": unlocked})
            y_offset += int(H * 0.12)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.change_screen("campaign_menu")
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for item in self.quest_items:
                if item["rect"].collidepoint(event.pos) and item["unlocked"]:
                    self.state.selected_quest_id = item["id"]
                    quest = self.controller.campaign_manager.get_quest(
                        self.state.selected_campaign_id, item["id"]
                    )
                    if quest["type"] == "tuner":
                        self.app.change_screen("tuner")
                    elif quest["type"] == "rhythm":
                        # Sera implémenté à l'étape suivante
                        print("Mode Rythme bientôt disponible")

    def draw(self, surface):
        surface.fill((20, 25, 35))
        self.lbl_title.draw(surface)
        for item in self.quest_items:
            bg = (40, 50, 70) if item["unlocked"] else (30, 30, 35)
            if item["unlocked"] and item["rect"].collidepoint(pygame.mouse.get_pos()):
                bg = (60, 80, 110)
            pygame.draw.rect(surface, bg, item["rect"], border_radius=8)
            border = (0, 255, 255) if item["unlocked"] else (60, 60, 60)
            pygame.draw.rect(surface, border, item["rect"], 2, border_radius=8)
            item["label"].draw(surface)
