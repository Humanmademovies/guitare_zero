import sys
import os

# Permet d'exécuter le package directement
if __name__ == "__main__":
    try:
        from .app import main
        main()
    except ImportError:
        # Fallback si exécuté de manière incorrecte
        from app import main
        main()