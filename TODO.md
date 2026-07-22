# TODO — plan d'action

Plan établi à la reprise du 2026-07-22, gradé **U** = urgence (1→5) et **S** = simplicité
(1 = complexe → 5 = trivial), trié du plus simple/urgent au plus complexe/moins urgent.

## Fait (2026-07-22)

| Action | Commits |
|---|---|
| Volume ALSA sortie carte USB 49 % → 100 % (hors dépôt, à refaire si reboot) | — |
| Seuils adaptés au niveau réel d'une guitare passive (rms 0.003, gate 0.05) | `ea7c4ee` |
| UI indépendante de la résolution (canvas logique 1600×1200 + fenêtre redimensionnable) | `c5c2c95` |
| Chevauchements In/Out corrigés (colonne réservée accordeur, `ellipsize`, game screen) | `12ee8c5` |
| `.pyc` versionnés retirés du suivi | `77b4ed7` |
| Changement de périphérique robuste (redémarrage systématique + rollback) | `1bdecab` |
| Erreurs audio visibles à l'écran (bandeau branché sur `state.set_error`) | `1bdecab` |
| README + TODO + bandeau d'état dans Archi.md | `1d06bba` |
| Gain d'entrée logiciel (potard GAIN 1×–8×, défaut 2×, appliqué avant analyse et monitoring) | `62a2faa` |
| Config persistante `config.json` (fermeture, sortie accordeur, changement de périphérique) | `62a2faa` |
| Périphériques mémorisés par nom (les index ALSA changent au reboot) | `62a2faa` |
| DSP pedalboard (C++/JUCE) : ~0,03 ms/bloc contre ~8 ms en Python pur (×266) + log des xruns | `d2277d9` |
| Bloc 512 + fenêtre yin fixe 2048 (256 abandonné : xruns par contention GIL avec l'UI) | `d635ac7` |
| Spectrogramme vectorisé (20,9 → 1,25 ms/frame) — cause des dropouts du tuner | `1d164cf` |
| Écrêtage doux tanh en sortie (fini le clipping dur « pixélisé » ; `Limiter` pedalboard rejeté : maximiseur) | `a8aa8a0` |
| Métrologie hors-callback (le print dans le callback créait ses propres dropouts) | `a8aa8a0` |
| Routage PipeWire exposé : entrée+sortie « pipewire » = enceintes du bureau, 11,6 ms/côté | `a8aa8a0` |
| Calibration d'entrée documentée (volume guitare bas + GAIN logiciel — l'ADC du câble écrête à la source) | README |
| **Point 12 tranché : on reste sur Pygame.** L'UI est devenue résolution-indépendante, le DSP est en C++, et la qualité ampli (accès périphérique natif, PipeWire, 11,6 ms, gate anti-souffle) est impossible en navigateur ; la portabilité web était un faux besoin (on joue là où la guitare est branchée) | décision 2026-07-22 |
| Knobs synchronisés avec la config (drive/tone/volume persistés — le tone restait bloqué à 0,12 = 1,8 kHz à chaque démarrage !) + paramètres d'effets lissés à 10 Hz (fini le TONE qui « découpe » pendant le drag) | `713beb5` |
| `latency='high'` : dropouts éliminés durablement. Prouvé par bisection : même code = sessions propres OU injouables selon l'état machine au lancement ; `'low'` imposait ~2,7 ms d'échéances au graphe PipeWire. Tone défaut ramené à 0,12 (le 0,6 saturait l'étage de gain calibré à l'oreille) | `983bf75` |
| **Point 11 / Phase B d'Archi.md : `PreviewPlayer`** — touche P dans la liste des quêtes : séquence jouée avec les samples du Studio (strumming des accords, coupure par corde, pitch-shift 1 saut pour les 6 positions manquantes : cordes 1-2 cases 2-4) | `897840e` |

## Restant

| # | Action | U | S | Notes |
|---|--------|---|---|-------|
| 16 | IR de cabinet (`pedalboard.Convolution`) | 2 | 3 | Le signal est propre désormais : un IR de baffle (WAV libre, ~50 Ko) donnerait le rendu « ampli micro-capté » ; potard de mix éventuel |
| 13 | Accords et mélodies (nouveaux types de quêtes) | 2 | 1 | Annoncés dans l'intro d'Archi.md, inexistants ; une seule campagne (`debutant.json`) |
| 14 | Pipeline Custom Tracks (Demucs + Basic Pitch + Mapper) | 1 | 1 | Plan détaillé en fin d'Archi.md ; outil externe hors-ligne, indépendant de la techno du jeu |

## Micro-fixes en passant

- `guitar_trainer/run.sh` cherche `environment.yml` à côté de lui (il est à la racine) : `-f ../environment.yml`.
- `sudo alsactl store` sur pop-os pour pérenniser le volume ALSA de la carte USB.
- `state.set_error` est branché, mais les erreurs de `resolve_device_index` (warning console) pourraient l'utiliser aussi.
- Si des dropouts résiduels apparaissent : priorité temps réel du thread audio (rtkit / profil pro-audio PipeWire).
- `pop-upgrade` bloqué à 100 % CPU depuis des semaines (bug Pop!_OS) : `sudo systemctl restart pop-upgrade`.
- Latence configurable dans config.json (`high` robuste / `low` toucher) si la latence de monitoring devient gênante.
- Le graphe PipeWire tourne à 48 kHz, le jeu à 44,1 (rééchantillonnage permanent) : caler le jeu sur 48 kHz éviterait la conversion (attention aux 60 samples wav en 44,1).
- Matériel, un jour : interface avec vraie entrée Hi-Z (1 MΩ) — le câble TTGK reste le plafond de qualité de la chaîne.
- Enregistrer en mode Studio les 6 positions manquantes (cordes 1-2, cases 2-4) : les pitch-shifts de la preview s'effaceront automatiquement.
