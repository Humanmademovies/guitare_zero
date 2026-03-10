import json
import os

class CampaignManager:
    def __init__(self, campaigns_dir="data/campaigns", save_path="campaign_save.json"):
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.campaigns_dir = os.path.join(base_path, campaigns_dir)
        self.save_path = os.path.join(base_path, save_path)
        
        self.campaigns = {}
        self.progress = {} 
        
        self._load_campaigns()
        self._load_progress()

    def _load_campaigns(self):
        if not os.path.exists(self.campaigns_dir):
            os.makedirs(self.campaigns_dir, exist_ok=True)
            return
            
        for filename in os.listdir(self.campaigns_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.campaigns_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        camp_data = json.load(f)
                        if "id" in camp_data:
                            self.campaigns[camp_data["id"]] = camp_data
                except Exception as e:
                    print(f"Erreur de lecture de la campagne {filename} : {e}")

    def _load_progress(self):
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    # Sécurité : Si l'ancien format était une liste globale, on reset
                    if isinstance(raw_data, dict):
                        self.progress = raw_data
                    else:
                        self.progress = {}
            except Exception:
                self.progress = {}
        
        # Migration et Initialisation pour chaque campagne
        for camp_id, camp_data in self.campaigns.items():
            # Si la campagne n'existe pas dans le save
            if camp_id not in self.progress:
                first_q = camp_data.get("quests", [])[0]["id"] if camp_data.get("quests") else None
                self.progress[camp_id] = {
                    "unlocked": [first_q] if first_q else [],
                    "scores": {}
                }
            # Si la campagne existe mais est au vieux format (une liste au lieu d'un dict)
            elif isinstance(self.progress[camp_id], list):
                old_list = self.progress[camp_id]
                self.progress[camp_id] = {
                    "unlocked": old_list,
                    "scores": {}
                }

    def save_progress(self):
        with open(self.save_path, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=4)

    def unlock_quest(self, campaign_id, quest_id):
        if campaign_id in self.progress:
            if quest_id not in self.progress[campaign_id]["unlocked"]:
                self.progress[campaign_id]["unlocked"].append(quest_id)
                self.save_progress()

    def save_quest_score(self, campaign_id, quest_id, percent):
        if campaign_id in self.progress:
            # On s'assure que la structure des scores existe
            if "scores" not in self.progress[campaign_id]:
                self.progress[campaign_id]["scores"] = {}
                
            # On enregistre si c'est la première fois OU si le score est meilleur
            if quest_id not in self.progress[campaign_id]["scores"] or percent > self.progress[campaign_id]["scores"][quest_id]:
                self.progress[campaign_id]["scores"][quest_id] = percent
                self.save_progress()

    def get_quest_score(self, campaign_id, quest_id):
        camp_data = self.progress.get(campaign_id, {})
        if isinstance(camp_data, dict):
            return camp_data.get("scores", {}).get(quest_id, None)
        return None

    def is_unlocked(self, campaign_id, quest_id):
        camp_data = self.progress.get(campaign_id, {})
        if isinstance(camp_data, dict):
            return quest_id in camp_data.get("unlocked", [])
        return False

    def get_campaign(self, campaign_id):
        return self.campaigns.get(campaign_id)

    def get_quest(self, campaign_id, quest_id):
        campaign = self.get_campaign(campaign_id)
        if campaign:
            for q in campaign.get("quests", []):
                if q["id"] == quest_id:
                    return q
        return None
