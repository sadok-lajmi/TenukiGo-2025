# Photo Analysis API

FastAPI service pour l'analyse de photos de plateau de Go, la complétion de coups, et la génération de SGF.

## 🚀 Installation

```bash
# Avec Docker (recommandé)
docker-compose up photo

# Ou en local
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 5001
```

## 📚 Documentation

- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc
- **Tests**: Voir [README_TESTING.md](./README_TESTING.md)

## ⚙️ Configuration

Variables d'environnement :
```bash
UPLOAD_FOLDER=/app/uploads          # Dossier uploads
LEGACY_MODEL_PATH=/path/model.keras # Modèle CNN (optionnel)
YOLO_MODEL_PATH=/path/model.pt      # Modèle YOLO (requis pour photos)
PHOTO_HOST=0.0.0.0                 # Host
PHOTO_PORT=5001                    # Port
```

## 🔌 API Endpoints

### Health Check
```http
GET /health
Response: {"status": "healthy", "service": "completion-analysis", "model_loaded": true}
```

### 🤖 Modèles IA

#### Charger modèle CNN (complétion IA)
```http
POST /model/load
Content-Type: application/json
{
  "model_path": "/path/to/model.keras",
  "use_legacy": true
}
```

#### Charger modèle YOLO (détection photos)
```http
POST /model/load_yolo
Content-Type: application/json
{
  "model_path": "/path/to/model.pt"
}
```

#### Informations modèle
```http
GET /model/info
Response: {"model_type": "CNN", "input_shape": [19, 19, 1], "model_loaded": true}
```

#### Décharger modèle
```http
POST /model/unload
```

### 🏁 Complétion de coups

#### Compléter une séquence de coups
```http
POST /complete
Content-Type: application/json
{
  "initial_state": [[0,1,2,...], [0,1,2,...]],  // Plateau initial (0=vide, 1=noir, 2=blanc)
  "final_state": [[0,1,2,...], [0,1,2,...]],   // Plateau final
  "board_size": 19,                             // Taille du plateau (défaut: 19)
  "use_ai": false                               // Utiliser l'IA (défaut: false)
}

Response: {
  "success": true,
  "moves": [[9,9,1], [15,15,2]],               // Liste des coups [(ligne, col, couleur)]
  "method": "algorithmic",                      // Méthode utilisée
  "confidence": 0.8,                           // Score de confiance
  "move_count": 2
}
```

#### Analyser différences entre plateaux
```http
POST /analyze
Content-Type: application/json
{
  "initial_state": [[0,1,2,...], [0,1,2,...]],
  "final_state": [[0,1,2,...], [0,1,2,...]],
  "board_size": 19
}

Response: {
  "differences": {
    "1": {"ajout": [[9,9,1]], "retire": []},    // Pierres noires
    "2": {"ajout": [[15,15,2]], "retire": []}   // Pierres blanches
  }
}
```

### 📸 Analyse de photos

#### Traiter une photo unique
```http
POST /photo/upload
Content-Type: multipart/form-data
file: image.jpg

Response: {
  "board_matrix": [[0,1,2,...], [0,1,2,...]],  // Matrice du plateau détectée
  "stones_info": {"black": 25, "white": 23},   // Nombre de pierres
  "sgf_content": "(;FF[4]GM[1]SZ[19]...)"      // Contenu SGF
}
```

#### Traiter deux photos (complétion automatique)
```http
POST /photo/process_two
Content-Type: multipart/form-data
file1: before.jpg                              // Photo avant
file2: after.jpg                               // Photo après
use_ai: "true"                                 // Utiliser l'IA pour complétion
metadata: '{"player_black":"Alice","player_white":"Bob","event":"Tournament"}'

Response: {
  "sgf_content": "(;FF[4]GM[1]SZ[19]PB[Alice]PW[Bob]...)", 
  "completion_info": {
    "moves": [[9,9,1], [15,15,2]],
    "method": "ai",
    "confidence": 0.9
  },
  "analysis_info": {
    "initial_stones": {"black": 23, "white": 21},
    "final_stones": {"black": 24, "white": 22}
  }
}
```

## 🖥️ Intégration Frontend

### TypeScript/JavaScript

