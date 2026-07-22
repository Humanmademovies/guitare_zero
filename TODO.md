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
| README + TODO + bandeau d'état dans Archi.md | (ce commit) |

## Restant

| # | Action | U | S | Notes |
|---|--------|---|---|-------|
| 7 | Gain d'entrée / rattrapage logiciel | 3 | 4 | Guitare **passive** : niveau bas structurel, un boost configurable vaut mieux que de courir après les seuils |
| 9 | Config persistante (YAML/JSON) | 3 | 3 | Prévu dès la spec d'origine ; mémoriser aussi le dernier périphérique valide et la taille de fenêtre |
| 10 | Remplacer le DSP pur Python de `processor.py` | 3 | 3 | Boucles par échantillon dans le callback audio (gate/tone/réverbe) ; pedalboard est dans `environment.yml` mais n'est plus utilisé |
| 11 | Phase B d'Archi.md : `PreviewPlayer` + bouton « Écouter la quête » | 2 | 2 | Les 60 samples de `data/samples/` existent (Phase A faite), rien ne les exploite |
| 12 | Trancher : consolider Pygame vs web app auto-hébergée (nerdodrome) | 2 | 2 | Electron écarté (aucun gain audio vs navigateur) ; décider avant d'investir dans le point 11 |
| 13 | Accords et mélodies (nouveaux types de quêtes) | 2 | 1 | Annoncés dans l'intro d'Archi.md, inexistants ; une seule campagne (`debutant.json`) |
| 14 | Pipeline Custom Tracks (Demucs + Basic Pitch + Mapper) | 1 | 1 | Plan détaillé en fin d'Archi.md ; outil externe hors-ligne, indépendant de la techno du jeu |

## Micro-fixes en passant

- `guitar_trainer/run.sh` cherche `environment.yml` à côté de lui (il est à la racine) : `-f ../environment.yml`.
- `sudo alsactl store` sur pop-os pour pérenniser le volume ALSA de la carte USB.
- `state.set_error` est branché, mais les erreurs de `resolve_device_index` (warning console) pourraient l'utiliser aussi.
