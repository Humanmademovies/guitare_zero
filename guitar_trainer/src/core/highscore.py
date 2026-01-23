import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List

SCORE_FILE = "highscores.json"

@dataclass
class ScoreEntry:
    score: int
    date: str
    difficulty: str # Ex: "x2.5"

class HighScoreManager:
    def __init__(self):
        self.scores: List[ScoreEntry] = []
        self.load_scores()

    def load_scores(self):
        if not os.path.exists(SCORE_FILE):
            self.scores = []
            return

        try:
            with open(SCORE_FILE, 'r') as f:
                data = json.load(f)
                self.scores = [ScoreEntry(**item) for item in data]
        except (json.JSONDecodeError, TypeError):
            print("[HIGHSCORE] Erreur de lecture, fichier corrompu. Reset.")
            self.scores = []

    def save_scores(self):
        # Convertir les objets en dict pour le JSON
        data = [asdict(s) for s in self.scores]
        with open(SCORE_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def add_score(self, score: int, multiplier: float):
        if score <= 0: return

        # Création de la date lisible (24/01 14:30)
        now = datetime.now().strftime("%d/%m %H:%M")
        
        entry = ScoreEntry(
            score=score,
            date=now,
            difficulty=f"x{multiplier}"
        )
        
        self.scores.append(entry)
        
        # 1. Trier par score décroissant (Le plus grand en haut)
        self.scores.sort(key=lambda x: x.score, reverse=True)
        
        # 2. Garder les 10 premiers
        self.scores = self.scores[:10]
        
        # 3. Sauvegarder
        self.save_scores()
        print(f"[HIGHSCORE] Score sauvegardé: {score}")

    def get_top_scores(self):
        return self.scores