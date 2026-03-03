import pygame
from .base import Screen
from ..widgets.text import TextLabel

class QuestResultScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.06), bold=True)
        self.font_tier = pygame.font.SysFont("monospace", int(H * 0.12), bold=True)
        self.font_btn = pygame.font.SysFont("monospace", int(H * 0.05))
        
        self.btn_next = pygame.Rect(W//2 - int(W*0.2), int(H * 0.7), int(W*0.4), int(H * 0.08))
        self.btn_retry = pygame.Rect(W//2 - int(W*0.2), int(H * 0.8), int(W*0.4), int(H * 0.08))

    def get_tier_info(self, pct):
        tiers = [
            (10, "Poopoo Tier", (139, 69, 19)),
            (20, "Casserole Tier", (169, 169, 169)),
            (30, "Fausse Note Tier", (255, 69, 0)),
            (40, "Apprenti Sourd Tier", (218, 165, 32)),
            (50, "Garage Band Tier", (70, 130, 180)),
            (60, "Ok Tier", (144, 238, 144)),
            (70, "Feu de Camp Tier", (255, 140, 0)),
            (80, "Local Hero Tier", (0, 191, 255)),
            (90, "Virtuose-ish Tier", (186, 85, 211)),
            (97.5, "Guitar Hero Tier", (255, 215, 0)),
            (99, "God Tier", (0, 255, 255)),
            (101, "Ultimate God Tier", (255, 255, 255))
        ]
        for threshold, name, color in tiers:
            if pct <= threshold: return name, color
        return tiers[-1][1], tiers[-1][2]

    def draw(self, surface):
        surface.fill((10, 15, 25))
        engine = self.controller.game_engine
        pct = engine.quest_percent
        tier_name, tier_color = self.get_tier_info(pct)
        
        # Affichage Score et Tier
        txt_pct = self.font_title.render(f"PRECISION : {pct:.1f}%", True, (200, 200, 200))
        surface.blit(txt_pct, (surface.get_width()//2 - txt_pct.get_width()//2, 100))
        
        txt_tier = self.font_tier.render(tier_name, True, tier_color)
        surface.blit(txt_tier, (surface.get_width()//2 - txt_tier.get_width()//2, 200))

        # Boutons
        for btn, label in [(self.btn_next, "CONTINUER"), (self.btn_retry, "REESSAYER")]:
            pygame.draw.rect(surface, (40, 50, 80), btn, border_radius=10)
            t = self.font_btn.render(label, True, (255, 255, 255))
            surface.blit(t, (btn.centerx - t.get_width()//2, btn.centery - t.get_height()//2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_next.collidepoint(event.pos):
                self.app.change_screen("quest_list")
            elif self.btn_retry.collidepoint(event.pos):
                q = self.controller.campaign_manager.get_quest(self.state.selected_campaign_id, self.state.selected_quest_id)
                self.controller.game_engine.load_quest(self.state.selected_campaign_id, q)
                self.app.change_screen("game")
