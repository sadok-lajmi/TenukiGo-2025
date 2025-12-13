from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio

from api.processors.StreamingProcessor import StreamingProcessor

router = APIRouter()

# Dictionnaire global pour garder une trace des pipelines actifs
# Clé: match_id, Valeur: Instance de StreamingProcessor
ACTIVE_PROCESSORS = {} 

class ProcessStreamingRequest(BaseModel):
    match_id: int
    rtsp_url: str
    ws_url: str # URL du WebSocket du Backend

@router.post("/stream/start")
async def start_stream(request: ProcessStreamingRequest):
    """
    Démarre le traitement d'un flux live.
    Garantit qu'un seul processeur tourne par match_id.
    """
    if request.match_id in ACTIVE_PROCESSORS:
        raise HTTPException(
            status_code=409, 
            detail=f"Le stream pour le match {request.match_id} est déjà en cours."
        )

    # 1. Créer le processeur
    processor = StreamingProcessor(
        match_id=request.match_id,
        rtsp_url=request.rtsp_url,
        ws_url=request.ws_url
    )

    # 2. Lancer la tâche de fond (dans la boucle d'événements FastAPI)
    task = asyncio.create_task(processor.run())

    # 3. Stocker l'instance du processeur ET la tâche pour l'annulation
    # On ajoute la référence de la tâche au processeur
    processor.task = task 
    ACTIVE_PROCESSORS[request.match_id] = processor 
    
    return {"status": "stream processing started"}

@router.post("/stream/stop")
async def stop_stream(match_id: int):
    """Arrête proprement le processeur de streaming."""
    if match_id not in ACTIVE_PROCESSORS:
        raise HTTPException(status_code=404, detail="Stream non trouvé.")

    processor: StreamingProcessor = ACTIVE_PROCESSORS[match_id]
    
    # 1. Demander au processeur de s'arrêter (change son flag is_running)
    processor.stop() 
    
    # 2. Annuler la tâche asynchrone directement
    if not processor.task and not processor.task.done():
        processor.task.cancel()
        print(f"🛑 Tâche asyncio pour match {match_id} annulée.")
    
    # 3. Supprimer la référence
    del ACTIVE_PROCESSORS[match_id]

    return {"status": "stream processing stopped"}

@router.get("/stream/status")
def get_status():
    """Retourne la liste des streams actifs pour le debug"""
    return {
        "active_streams": list(ACTIVE_PROCESSORS.keys()),
        "count": len(ACTIVE_PROCESSORS)
    }