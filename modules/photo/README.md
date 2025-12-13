# Photo Analysis API

FastAPI service pour l'analyse de photos de plateau de Go et la génération de SGF.

## Installation

```bash
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 5001
```

## Documentation

- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc

## Configuration

Variables d'environnement :
```bash
UPLOAD_FOLDER=/app/uploads          # Dossier uploads
LEGACY_MODEL_PATH=/path/model.keras # Modèle CNN (optionnel)
PHOTO_HOST=0.0.0.0                 # Host
PHOTO_PORT=5001                    # Port
```

## Endpoints

### Health Check
```
GET /health
```

### Modèles

```
POST /model/load
{
  "model_path": "/path/to/model.keras",
  "use_legacy": true
}
```

```
POST /model/load_yolo
{
  "model_path": "/path/to/model.pt"
}
```

```
GET /model/info
```

```
POST /model/unload
```

### Analyse de plateau

```
POST /complete
{
  "initial_state": [[0,0,...], [1,2,...]],
  "final_state": [[0,0,...], [1,2,...]],
  "board_size": 19,
  "use_ai": false
}
```

```
POST /analyze
{
  "initial_state": [[0,0,...], [1,2,...]],
  "final_state": [[0,0,...], [1,2,...]],
  "board_size": 19
}
```

### Upload de photos

```
POST /photo/upload
Content-Type: multipart/form-data
file: image.jpg
```

```
POST /photo/process_two
Content-Type: multipart/form-data
file1: before.jpg
file2: after.jpg
use_ai: "true"
metadata: '{"player_black":"Nom1","player_white":"Nom2"}'
```

## Exemples curl

```bash
# Health check
curl http://localhost:5001/health

# Upload photo
curl -X POST http://localhost:5001/photo/upload \
     -F "file=@image.jpg"

# Analyser deux photos
curl -X POST http://localhost:5001/photo/process_two \
     -F "file1=@before.jpg" \
     -F "file2=@after.jpg" \
     -F "use_ai=true"

# Charger modèle YOLO
curl -X POST http://localhost:5001/model/load_yolo \
     -H "Content-Type: application/json" \
     -d '{"model_path":"/path/to/model.pt"}'
```