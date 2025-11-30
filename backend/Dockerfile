# Utiliser une version de Python légère mais compatible
FROM python:3.10-slim

# Définir le dossier de travail racine
WORKDIR /app

# Installation des dépendances système
# - gcc, libpq-dev : Nécessaires pour compiler psycopg2 (driver PostgreSQL)
# - libgl1..., libglib... : Nécessaires si vous utilisez OpenCV dans le backend
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CRUCIAL : Structure des dossiers ---
# On copie tout le contenu du dossier 'backend' local VERS '/app/backend' dans le conteneur.
# Cela permet aux imports Python de type "from backend.api import..." de fonctionner.
COPY . ./backend

# On ajoute /app au PYTHONPATH pour que Python trouve le package 'backend'
ENV PYTHONPATH=/app

# Création du dossier pour les uploads partagés
RUN mkdir -p /app/uploads

# Exposer le port de l'API
EXPOSE 8000

# Lancement de l'application
# Notez la syntaxe "backend.main:app" qui correspond à la structure de dossier
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]