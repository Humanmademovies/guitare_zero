# Guitar Zero

Entraîneur de guitare : détection de pitch en temps réel (aubio), accordeur, mode arcade,
campagne à quêtes et studio d'échantillonnage. Python + Pygame + sounddevice.

## Matériel

Pensé pour une **guitare passive** branchée via un câble-interface USB (carte ALSA
« USB Audio », chipset TTGK). Le niveau d'entrée est faible par nature (RMS ≈ 0,01–0,02
en jeu, bruit de fond ≈ 0,0006) : les seuils par défaut de `src/core/config.py`
(`rms_threshold = 0.003`, `gate_threshold = 0.05`) sont calibrés pour ce matériel,
et un **gain d'entrée logiciel** (`input_gain`, défaut 2×, potard GAIN de l'accordeur,
1× à 8×) amplifie le signal avant l'analyse et le monitoring.

## Installation & lancement

```bash
conda env create -f environment.yml   # crée l'env "guitar_env" (depuis la racine du dépôt)
cd guitar_trainer
conda activate guitar_env
python -m src
```

Note : `guitar_trainer/run.sh` automatise ces étapes mais cherche `environment.yml`
à côté de lui alors qu'il est à la racine — voir TODO.md.

## Touches

| Contexte | Touches |
|---|---|
| Partout | `ESPACE` start/stop audio · `Échap` retour |
| Accordeur & jeu | `←`/`→` change l'entrée audio · `↑`/`↓` change la sortie |
| Accordeur | potards à la souris (glisser vertical) : GAIN, GATE, PURE, DRIVE, TONE, VOL |
| Studio | `G`/`D` case · `H`/`B` corde · `N` prochain vide · `R` refaire · `ESPACE` écouter |
| Menus | souris (clic + molette) |

Les périphériques actifs sont affichés en bas à droite (`In (L/R)` / `Out (U/D)`).

## Fenêtre

L'UI dessine en résolution logique 1600×1200, mise à l'échelle automatiquement.
La fenêtre est redimensionnable librement (bandes noires si le ratio diffère).

## Configuration persistante

Les réglages (gain, seuils, périphériques, fenêtre) sont sauvegardés dans
`guitar_trainer/config.json` (non versionné, propre à chaque machine) : à la fermeture
du jeu, en sortant de l'accordeur et après chaque changement de périphérique réussi.
Les périphériques y sont mémorisés **par nom** (sans le suffixe `hw:x,y`), car les
index ALSA changent d'un reboot à l'autre. Supprimer le fichier restaure les défauts.

## Dépannage

- **Bandeau rouge en haut** : l'ouverture du flux audio a échoué ; le message donne la
  cause et le jeu revient automatiquement au périphérique précédent.
- **Bandeau jaune « AUDIO ARRÊTÉ »** : flux coupé volontairement — `ESPACE` pour relancer.
- **Aucune détection** : vérifier l'entrée sélectionnée, monter le knob GAIN, puis
  baisser le knob GATE (= `rms_threshold`, le trait sur le VU-mètre MIC montre le
  seuil courant).
- **Son de sortie très faible** : le volume ALSA de la carte USB retombe parfois à ~49 %
  (−30 dB). Le remonter : `amixer -c 1 sset PCM 100%` (pérenniser : `sudo alsactl store`).
- **Craquements / décrochages** : des lignes `[AUDIO] Stream status: ...` en console
  comptent les xruns. Les effets de monitoring tournent en C++ (pedalboard), leur coût
  est négligeable — chercher plutôt côté périphérique ou charge machine.

## Documentation

- `Archi.md` — proposition d'architecture d'origine + chantiers « prochaines features »
  (Mode Studio/Preview, Custom Tracks), avec bandeau d'état en tête.
- `TODO.md` — plan d'action courant (fait / restant, gradé urgence × simplicité).
