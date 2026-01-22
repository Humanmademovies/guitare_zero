Voici une proposition d’architecture **MVP** (Linux), conçue pour rester **évolutive** (défis, progression, accords corde-par-corde, mélodies) tout en restant très simple au départ.

------

## Arborescence (projet minimal mais propre)

```
guitar_trainer/
  README.md
  environment.yml
  run.sh

  src/
    app.py

    core/
      config.py
      types.py
      state.py

    audio/
      devices.py
      stream.py

    analysis/
      pitch.py
      stability.py
      features.py

    ui/
      pygame_app.py
      screens/
        base.py
        tuner_screen.py
      widgets/
        vu_meter.py
        text.py
        status_light.py
```

Notes :

- `core/` contient le contrat de données et l’état global (stable dans le temps).
- `audio/` est uniquement l’entrée micro.
- `analysis/` est uniquement l’extraction de features (pitch, RMS, stabilité).
- `ui/` est uniquement l’affichage Pygame (et sera réutilisable pour les futurs modes “défis”).

------

## Détail fichier par fichier (classes / fonctions à écrire, sans code)

### `src/app.py`

**Rôle :** point d’entrée Python. Crée la config, initialise audio+analyse+UI, lance l’application.

- `def main() -> int`
  - Charge la config (valeurs par défaut + overrides éventuels).
  - Initialise `AppState`.
  - Crée `AudioStream` + `PitchAnalyzer`.
  - Crée `PygameApp` et lance la boucle principale.
  - Assure l’arrêt propre (stop stream, join threads).

------

## CORE

### `src/core/config.py`

**Rôle :** regrouper tous les paramètres réglables du MVP (et des versions futures), au même endroit.

- `@dataclass class AppConfig`
  - Audio : `sample_rate`, `block_size`, `channels`, `device_name_or_index`
  - Analyse : `fmin`, `fmax`, `confidence_threshold`, `rms_threshold`
  - Stabilité : `stable_window_ms`, `stable_cents_tolerance`, `stable_hold_ms`
  - UI : `fps`, `window_size`, `font_size`
- `def load_config() -> AppConfig`
  - Retourne une config avec des valeurs par défaut (évolutif vers fichier YAML plus tard).
- `def validate_config(cfg: AppConfig) -> None`
  - Vérifie des valeurs cohérentes (fmin < fmax, block_size > 0, etc.).

### `src/core/types.py`

**Rôle :** types et contrats partagés, pour éviter les dépendances circulaires.

- `@dataclass class AudioBlock`
  - `samples: np.ndarray` (mono float32)
  - `sample_rate: int`
  - `timestamp: float`
- `@dataclass class Features`
  - `timestamp: float`
  - `rms: float`
  - `f0_hz: float | None`
  - `note_name: str | None` (ex “A2”)
  - `cents: float | None` (écart à la note “la plus proche”)
  - `confidence: float`
  - `is_voiced: bool`
  - `stable: bool`
  - `stable_ms: float`
- `@dataclass class AppEvents`
  - Pour l’évolution (ex. `last_error: str | None`, `audio_running: bool`).

### `src/core/state.py`

**Rôle :** stockage thread-safe de l’état courant (features + statut), lisible par l’UI.

- `class AppState`
  - Attributs :
    - `current_features: Features`
    - `events: AppEvents`
  - `def update_features(self, f: Features) -> None`
    - Mise à jour atomique / thread-safe.
  - `def get_features_snapshot(self) -> Features`
    - Retourne une copie/snapshot pour l’UI.
  - `def set_audio_running(self, running: bool) -> None`
  - `def set_error(self, message: str | None) -> None`

------

## AUDIO

### `src/audio/devices.py`

**Rôle :** lister et choisir un périphérique micro (utile en Linux si plusieurs entrées).

- `def list_input_devices() -> list[dict]`
  - Retourne les périphériques d’entrée disponibles (nom, index, canaux).
- `def resolve_input_device(device_name_or_index: str | int | None) -> int | None`
  - Transforme un nom partiel ou index en index utilisable par le stream.

### `src/audio/stream.py`

**Rôle :** capture micro en flux, et fourniture des blocs audio au reste du système.

- `class AudioStream`
  - `__init__(self, cfg: AppConfig)`
  - `def start(self) -> None`
    - Ouvre le flux micro (callback).
  - `def stop(self) -> None`
    - Stoppe et libère.
  - `def is_running(self) -> bool`
  - `def get_queue(self) -> "queue.Queue[AudioBlock]"`
    - Queue alimentée par le callback.
  - `def get_last_rms(self) -> float`
    - Optionnel : utile pour VU-mètre même si pitch absent.
  - (privé) `def _callback(self, indata, frames, time_info, status) -> None`
    - Empile `AudioBlock` dans la queue (aucun calcul lourd).
  - (privé) `def _compute_rms(samples: np.ndarray) -> float`
    - RMS brut.

------

## ANALYSIS

### `src/analysis/pitch.py`

**Rôle :** extraire le pitch (f0) et une confiance.

- `class PitchTracker`
  - `__init__(self, cfg: AppConfig)`
  - `def process(self, block: AudioBlock) -> tuple[float | None, float]`
    - Retourne `(f0_hz, confidence)` ; `None` si non détecté.
  - `def reset(self) -> None`
  - (privé) `def _preprocess(self, samples: np.ndarray) -> np.ndarray`
    - Optionnel : normalisation, suppression DC, etc.

### `src/analysis/features.py`

**Rôle :** transformer audio+pitch en `Features` (note, cents, voiced).

- `def hz_to_note_name(f0_hz: float) -> str`
  - Convertit en note la plus proche (A4=440).
