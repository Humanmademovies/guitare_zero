#!/bin/bash

# Nom de l'environnement défini dans environment.yml
ENV_NAME="guitar_env"

# 1. Se placer dans le dossier du script (racine du projet)
# Cela garantit que python trouve le module 'src' même si le script est lancé depuis ailleurs
cd "$(dirname "$0")"

# Vérifie si conda est disponible
if ! command -v conda &> /dev/null; then
    echo "Conda n'est pas détecté. Assurez-vous d'avoir Anaconda ou Miniconda installé."
    exit 1
fi

# Initialisation shell pour conda
eval "$(conda shell.bash hook)"

# Vérifie si l'env existe, sinon le crée
if ! conda info --envs | grep -q "$ENV_NAME"; then
    echo "Environnement '$ENV_NAME' non trouvé. Création en cours..."
    conda env create -f environment.yml
else
    # Optionnel : Mettre à jour l'env si environment.yml a changé (commenté pour l'instant)
    conda env update -f environment.yml --prune
    echo "Environnement '$ENV_NAME' détecté."
fi

# Active l'environnement
conda activate $ENV_NAME

# Lance le module src
echo "Lancement de Guitar Trainer..."
# export PYTHONPATH=$PYTHONPATH:$(pwd) # Sécurité supplémentaire si besoin
python -m src