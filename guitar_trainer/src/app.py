import sys
from .core.config import load_config, validate_config
from .core.state import AppState
from .audio.stream import AudioStream
from .audio.devices import list_input_devices, list_output_devices
from .core.controller import AppController
from .ui.pygame_app import PygameApp

# Import des écrans
from .ui.screens.tuner_screen import TunerScreen
from .ui.screens.menu_screen import MenuScreen
from .ui.screens.game_screen import GameScreen
from .ui.screens.game_setup_screen import GameSetupScreen

def main() -> int:
    print("--------------------------------------------------")
    print("Guitar Trainer - Initialization")
    print("--------------------------------------------------")

    try:
        cfg = load_config()
        validate_config(cfg)
        print("[INIT] Config loaded.")

        # --- DIAGNOSTIC AUDIO COMPLET ---
        print("\n--- INPUT Devices (Micros) ---")
        for dev in list_input_devices():
            print(f"Index {dev['index']}: {dev['name']} (Ch: {dev['channels']}, SR: {dev['samplerate']})")
            
        print("\n--- OUTPUT Devices (Speakers) ---")
        for dev in list_output_devices():
            print(f"Index {dev['index']}: {dev['name']} (Ch: {dev['channels']}, SR: {dev['samplerate']})")
        print("-------------------------------\n")

        state = AppState()
        state.set_input_devices(list_input_devices())
        state.set_output_devices(list_output_devices())
        
        print("[INIT] State initialized.")
        
        audio = AudioStream(cfg)
        print("[INIT] Audio stream created.")

        controller = AppController(cfg, state, audio)
        print("[INIT] Controller ready.")

        app = PygameApp(cfg, state, controller)
        print("[INIT] UI Engine created.")

        # --- CRÉATION DES ÉCRANS ---
        menu_screen = MenuScreen(cfg, state, controller)
        tuner_screen = TunerScreen(cfg, state, controller)
        game_screen = GameScreen(cfg, state, controller)
        setup_screen = GameSetupScreen(cfg, state, controller)
        
        # --- ENREGISTREMENT ---
        app.register_screen("menu", menu_screen)
        app.register_screen("tuner", tuner_screen)
        app.register_screen("game", game_screen)
        app.register_screen("setup", setup_screen)
        
        # --- DÉMARRAGE SUR LE MENU ---
        app.change_screen("menu")
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