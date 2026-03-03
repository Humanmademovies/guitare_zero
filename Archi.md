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

# prochaines features:

# 🎸 Plan d'Action : Le Mode Studio & Le Moteur de Rendu (Preview)

## 1. La Raison d'Être des Samples (Le "Pourquoi")

L'objectif est d'offrir un bouton **"Écouter la Quête"** avant de la jouer, pour que l'utilisateur puisse assimiler le rythme et la mélodie à l'oreille.

- **Le Réalisme Absolu :** En s'enregistrant soi-même, la "Preview" du jeu sonnera exactement avec le même grain, les mêmes micros et la même guitare que le joueur.
- **L'Évolutivité (Scalability pour les Accords) :** Un accord n'est qu'une superposition de notes. En possédant un sample propre pour chaque note individuelle (ex: Corde 6 Case 0, Corde 5 Case 2...), le moteur pourra générer n'importe quel accord complexe en les jouant avec un micro-décalage (strumming), sans avoir besoin d'enregistrer chaque accord manuellement.
- **La Personnalisation :** Si le joueur change de guitare (passe d'une acoustique à une électrique métal), il lui suffit de refaire une session "Studio" pour que le jeu s'adapte à son nouvel instrument.

------

## 2. Le Concept du "Mode Studio" (Le "Quoi")

C'est la gamification du fastidieux processus d'échantillonnage (sampling). Au lieu d'utiliser un logiciel de MAO (comme Audacity) pour enregistrer et découper 40 notes, on intègre un mini-jeu de précision dans *Guitar Zero*.

- L'interface demande une note spécifique (ex: "Joue la Corde 6 à vide").
- Le moteur attend que le joueur joue la note.
- Si la note est **juste** (cents proches de 0), **pure** (pas de bruit parasite) et **stable**, le jeu "capture" automatiquement les 3 secondes de résonance.
- Le jeu sauvegarde le fichier et passe automatiquement à la case suivante (Case 1, Case 2...).

------

## 3. Plan d'Implémentation Détaillé (Le "Comment")

Ce chantier se divise en deux grandes phases : l'Enregistrement (Le Studio) et la Lecture (Le Sampler).

### PHASE A : L'Enregistrement (Créer sa banque de sons)

1. **Création du `StudioScreen` (UI) :**
   - Cloner l'écran de l'accordeur (`TunerScreen`).
   - Ajouter une liste interne d'objectifs : de `(6, 0)` [Corde 6, Case 0] jusqu'à `(1, 4)` [Corde 1, Case 4].
   - Afficher au centre de l'écran la note à jouer avec une jauge de stabilité.
2. **Logique de Capture (Audio) :**
   - Dans la boucle d'update, vérifier les `Features` du micro : `f0`, `cents` et `is_pure`.
   - Si les conditions sont parfaites pendant `X` frames, déclencher l'état **"ENREGISTREMENT"**.
   - Empiler les tableaux `samples` générés par le processeur audio pendant 2 ou 3 secondes pour capter le *sustain* de la note.
3. **Sauvegarde sur le Disque (Export WAV) :**
   - Utiliser le module standard Python `wave` ou `scipy.io.wavfile` pour convertir le grand tableau de samples accumulés.
   - Sauvegarder dans un dossier : `data/samples/`.
   - **Convention de nommage stricte :** `string_fret.wav` (ex: `6_0.wav`, `5_3.wav`). C'est crucial pour que le moteur retrouve les sons sans réfléchir.

### PHASE B : Le Moteur de Rendu (Le "Sampler")

1. **Création de la classe `PreviewPlayer` :**
   - Une classe qui se charge au lancement du jeu et qui lit le dossier `data/samples/`.
   - Elle charge tous les fichiers `.wav` trouvés en mémoire (dans des objets `pygame.mixer.Sound` ou des tableaux Numpy) indexés par `(corde, case)`.
2. **Le Générateur de Piste :**
   - Une fonction qui prend en entrée la `sequence` d'une quête JSON (la liste des `beats`, `strings`, `frets`).
   - Elle convertit les `beats` en secondes réelles en utilisant le `tempo` de la quête.
   - Elle programme la lecture des sons correspondants aux timestamps exacts.
3. **Intégration UI (`QuestListScreen` / `GameSetupScreen`) :**
   - Ajouter un bouton "Écouter" (ou Play) à côté du nom de la quête.
   - Au clic, la piste générée est envoyée à la sortie audio (et pourquoi pas, passe à travers les effets de Distorsion/Reverb de ton `Pedalboard` pour un rendu épique).

------



# 🎸 Plan d'Action : Custom Tracks & Transcription Audio (Suno)

## 1. La Raison d'Être des Custom Tracks (Le "Pourquoi")

L'objectif est d'offrir une durée de vie infinie au jeu en permettant au joueur d'apprendre et de jouer par-dessus n'importe quelle chanson (générée par Suno ou issue de sa bibliothèque MP3).

- **L'Apprentissage Réel :** Sortir des exercices répétitifs pour apprendre à jouer de vrais morceaux, avec le vrai son d'un groupe en fond sonore (batterie, basse, chant).
- **Automatisation du Contenu :** Créer un niveau de jeu de rythme à la main (en tapant le JSON note par note) est un travail titanesque. L'automatisation permet de générer des centaines de quêtes instantanément.
- **Séparation des Préoccupations :** Conserver un moteur de jeu (`engine.py`) extrêmement léger et rapide, en déplaçant toute la charge de calcul lourde (IA, analyse spectrale) vers un outil externe exécuté avant de jouer.

------

## 2. Le Concept du "Pré-Processeur" (Le "Quoi")

Transformer une musique brute en niveau de jeu est un défi d'ambiguïté (où placer ses doigts pour une même note ?). La solution est un pipeline **hors-ligne** (un script indépendant du jeu) divisé en 3 étapes :

1. Séparer les instruments (Stems).
2. Extraire la partition de la guitare (Audio vers MIDI).
3. Placer intelligemment les doigts sur le manche (MIDI vers JSON).

------

## 4. Plan d'Implémentation Détaillé (Le "Comment")

Ce chantier se divise en trois grandes phases. Les phases A et B constituent un utilitaire externe, la phase C est une mise à jour mineure du moteur de jeu.

### PHASE A : L'Extraction et l'Analyse (Les IAs)

1. **La Séparation des Pistes (Stems) :**
   - Utiliser une IA de *Source Separation* (comme Demucs ou Spleeter de Deezer) sur le morceau généré par Suno.
   - Objectif : Obtenir deux fichiers. Un `backing_track.wav` (Tout sauf la guitare) et un `guitar_stem.wav` (Guitare isolée).
2. **La Transcription Audio vers MIDI (AMT) :**
   - Faire passer le `guitar_stem.wav` dans un modèle open-source de transcription (comme **Basic Pitch** par Spotify).
   - L'IA écoute la piste de guitare et génère un fichier `guitar_track.mid`. Ce fichier contient le rythme parfait et la hauteur des notes, mais pas le doigté (corde/case).

### PHASE B : Le Convertisseur Python (Le "Mapper")

C'est le script "Magique" que tu devras coder pour relier l'IA à ton jeu.

1. **Lecture du Fichier MIDI :**
   - Utiliser une bibliothèque Python (comme `mido` ou `pretty_midi`) pour lire les notes et leurs timestamps (en secondes).
   - Calculer le `beat` de chaque note en fonction du BPM de la chanson.
2. **L'Heuristique de Placement (Le chemin le plus court) :**
   - Pour chaque note lue (ex: E4), le script interroge le `GUITAR_MAP` de ton jeu pour trouver toutes les positions possibles (ex: Corde 1 Case 0, Corde 2 Case 5, etc.).
   - **L'Algorithme :** Le script retient la position *la plus proche* de la note précédente. Si la note précédente était jouée Corde 3 Case 7, l'algorithme privilégiera une nouvelle note Corde 2 Case 5 plutôt qu'une corde à vide pour éviter que le joueur ne fasse des bonds impossibles sur le manche.
3. **L'Export au format Quête :**
   - Le script génère la structure `json` attendue par le jeu, en y insérant la liste des notes calculées.
   - Il crée un dossier pour la chanson contenant : `level.json` et `backing_track.wav`.

### PHASE C : L'Intégration In-Game (Dans le Moteur)

1. **Mise à jour de `engine.py` (`load_quest`) :**
   - Ajouter une vérification : si la quête contient une clé `"audio_track": "backing_track.wav"`, le moteur charge ce fichier audio.
   - Lancer la lecture (`pygame.mixer.music.play()`) au moment exact où les notes commencent à descendre.
2. **La Synchronisation :**
   - L'avancement des notes ne sera plus purement calculé sur le `dt` (delta time) théorique, mais idéalement asservi à la position de lecture du fichier audio (`pygame.mixer.music.get_pos()`) pour s'assurer qu'aucun décalage ne se crée si le jeu subit un ralentissement (lag).