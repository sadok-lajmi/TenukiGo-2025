# Utiliser une image qui supporte OpenCV et les dépendances IA
FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système pour OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copie des dépendances Python
COPY requirements.txt .

# On crée un fichier de requirements filtré SANS 'sente'
RUN grep -v '^sente' requirements.docker.txt > requirements.filtered.txt

# On installe pybind11 (dépendance de build/runtime requise par 'sente')
# Puis on installe toutes les autres dépendances du fichier filtré
RUN pip install --no-cache-dir pybind11 meson ninja && \
    pip install --no-cache-dir -r requirements.filtered.txt

# Patcher et installer 'sente' manuellement
RUN SENTE_SRC_DIR="/app/sente-src" && \
    echo "--- Cloning and patching 'sente' source... ---" && \
    git clone https://github.com/atw1020/sente.git "$SENTE_SRC_DIR" && \
    \
    echo "--- Patching files... ---" && \
    sed -i 's/">=3.8.*"/">=3.8"/' "$SENTE_SRC_DIR/setup.py" && \
    sed -i '1s;^;#include <algorithm>\n;' "$SENTE_SRC_DIR/src/Utils/Tree.h" && \
    sed -i '1s;^;#include <algorithm>\n;' "$SENTE_SRC_DIR/src/Utils/SGF/SGFNode.cpp" && \
    \
    echo "--- Installing 'sente' from patched source... ---" && \
    # On utilise --no-deps car on a déjà installé les dépendances (numpy, sgf) à l'étape 3
    pip install --no-cache-dir --no-deps "$SENTE_SRC_DIR" && \
    \
    echo "--- Cleaning up 'sente' source... ---" && \
    # On supprime le code source pour garder l'image légère
    rm -rf "$SENTE_SRC_DIR"

# Copie du code source
COPY . .

# Création du dossier uploads
RUN mkdir -p /app/uploads

# Lancement du service
CMD ["python", "video_processor.py"]