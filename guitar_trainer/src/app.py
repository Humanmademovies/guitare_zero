import sys
from .core.config import load_config, validate_config
from .core.state import AppState
from .audio.stream import AudioStream
from .audio.devices import list_input_devices, list_output_devices
from .core.controller import AppController
from .ui.pygame_app import PygameApp
from .ui.screens.tuner_screen import TunerScreen

def main() -> int:
    print("--------------------------------------------------")
    print("Guitar Trainer MVP - Initialization")
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
        # On stocke les inputs et outputs pour le switch dynamique
        state.set_input_devices(list_input_devices())
        state.set_output_devices(list_output_devices())
        
        print("[INIT] State initialized.")
        
        audio = AudioStream(cfg)
        print("[INIT] Audio stream created.")

        controller = AppController(cfg, state, audio)
        print("[INIT] Controller ready.")

        app = PygameApp(cfg, state, controller)
        print("[INIT] UI Engine created.")

        tuner_screen = TunerScreen(cfg, state, controller)
        
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