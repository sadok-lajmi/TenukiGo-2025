# 1. Utiliser une image Node.js officielle légère (Alpine)
FROM node:18-alpine

# 2. Définir le dossier de travail dans le conteneur
WORKDIR /app

# 3. Copier les fichiers de définition des dépendances
# On le fait avant de copier le reste du code pour profiter du cache Docker
COPY package.json package-lock.json* ./

# 4. Installer les dépendances
# L'option --legacy-peer-deps peut aider si vous avez des conflits de versions
RUN npm install

# 5. Copier le reste du code source du frontend
COPY . .

# 6. Exposer le port sur lequel Next.js tourne par défaut
EXPOSE 3000

# 7. Commande de démarrage pour le développement
# Cela lance le serveur Next.js en mode dev avec hot-reloading
CMD ["npm", "run", "dev"]