- `def hz_to_cents(f0_hz: float) -> float`
  - Écart en cents par rapport à la note la plus proche.
- `def is_voiced(rms: float, confidence: float, cfg: AppConfig) -> bool`
  - Applique les seuils.
- `class FeatureExtractor`
  - `__init__(self, cfg: AppConfig, pitch: PitchTracker, stability: "StabilityTracker")`
  - `def process(self, block: AudioBlock) -> Features`
    - Calcule RMS, pitch, note, cents, stabilité et renvoie `Features`.

### `src/analysis/stability.py`

**Rôle :** mesurer “tenue/stabilité” de la note (nécessaire pour les futurs défis).

- `class StabilityTracker`
  - `__init__(self, cfg: AppConfig)`
  - `def update(self, f0_hz: float | None, cents: float | None, voiced: bool, timestamp: float) -> tuple[bool, float]`
    - Retourne `(stable, stable_ms)` mis à jour.
  - `def reset(self) -> None`
  - (privé) `def _within_tolerance(self, cents: float) -> bool`
  - (privé) `def _advance_timer(self, timestamp: float, stable_now: bool) -> float`
    - Gère cumul, reset, hold.

------

## UI (Pygame)

### `src/ui/pygame_app.py`

**Rôle :** boucle Pygame, gestion des événements, navigation d’écrans.

- `class PygameApp`
  - `__init__(self, cfg: AppConfig, state: AppState, controller: "AppController")`
  - `def run(self) -> None`
    - Main loop (FPS fixe), événements, rendu.
  - `def set_screen(self, screen: "Screen") -> None`
  - (privé) `def _handle_events(self) -> None`
    - Quit, touches, etc.
  - (privé) `def _render(self) -> None`
  - (privé) `def _tick(self) -> None`

### `src/ui/screens/base.py`

**Rôle :** interface commune pour des écrans (menu, tuner, défis plus tard).

- `class Screen`
  - `def on_enter(self) -> None`
  - `def on_exit(self) -> None`
  - `def handle_event(self, event) -> None`
  - `def update(self, dt: float) -> None`
  - `def draw(self, surface) -> None`

### `src/ui/screens/tuner_screen.py`

**Rôle :** l’écran MVP : affiche note, Hz, RMS (VU), stabilité.

- `class TunerScreen(Screen)`
  - `__init__(self, cfg: AppConfig, state: AppState, controller: "AppController")`
  - `def handle_event(self, event) -> None`
    - Espace : start/stop audio, éventuellement “reset stabilité”.
  - `def update(self, dt: float) -> None`
    - Lit snapshot `Features`.
  - `def draw(self, surface) -> None`
    - Dessine VU-mètre, textes, voyant stable.

### `src/ui/widgets/vu_meter.py`

**Rôle :** widget VU-mètre simple (barre).

- `class VUMeter`
  - `__init__(self, rect, smoothing: float)`
  - `def set_value(self, rms: float) -> None`
  - `def draw(self, surface) -> None`

### `src/ui/widgets/text.py`

**Rôle :** rendu texte réutilisable.

- `class TextLabel`
  - `__init__(self, font, pos, align: str = "topleft")`
  - `def set_text(self, text: str) -> None`
  - `def draw(self, surface) -> None`

### `src/ui/widgets/status_light.py`

**Rôle :** voyant simple (stable/unstable, audio on/off).

- `class StatusLight`
  - `__init__(self, center, radius)`
  - `def set_on(self, on: bool) -> None`
  - `def draw(self, surface) -> None`

------

## Contrôle de l’application (important pour l’évolutivité)

### Nouveau fichier recommandé : `src/core/controller.py` (à ajouter)

**Rôle :** orchestrer start/stop et relier audio → analyse → state, sans le mettre dans l’UI.

- `class AppController`
  - `__init__(self, cfg: AppConfig, state: AppState, audio: AudioStream, extractor: FeatureExtractor)`
  - `def start_audio(self) -> None`
  - `def stop_audio(self) -> None`
  - `def toggle_audio(self) -> None`
  - `def update(self) -> None`
    - Appelée régulièrement depuis la boucle Pygame.
    - Vide la queue audio (ou traite N blocs) et met à jour `AppState`.
  - `def reset_trackers(self) -> None`
    - Réinitialise stabilité/pitch.

Pourquoi c’est crucial :

- Plus tard, le “controller” pourra aussi gérer les **modes de jeu** (défis), sans que l’UI ne devienne un monolithe.

------

## Fichiers “outillage”

### `run.sh`

**Rôle :** lanceur cliquable.

- Active conda env
- `python -m src.app` (ou équivalent)

### `environment.yml`

**Rôle :** environnement conda reproductible.

- Python
- pygame
- numpy
- sounddevice
- aubio

### `README.md`

**Rôle :** instructions d’installation + sélection du micro + touches.

------

## Pourquoi cette structure valide l’évolutivité

- Les futurs **défis** se branchent en ajoutant `game/` (ex. `exercise_base.py`, `hold_note.py`) qui consommera `Features` sans toucher à `audio/` et très peu à `ui/`.
- Les futurs **accords** (corde par corde) réutilisent pitch monophonique et ajoutent un `ChordExercise` au lieu de réécrire l’analyse.
- Les futures **mélodies** ajoutent un module `analysis/onset.py` + un exercice de séquence, sans casser le MVP.

Si vous voulez continuer immédiatement, l’étape suivante logique est : définir les valeurs par défaut de `AppConfig` pour guitare (fmin/fmax, block size, seuils) et la boucle de traitement (`AppController.update`) pour garantir une UI fluide.