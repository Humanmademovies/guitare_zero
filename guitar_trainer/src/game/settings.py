from dataclasses import dataclass, field
from typing import List

@dataclass
class GameSettings:
    # --- DIFFICULTÉ PHYSIQUE ---
    # Quelles cordes utiliser ?
    active_strings: List[int] = field(default_factory=lambda: [6, 5, 4]) 
    
    # Zone du manche
    min_fret: int = 0
    max_fret: int = 5
    
    # Vitesse de chute (Secondes)
    note_duration: float = 3.0  
    
    # Écart max (Cases)
    max_jump: int = 5 
    
    # --- RÈGLES DE LA PARTIE (NOUVEAU) ---
    total_notes: int = 20       # Longueur de la partie
    max_lives: int = 3          # Nombre de vies (0 = Mort subite ?)
    show_helper: bool = True    # Afficher "Corde X Case Y" (False = Mode Aveugle)
    
    def get_multiplier(self) -> float:
        """Calcule le multiplicateur de score basé sur la difficulté."""
        mult = 1.0
        
        # 1. Bonus Vitesse (Base 3.0s)
        # Ex: 1.5s -> x2.0
        mult *= (3.0 / max(0.5, self.note_duration))
        
        # 2. Bonus Cordes
        # Chaque corde supplémentaire ajoute 10%
        nb_strings = len(self.active_strings)
        mult *= (1.0 + (nb_strings - 1) * 0.1)
        
        # 3. Bonus Mode Aveugle (Gros bonus x1.5)
        if not self.show_helper:
            mult *= 1.5
            
        # 4. Bonus "Mort Subite" (1 Vie = x1.2)
        if self.max_lives == 1:
            mult *= 1.2
            
        return round(mult, 1)