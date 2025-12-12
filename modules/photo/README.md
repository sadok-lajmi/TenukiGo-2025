# Module Photo - Tenuki25

Module d'analyse photo intégré avec pipeline complet : **Photo → Matrice de plateau → SGF**

## Fonctionnalités

### Analyse d'images brutes
- **Détection YOLO** : Reconnaissance automatique des plateaux de Go
- **Vision par ordinateur** : Extraction des positions des pierres
- **Transformation de perspective** : Correction automatique de l'angle de vue

### Complétion intelligente
- **Algorithme classique** : Complétion basée sur les règles du Go
- **IA hybride** : CNN + YOLO pour prédiction de coups avancée
- **Analyse de différences** : Détection des changements entre deux positions

### Génération SGF
- **Export direct** : Fichiers SGF compatibles avec tous les logiciels de Go
- **Métadonnées** : Informations de partie (joueurs, date, résultat, etc.)
- **Validation** : Vérification automatique du format SGF

## Architecture

```
modules/photo/
├── api.py              # API Flask avec endpoints étendus
├── service.py          # Services de complétion et analyse
├── image_processor.py  # Traitement d'images YOLO + OpenCV
├── sgf_generator.py    # Génération de fichiers SGF
├── model_loader.py     # Chargement des modèles IA
├── requirements.txt    # Dépendances mises à jour
└── README.md          # Cette documentation
```

## API Endpoints

### Nouveaux endpoints

#### **POST /photo/upload**
Upload et analyse d'une photo
```bash
curl -X POST -F "file=@image.jpg" http://localhost:5001/photo/upload
```

#### **POST /photo/process_two**
Traitement de deux photos avec génération SGF et sauvegarde automatique
```bash
curl -X POST \
  -F "file1=@image1.jpg" \
  -F "file2=@image2.jpg" \
  -F "use_ai=true" \
  -F 'metadata={"player_black":"Joueur 1","player_white":"Joueur 2"}' \
  http://localhost:5001/photo/process_two
```
**Retourne :**
```json
{
  "success": true,
  "sgf_content": "(;FF[4]...)",
  "sgf_url": "/sgf_files/a1b2c3d4.sgf",
  "sgf_filename": "game_a1b2c3d4.sgf",
  "completion_result": {...}
}
```

#### **POST /sgf/download**
Génération et sauvegarde de fichier SGF avec retour d'URL
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"content_type":"sgf_content","data":"(;FF[4]...)","filename":"partie.sgf"}' \
  http://localhost:5001/sgf/download
```
**Retourne :**
```json
{
  "success": true,
  "sgf_url": "/sgf/file/x1y2z3w4_partie.sgf",
  "filename": "x1y2z3w4_partie.sgf",
  "download_url": "http://localhost:5001/sgf/file/x1y2z3w4_partie.sgf"
}
```

#### **GET /sgf/file/<filename>**
Téléchargement direct d'un fichier SGF sauvegardé
```bash
curl -O http://localhost:5001/sgf/file/game_a1b2c3d4.sgf
```

#### **POST /model/load_yolo**
Chargement du modèle YOLO
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"model_path":"/path/to/model.pt"}' \
  http://localhost:5001/model/load_yolo
```

### Endpoints existants (maintenus)
- `GET /health` - État du service
- `POST /complete` - Complétion de coups entre états
- `POST /analyze` - Analyse de différences entre plateaux
- `POST /model/load` - Chargement modèle CNN
- `GET /model/info` - Informations sur les modèles

## Pipeline d'utilisation

### 1. Initialisation
```python
from service import PhotoAnalysisService

# Initialiser le service avec modèle YOLO
service = PhotoAnalysisService("path/to/model.pt")

# Charger le modèle IA (optionnel)
service.completion_service.load_legacy_model()
```

### 2. Analyse de deux photos
```python
# Pipeline complet : photos → SGF
sgf_content = service.fill_photo(
    "image1.jpg", 
    "image2.jpg", 
    use_ai=True,
    metadata={
        "player_black": "Joueur Noir",
        "player_white": "Joueur Blanc",
        "game_name": "Partie du 2025-01-15"
    }
)

# Sauvegarder le SGF
with open("partie.sgf", "w") as f:
    f.write(sgf_content)
```

### 3. Analyse d'une photo
```python
# Générer SGF à partir d'une position
sgf_content = service.process_single_photo(
    "position.jpg",
    metadata={"game_name": "Position analysée"}
)
```

## Modèles requis

### Modèle YOLO (model.pt)
- **Classes détectées** :
  - 0: Pierres noires
  - 1: Bords du plateau  
  - 2: Coins du plateau
  - 3: Intersections vides
  - 4: Coins vides
  - 5: Bords vides
  - 6: Pierres blanches

### Modèle CNN (modelCNN.keras)
- **Fonction** : Prédiction de coups optimaux
- **Entrée** : Position de plateau 19x19
- **Sortie** : Probabilités de coups

## Stockage des fichiers

### Volume Docker partagé
- **Dossier SGF** : `/app/uploads/sgf/` (dans le conteneur)
- **Volume** : `uploads_data` (partagé avec les autres services)
- **Accès externe** : Via endpoints `/sgf/file/<filename>`

### Génération automatique des URLs
```bash
POST /photo/process_two  →  sgf_url: "/sgf/file/game_a1b2c3d4.sgf"
POST /sgf/download       →  sgf_url: "/sgf/file/x1y2z3w4_partie.sgf"
```

## Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le service
python api.py
```

### Configuration Docker

Le module photo configure automatiquement son stockage via son **Dockerfile** :

```dockerfile
# Crée la structure de dossiers
RUN mkdir -p /app/uploads/sgf /app/uploads/images

# Définit le volume (monté automatiquement par docker-compose)
VOLUME ["/app/uploads"]
```

Le **docker-compose.yaml** monte simplement le volume partagé :
```yaml
photo:
  volumes:
    - uploads_data:/app/uploads  # Volume partagé automatiquement
```

Cette approche est **plus modulaire** - chaque service gère sa propre configuration de stockage.

## Comparaison Tenuki25 vs Tenuki2025

| Fonctionnalité | Tenuki25 (Avant) | Tenuki25 (Après) | Tenuki2025 |
|---------------|------------------|------------------|------------|
| **Architecture** | Module autonome | Module autonome étendu | Intégré |
| **Entrée** | Matrices JSON | Photos + Matrices | Photos |
| **Vision** | Non | YOLO + OpenCV | YOLO + CNN |
| **SGF Export** | Non | Direct | Direct |
| **Upload Web** | Non | API REST | Interface Web |
| **IA Hybride** | CNN seul | CNN + YOLO | CNN + YOLO |
| **Modularité** | Oui | Oui | Non |

## Avantages de la nouvelle version

### **Expérience utilisateur complète**
- Pipeline photo → SGF en une étape
- Upload direct d'images
- Téléchargement automatique de fichiers SGF

### **Performance améliorée** 
- Détection YOLO pour analyse précise des plateaux
- Correction automatique de perspective
- Validation automatique des formats

### **Compatibilité maintenue**
- Tous les endpoints existants fonctionnent
- API REST modulaire conservée  
- Intégration facile dans d'autres systèmes

### **Fonctionnalités avancées**
- Métadonnées SGF complètes
- Analyse de confiance des prédictions
- Support de multiples formats d'images

Le module photo de Tenuki25 offre maintenant les mêmes capacités que Tenuki2025 tout en conservant son architecture modulaire et sa flexibilité d'intégration.