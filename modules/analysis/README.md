# Video Analysis Service

Service FastAPI dédié à l'analyse de flux vidéo en temps réel (RTSP) et à l'analyse de vidéo en différé, la détection de pierres de Go via Computer Vision/CNN, et la génération de SGF en direct.

## 🚀 Installation

Il est possible de lancer le service localement et d'utiliser le service manuellement.
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5000
```
Cependant, ce module a été conçu pour être déployé via Docker dans l'architecture complète de TenukiGo. Il est recommandé d'utiliser `docker-compose` dans le dossier `docker/` pour lancer tous les services ensemble.

## ⚙️ Configuration

Variables d'environnement (créer un fichier `.env`) :

```bash
TF_ENABLE_ONEDNN_OPTS=0
```

## 🔌 API Endpoints

Ce service est piloté principalement par le Backend via des appels REST.
Pour la diffusion des coups détectés en temps réel, il communique ses résultats via WebSocket.
Pour l'analyse d'une vidéo en différé, l'analyse est faite en tâche de fond et génère un fichier SGF qui est envoyé au Backend une fois l'analyse terminée.

### Health Check

```http
GET /health
Response: {"status": "healthy", "active_streams": 1}
```

### 🎥 Gestion du Streaming

#### Démarrer l'analyse d'un flux

Déclenche un processus d'arrière-plan (`StreamingProcessor`) qui lit le RTSP et envoie les coups via WebSocket.

```http
POST /stream/start
Content-Type: application/json
{
  "match_id": 123,
  "rtsp_url": "rtsp://mediamtx:8554/live/1",
  "ws_url": "ws://backend:8000/ws/match/123"
}

Response: {
  "status": "stream processing started",
  "match_id": 123
}
```

#### Arrêter l'analyse

Arrête proprement la boucle OpenCV et libère les ressources.

```http
POST /stream/stop
Content-Type: application/json
params: match_id=123

Response: {
  "status": "stream processing stopped",
  "match_id": 123
}
```

### 🎥 Gestion des Vidéos en différé

#### Démarrer l'analyse d'une vidéo

Déclenche un processus d'arrière-plan (`VideoProcessor`) qui lit la vidéo et envoie le fichier SGF au Backend une fois terminé.

```http
POST /video/process
Content-Type: application/json
{
    "video_id": 123,
    "video_path": "videos/video.mp4",
    "callback_url": "http://backend:8000/video/123/analysis-complete"
}


Response: {
    "status": "processing_started", 
    "message": "Video analysis started in background."
}
```

### Statut des flux

```http
GET /stream/status
Response: {
  "active_streams": [123, 124],
  "count": 2
}
```

## 🧠 Fonctionnement de l'Analyse en live

Le service suit une pipeline stricte pour chaque frame vidéo :

1.  **Ingestion RTSP** : Lecture du flux via OpenCV (TCP forcé).
2.  **Détection** : Localisation du plateau de Go et correction de perspective.
3.  **Extraction** : Découpage de la grille 19x19.
4.  **Inférence** : Analyse de l'état (Noir/Blanc/Vide) via CNN (`modelCNN.keras`).
5.  **Broadcast** : Envoi du SGF mis à jour au Backend via WebSocket uniquement si l'état change.

## 🛠️ Dépannage (Troubleshooting)

### Erreur CUDA / TensorFlow (Erreur 303)

Si vous voyez `INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)` :

  * **Cause** : TensorFlow détecte des drivers NVIDIA sur l'hôte mais le conteneur n'a pas accès au GPU.
  * **Solution** : Aucune solution n'a été trouvée pour l'instant. L'erreur n'empêche pas le service de fonctionner en CPU.

### Artefacts Vidéo / Corrupted Macroblock

Si vous voyez `[h264 @ ...] error while decoding MB ...` ou des images grises :

  * **Cause** : Problème de transfert de paquets entre le service MediaMTX et le module d'analyse.
  * **Solution** : Aucune solution fiable n'a été trouvée. Cela ne semble pas affecter la détection des coups.

## 🏗️ Architecture du Module

```
modules/analysis/
├── main.py                 # Point d'entrée & Routes API
├── StreamingProcessor.py   # Gestionnaire de boucle asynchrone & OpenCV
├── logique/
│   ├── GoGame.py          # Logique métier & règles du Go
│   ├── GoBoard.py         # Computer Vision (Détection plateau)
│   ├── utils/             # Helpers (SGF, chargement modèles)
│   └── corrector_noAI.py  # Fallback si l'IA échoue
├── models/                 # Fichiers .pt et .keras
├── requirements.txt        # Dépendances (opencv-python, tensorflow, fastapi...)
└── Dockerfile              # Configuration de l'image
```

## 📚 Références

- TenukiGo 2024 Project GitHub :
https://github.com/Borishkof/TenukiGo

