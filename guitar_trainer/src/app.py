import sys
from .core.config import load_config, validate_config
from .core.state import AppState
from .audio.stream import AudioStream
from .audio.devices import list_input_devices # Nouvel import
from .core.controller import AppController
from .ui.pygame_app import PygameApp
from .ui.screens.tuner_screen import TunerScreen

def main() -> int:
    print("--------------------------------------------------")
    print("Guitar Trainer MVP - Initialization")
    print("--------------------------------------------------")

    try:
        # 1. Configuration
        cfg = load_config()
        validate_config(cfg)
        print("[INIT] Config loaded.")

        # --- DIAGNOSTIC AUDIO ---
        print("\n--- Available Input Devices ---")
        devices = list_input_devices()
        for dev in devices:
            print(f"Index {dev['index']}: {dev['name']} (Channels: {dev['channels']}, SR: {dev['samplerate']})")
        print("-------------------------------\n")
        # ------------------------

        # 2. État Global (Shared State)
        state = AppState()
        print("[INIT] State initialized.")

        # 3. Audio (Entrée micro)
        audio = AudioStream(cfg)
        print("[INIT] Audio stream created.")

        # 4. Contrôleur (Orchestrateur)
        controller = AppController(cfg, state, audio)
        print("[INIT] Controller ready.")

        # 5. UI (Moteur graphique)
        app = PygameApp(cfg, state, controller)
        print("[INIT] UI Engine created.")

        # 6. Création de l'écran principal (Tuner)
        tuner_screen = TunerScreen(cfg, state, controller)
        
        # 7. Lancement
        app.set_screen(tuner_screen)
        print("[INIT] Starting Main Loop...")
        app.run()

    except KeyboardInterrupt:
        print("\n[STOP] User interrupted.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0