```typescript
// Configuration du service
const PHOTO_API_BASE = 'http://localhost:5001';

// Interface pour les réponses
interface PhotoAnalysisResponse {
  board_matrix: number[][];
  stones_info: { black: number; white: number };
  sgf_content: string;
}

interface CompletionResponse {
  success: boolean;
  moves: [number, number, number][];
  method: 'ai' | 'algorithmic';
  confidence: number;
  move_count: number;
}

// Upload d'une photo unique
async function uploadSinglePhoto(file: File): Promise<PhotoAnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${PHOTO_API_BASE}/photo/upload`, {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) throw new Error('Upload failed');
  return response.json();
}

// Analyse de deux photos avec complétion
async function analyzeTwoPhotos(
  file1: File, 
  file2: File, 
  useAI: boolean = true,
  metadata?: Record<string, string>
): Promise<{sgf_content: string, completion_info: any}> {
  const formData = new FormData();
  formData.append('file1', file1);
  formData.append('file2', file2);
  formData.append('use_ai', useAI.toString());
  
  if (metadata) {
    formData.append('metadata', JSON.stringify(metadata));
  }
  
  const response = await fetch(`${PHOTO_API_BASE}/photo/process_two`, {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) throw new Error('Analysis failed');
  return response.json();
}

// Complétion manuelle de coups
async function completeMovesManual(
  initialState: number[][],
  finalState: number[][],
  useAI: boolean = false
): Promise<CompletionResponse> {
  const response = await fetch(`${PHOTO_API_BASE}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      initial_state: initialState,
      final_state: finalState,
      board_size: 19,
      use_ai: useAI
    })
  });
  
  if (!response.ok) throw new Error('Completion failed');
  return response.json();
}
```

### React Hook Exemple

```typescript
import { useState } from 'react';

export function usePhotoAnalysis() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const analyzePhotos = async (file1: File, file2: File, useAI = true) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await analyzeTwoPhotos(file1, file2, useAI, {
        event: 'Photo Analysis',
        timestamp: new Date().toISOString()
      });
      
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  return { analyzePhotos, loading, error };
}
```

## 🔬 Tests

Le module dispose d'une suite de tests complète avec 100% de couverture :

```bash
# Exécuter les tests
docker exec -it tenuki-photo bash -c "python -m pytest tests/ -v"

# Avec couverture
docker exec -it tenuki-photo bash -c "python -m pytest tests/ --cov=. --cov-report=html"
```

Voir [README_TESTING.md](./README_TESTING.md) pour plus de détails.

## 📝 Exemples curl

```bash
# Health check
curl http://localhost:5001/health

# Upload photo unique
curl -X POST http://localhost:5001/photo/upload \
     -F "file=@plateau.jpg"

# Analyser deux photos
curl -X POST http://localhost:5001/photo/process_two \
     -F "file1=@avant.jpg" \
     -F "file2=@apres.jpg" \
     -F "use_ai=true" \
     -F 'metadata={"player_black":"Alice","player_white":"Bob"}'

# Complétion manuelle
curl -X POST http://localhost:5001/complete \
     -H "Content-Type: application/json" \
     -d '{
       "initial_state": [[0,0,0],[0,1,0],[0,0,0]], 
       "final_state": [[0,0,0],[0,1,2],[0,0,0]], 
       "use_ai": false
     }'

# Charger modèle YOLO
curl -X POST http://localhost:5001/model/load_yolo \
     -H "Content-Type: application/json" \
     -d '{"model_path":"/app/models/yolo_go.pt"}'
```

## 🏗️ Architecture

```
modules/photo/
├── api.py                 # FastAPI endpoints
├── service.py            # Business logic (BoardState, MoveCompletionService)
├── model_loader.py       # AI model management (CNN)
├── image_processor.py    # YOLO-based image processing
├── sgf_generator.py      # SGF file generation
├── settings.py          # Configuration
├── requirements.txt     # Dependencies
├── tests/              # Test suite (109 tests)
│   ├── conftest.py     # Test fixtures
│   ├── test_api.py     # API tests (23)
│   ├── test_service.py # Service tests (21)
│   └── ...
└── README_TESTING.md   # Testing documentation
```