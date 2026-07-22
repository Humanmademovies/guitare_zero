import sys
import os

# Sur Linux, exposer au PortAudio embarqué par conda les périphériques de
# routage du serveur audio (pipewire/pulse/default) : sans cela, seules les
# cartes ALSA brutes sont visibles, et la sortie jack de la carte intégrée —
# tenue par PipeWire pour le bureau — n'apparaît jamais dans la liste.
# À faire AVANT tout import de sounddevice. setdefault : un réglage manuel
# de l'utilisateur garde la priorité.
if sys.platform.startswith("linux"):
    if os.path.exists("/usr/share/alsa/alsa.conf"):
        os.environ.setdefault("ALSA_CONFIG_PATH", "/usr/share/alsa/alsa.conf")
    _plugin_dir = "/usr/lib/x86_64-linux-gnu/alsa-lib"
    if os.path.isdir(_plugin_dir):
        os.environ.setdefault("ALSA_PLUGIN_DIR", _plugin_dir)

# Permet d'exécuter le package directement
if __name__ == "__main__":
    try:
        from .app import main
        main()
    except ImportError:
        # Fallback si exécuté de manière incorrecte
        from app import main
        main()
