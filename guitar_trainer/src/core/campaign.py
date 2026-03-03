import json
import os

class CampaignManager:
    def __init__(self, campaigns_dir="data/campaigns", save_path="campaign_save.json"):
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.campaigns_dir = os.path.join(base_path, campaigns_dir)
        self.save_path = os.path.join(base_path, save_path)
        
        self.campaigns = {}
        self.unlocked_quests = {}
        
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
                    self.unlocked_quests = json.load(f)
            except Exception:
                pass
                
        # Assure que la première quête de chaque campagne est débloquée par défaut
        for camp_id, camp_data in self.campaigns.items():
            if camp_id not in self.unlocked_quests:
                first_quest = camp_data.get("quests", [])
                if first_quest:
                    self.unlocked_quests[camp_id] = [first_quest[0]["id"]]

    def save_progress(self):
        with open(self.save_path, "w", encoding="utf-8") as f:
            json.dump(self.unlocked_quests, f, indent=4)

    def unlock_quest(self, campaign_id, quest_id):
        if campaign_id in self.campaigns and quest_id:
            if campaign_id not in self.unlocked_quests:
                self.unlocked_quests[campaign_id] = []
            if quest_id not in self.unlocked_quests[campaign_id]:
                self.unlocked_quests[campaign_id].append(quest_id)
                self.save_progress()

    def is_unlocked(self, campaign_id, quest_id):
        return quest_id in self.unlocked_quests.get(campaign_id, [])

    def get_campaign(self, campaign_id):
        return self.campaigns.get(campaign_id)

    def get_quest(self, campaign_id, quest_id):
        campaign = self.get_campaign(campaign_id)
        if campaign:
            for q in campaign.get("quests", []):
                if q["id"] == quest_id:
                    return q
        return None
