# Choix de la version stable : Python 3.12 sur Debian 12 (Bookworm)
FROM python:3.12-slim-bookworm

WORKDIR /app

# 1. Installation des dépendances système
# - build-essential & git : pour cloner et compiler sente
# - libgl1 & libglib2.0-0 : pour OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Installation des outils de build Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel pybind11 meson ninja

# 3. INSTALLATION MANUELLE DE SENTE (Avec Patchs)
# On clone, on patch, on installe, puis on nettoie.
RUN git clone https://github.com/atw1020/sente.git sente-src && \
    cd sente-src && \
    # PATCH A: Modification de setup.py (remplacer '>=3.8.*' par '>=3.8')
    sed -i 's/python_requires=">=3.8.*"/python_requires=">=3.8"/' setup.py && \
    # PATCH B: Ajout de #include <algorithm> dans Tree.h et SGFNode.cpp
    # On insère la ligne au tout début du fichier (ligne 1)
    sed -i '1i #include <algorithm>' src/Utils/Tree.h && \
    sed -i '1i #include <algorithm>' src/Utils/SGF/SGFNode.cpp && \
    # Installation
    pip install . && \
    # Nettoyage
    cd .. && \
    rm -rf sente-src

# 4. Installation des autres dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Configuration finale
COPY . .
ENV PYTHONPATH=/app

# Création des dossiers nécessaires
RUN mkdir -p /app/uploads/videos 

# Lancement du service
CMD ["python", "main.py"]