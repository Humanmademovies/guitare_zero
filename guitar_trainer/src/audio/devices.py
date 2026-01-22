import sounddevice as sd

def list_input_devices() -> list[dict]:
    """Retourne la liste des périphériques d'entrée (micros)."""
    devices = []
    try:
        # query_devices retourne une liste de dicts
        all_devices = sd.query_devices()
        # On itère pour filtrer les inputs (max_input_channels > 0)
        for i, dev in enumerate(all_devices):
            if dev['max_input_channels'] > 0:
                devices.append({
                    "index": i,
                    "name": dev['name'],
                    "channels": dev['max_input_channels'],
                    "samplerate": dev['default_samplerate']
                })
    except Exception as e:
        print(f"[AUDIO ERROR] Listing devices: {e}")
    return devices

def resolve_input_device(device_id: str | int | None) -> int | None:
    """
    Convertit un identifiant (nom partiel ou index) en index d'API audio.
    Si None, laisse le système choisir par défaut.
    """
    if device_id is None:
        return None

    if isinstance(device_id, int):
        return device_id

    # Si c'est une string, on cherche une correspondance dans les noms
    devices = list_input_devices()
    search_name = str(device_id).lower()
    
    for dev in devices:
        if search_name in dev['name'].lower():
            return dev['index']
    
    print(f"[AUDIO WARNING] Device '{device_id}' non trouvé, utilisation par défaut.")
    return None