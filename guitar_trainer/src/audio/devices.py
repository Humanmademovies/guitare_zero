import sounddevice as sd

def list_input_devices() -> list[dict]:
    """Retourne la liste des périphériques d'entrée (micros)."""
    devices = []
    try:
        all_devices = sd.query_devices()
        for i, dev in enumerate(all_devices):
            if dev['max_input_channels'] > 0:
                devices.append({
                    "index": i,
                    "name": dev['name'],
                    "channels": dev['max_input_channels'],
                    "samplerate": dev['default_samplerate']
                })
    except Exception as e:
        print(f"[AUDIO ERROR] Listing input devices: {e}")
    return devices

def list_output_devices() -> list[dict]:
    """Retourne la liste des périphériques de sortie (Enceintes/Casque)."""
    devices = []
    try:
        all_devices = sd.query_devices()
        for i, dev in enumerate(all_devices):
            if dev['max_output_channels'] > 0:
                devices.append({
                    "index": i,
                    "name": dev['name'],
                    "channels": dev['max_output_channels'],
                    "samplerate": dev['default_samplerate']
                })
    except Exception as e:
        print(f"[AUDIO ERROR] Listing output devices: {e}")
    return devices

def resolve_device_index(device_id: str | int | None, kind='input') -> int | None:
    """
    Convertit un identifiant en index.
    kind: 'input' ou 'output' pour chercher dans la bonne liste.
    """
    if device_id is None:
        return None

    if isinstance(device_id, int):
        return device_id

    # Recherche par nom
    search_name = str(device_id).lower()
    # On récupère la bonne liste
    devices = list_input_devices() if kind == 'input' else list_output_devices()
    
    for dev in devices:
        if search_name in dev['name'].lower():
            return dev['index']
    
    print(f"[AUDIO WARNING] {kind.capitalize()} Device '{device_id}' non trouvé.")
    return None