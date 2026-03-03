import pygame
from .base import Screen
from ..widgets.text import TextLabel

class QuestListScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.font_title = pygame.font.SysFont("monospace", int(H * 0.08), bold=True)
        self.font_item = pygame.font.SysFont("monospace", int(H * 0.035))
        self.font_tier = pygame.font.SysFont("monospace", int(H * 0.025), bold=True)
        
        self.lbl_title = TextLabel(self.font_title, (W//2, int(H * 0.1)), align="center")
        self.quest_items = []

    def get_tier_info(self, pct):
        if pct is None: return None, None
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

    def on_enter(self):
        W, H = self.cfg.window_size
        manager = self.controller.campaign_manager
        camp_id = self.state.selected_campaign_id
        campaign = manager.get_campaign(camp_id)
        
        self.lbl_title.set_text(campaign["name"].upper(), (0, 255, 255))
        self.quest_items = []
        
        y_offset = int(H * 0.25)
        for q in campaign.get("quests", []):
            unlocked = manager.is_unlocked(camp_id, q["id"])
            score = manager.get_quest_score(camp_id, q["id"])
            tier_name, tier_color = self.get_tier_info(score)
            
            rect = pygame.Rect(W * 0.1, y_offset, W * 0.8, H * 0.08)
            
            # Nom de la quête
            display_name = q["name"] if unlocked else "??? (Verrouillé)"
            color = (255, 255, 255) if unlocked else (80, 80, 80)
            
            # Création des textes
            label_name = self.font_item.render(display_name, True, color)
            label_tier = None
            if unlocked and tier_name:
                label_tier = self.font_tier.render(tier_name, True, tier_color)
            
            self.quest_items.append({
                "rect": rect, 
                "name_surf": label_name,
                "tier_surf": label_tier,
                "id": q["id"], 
                "unlocked": unlocked
            })
            y_offset += int(H * 0.1)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.change_screen("campaign_menu")
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for item in self.quest_items:
                if item["rect"].collidepoint(event.pos) and item["unlocked"]:
                    # Enregistrement de la quête sélectionnée dans le state
                    self.state.selected_quest_id = item["id"]
                    
                    # Récupération des données de la quête
                    q_data = self.controller.campaign_manager.get_quest(
                        self.state.selected_campaign_id, 
                        item["id"]
                    )
                    
                    # ROUTAGE : On vérifie le type de quête
                    if q_data["type"] == "tuner":
                        # Si c'est un accordage, on va sur l'écran Tuner
                        self.app.change_screen("tuner")
                    else:
                        # Sinon, on charge le moteur rythmique et on va au jeu
                        self.controller.game_engine.load_quest(
                            self.state.selected_campaign_id, 
                            q_data
                        )
                        self.app.change_screen("game")

    def draw(self, surface):
        surface.fill((15, 20, 30))
        self.lbl_title.draw(surface)
        
        for item in self.quest_items:
            bg = (40, 45, 60) if item["unlocked"] else (25, 25, 30)
            if item["unlocked"] and item["rect"].collidepoint(pygame.mouse.get_pos()):
                bg = (60, 70, 90)
                
            pygame.draw.rect(surface, bg, item["rect"], border_radius=10)
            
            # Dessin du nom (à gauche)
            surface.blit(item["name_surf"], (item["rect"].x + 20, item["rect"].centery - item["name_surf"].get_height()//2))
            
            # Dessin du Tier (à droite)
            if item["tier_surf"]:
                x_tier = item["rect"].right - item["tier_surf"].get_width() - 20
                surface.blit(item["tier_surf"], (x_tier, item["rect"].centery - item["tier_surf"].get_height()//2))
