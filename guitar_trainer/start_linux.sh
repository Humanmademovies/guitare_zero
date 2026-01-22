#!/bin/bash

# 1. Autorise Docker à afficher des fenêtres sur ton serveur graphique (X11)
xhost +local:docker

# 2. Lance l'application via Docker Compose
# --build : force la reconstruction si tu as changé le Dockerfile
echo "Lancement du conteneur..."
docker compose up --build

# (Optionnel) Nettoyage des permissions à la sortie
# xhost -local:docker