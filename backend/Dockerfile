# Utiliser une version de Python légère mais compatible
FROM python:3.12-slim-bookworm

# Définir le dossier de travail racine
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libglib2.0-0 \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Structure des dossiers ---
COPY . ./backend

# On ajoute /app au PYTHONPATH
ENV PYTHONPATH=/app

# Création du dossier pour les uploads partagés
RUN mkdir -p /app/storage/sgf_files /app/storage/videos /app/storage/thumbnails 

# Exposer le port de l'API
EXPOSE 8000

# Lancement de l'application
CMD ["python", "main.py"]