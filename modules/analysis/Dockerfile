# Utiliser une image qui supporte OpenCV et les dépendances IA
FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système pour OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copie des dépendances Python
COPY requirements.txt .

# On installe pybind11 (dépendance de build/runtime requise par 'sente')
# Puis on installe toutes les autres dépendances du fichier
RUN pip install --no-cache-dir pybind11 meson ninja && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création du dossier uploads
RUN mkdir -p /app/uploads

# Lancement du service
CMD ["python", "video_processor.py"]