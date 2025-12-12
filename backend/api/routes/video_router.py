from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from pathlib import Path
import requests
import os

from utils.db_services import db
from utils.file_storage import upload_file, upload_file_from_content
from config.settings import (
    VIDEO_DIR,
    THUMBNAIL_DIR,
    SGF_DIR,
    ANALYSIS_SERVICE_URL
)

router = APIRouter()

@router.get("/videos")
def list_videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            v.video_id, v.title, v.path, v.url, v.thumbnail,
            v.date_upload, v.duration, v.match_id, m.date AS match_date
        FROM video v
        LEFT JOIN match m ON v.match_id = m.match_id
        ORDER BY v.date_upload DESC
    """)
    videos = cur.fetchall()
    
    conn.close()
    return {"videos": videos, "count": len(videos)}

@router.get("/video/{video_id}")
def get_video(video_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            v.video_id, v.title, v.path, v.url, v.thumbnail,
            v.date_upload, v.duration, v.sgf AS video_sgf,
            m.match_id, m.style, m.result, m.description,
            m.date AS match_date,
            w.firstname || ' ' || w.lastname AS white,
            b.firstname || ' ' || b.lastname AS black,
            m.sgf, m.title AS match_title
        FROM video v
        LEFT JOIN match m ON v.match_id = m.match_id
        LEFT JOIN player w ON m.white_id = w.player_id
        LEFT JOIN player b ON m.black_id = b.player_id
        WHERE v.video_id = %s
    """, (video_id,))
    video = cur.fetchone()
    conn.close()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return video

@router.post("/video/{video_id}/edit")
async def edit_video(
    video_id: int,
    title: Optional[str] = Form(None),
    match_id: Optional[int] = Form(None),
    thumbnail: Optional[UploadFile] = File(None),
    remove_sgf: Optional[bool] = Form(None)
):
    conn = db()
    cur = conn.cursor()

    # --- Fetch existing video ---
    cur.execute("SELECT * FROM video WHERE video_id = %s", (video_id,))
    video = cur.fetchone()
    if not video:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")

    # Start with current values
    thumb_url = video["thumbnail"]

    # --- Handle thumbnail replacement ---
    if thumbnail:
        _, thumb_url = await upload_file(thumbnail, THUMBNAIL_DIR)

    cur.execute("""
        UPDATE video
        SET
            title = COALESCE(%s, title),
            thumbnail = %s,
            match_id = %s
        WHERE video_id = %s
    """, (
        title,
        thumb_url,
        match_id,
        video_id,
    ))

    if remove_sgf:
        cur.execute("UPDATE video SET sgf = NULL WHERE video_id = %s", (video_id,))
        # delete the SGF file from storage
        p = Path(video["sgf"])
        if p.exists():
            p.unlink()

    conn.commit()
    conn.close()

    # Return updated result
    return get_video(video_id)

@router.delete("/video/{video_id}/delete")
def delete_video(video_id: int):
    conn = db()
    cur = conn.cursor()

    # Check exists
    cur.execute("SELECT * FROM video WHERE video_id = %s", (video_id,))
    video = cur.fetchone()
    if not video:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete video record
    cur.execute("DELETE FROM video WHERE video_id = %s", (video_id,))

    conn.commit()
    conn.close()
    return {"message": "Video deleted"}

@router.post("/video/upload")
async def upload_video(
    title: str = Form(...),
    file: UploadFile = File(...),  # Compatible avec le nom de champ 'file' attendu par le frontend
    thumbnail: Optional[UploadFile] = File(None),
    match_id: Optional[str] = Form(None)  # Compatible avec le nom de champ 'match_id'
):
    # 1. Traitement du match_id pour assurer qu'il est un entier ou None
    match_id_int = None
    if match_id and match_id.strip() and match_id.lower() != "none":
        try:
            match_id_int = int(match_id)
        except ValueError:
            # En cas de valeur invalide (e.g., texte), on l'ignore silencieusement
            pass
    
    try:
        # 2. Sauvegarde du fichier vidéo (Utilisation de la fonction utilitaire asynchrone)
        video_path, video_url = await upload_file(file, VIDEO_DIR)

        # 3. Sauvegarde de la miniature
        thumb_url = None
        if thumbnail:
            _, thumb_url = await upload_file(thumbnail, THUMBNAIL_DIR)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    # 4. Insertion dans la base de données
    conn = db()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO video (title, path, url, thumbnail, match_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING video_id
    """, (
        title,
        video_path,
        video_url,
        thumb_url,
        match_id_int
    ))
    
    result = cur.fetchone()
    video_id = result["video_id"]
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "Video uploaded successfully",
        "video_id": video_id,
        "video_url": video_url,
        "thumbnail_url": thumb_url
    }

@router.post("/video/{video_id}/convert-to-sgf")
def generate_sgf_from_video(video_id: int):
    """Generate SGF from an uploaded video using the Analysis module"""
    conn = db()
    cur = conn.cursor()
    
    # Fetch video details
    cur.execute("SELECT * FROM video WHERE video_id = %s", (video_id,))
    video = cur.fetchone()
    if not video:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_url = video['url']
    if not video_url:
        conn.close()
        raise HTTPException(status_code=400, detail="Video URL is missing")
    
    # Call Analysis module API
    try:
        requests.post(ANALYSIS_SERVICE_URL + "/video/process",
                                 json={"video_id": video_id, "filename": os.path.basename(video_url)},
                                 timeout=300)
        
        return {"message": "Analysis succesfully launched"}
    
    except requests.RequestException as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Analyse module error: {str(e)}")
    
@router.post("/video/{video_id}/analysis-complete")
def video_analysis_complete(video_id: int, sgf: str):
    """Endpoint called by Analysis module when video analysis is complete"""
    conn = db()
    cur = conn.cursor()
    
    # Fetch video details
    cur.execute("SELECT * FROM video WHERE video_id = %s", (video_id,))
    video = cur.fetchone()
    if not video:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Save SGF to file storage
    _, sgf_url = upload_file_from_content(f"video_{video_id}.sgf", sgf.encode('utf-8'), SGF_DIR)
    
    # Add sgf to database in video table
    cur.execute("UPDATE video SET sgf = %s WHERE video_id = %s", (sgf_url, video_id))
    
    conn.close()
    return {"message": "SGF saved"}