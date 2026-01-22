FROM python:3.10-slim

# 1. Installation des dépendances système
# On garde pkg-config et les libs audio
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libasound2-dev \
    portaudio19-dev \
    libsdl2-2.0-0 \
    pkg-config \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Dossier de travail
WORKDIR /app

# 3. Installation des dépendances Python (Séquencée)

# A. On met à jour pip
RUN pip install --upgrade pip

# B. On installe Numpy en premier (Version < 2.0 pour compatibilité)
RUN pip install "numpy<2"

# C. LE FIX : On installe Aubio avec une "désactivation de sécurité" pour le compilateur
# CFLAGS="..." : Dit à GCC d'ignorer les erreurs de type de pointeur (le bug de 2019)
# --no-build-isolation : Force Aubio à utiliser le Numpy qu'on vient d'installer juste au-dessus
RUN CFLAGS="-Wno-error=incompatible-pointer-types" \
    pip install --no-cache-dir --no-build-isolation aubio

# D. On installe le reste
RUN pip install --no-cache-dir pygame sounddevice

# 4. Commande de lancement
CMD ["python", "-m", "src"]