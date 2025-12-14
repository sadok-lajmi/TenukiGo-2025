from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import requests
import os

from api.utils.db_services import db
from api.utils.file_storage import save_file, save_file_from_content
from config.settings import (
    STORAGE_DIR,
    VIDEO_DIR,
    THUMBNAIL_DIR,
    SGF_DIR,
    ANALYSIS_SERVICE_URL,
    ANALYSIS_CALLBACK_URL
)

router = APIRouter()

class AnalysisCallback(BaseModel):
    video_id: int
    status: str  # "success" ou "error"
    sgf: Optional[str] = None
    error: Optional[str] = None

@router.get("/videos")
def list_videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            v.video_id, v.title, v.path, v.thumbnail,
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
            v.video_id, v.title, v.path, v.thumbnail,
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
    thumb_path = video["thumbnail"]

    # --- Handle thumbnail replacement ---
    try:
        if thumbnail:
            thumb_path = await save_file(thumbnail, THUMBNAIL_DIR)
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Thumbnail upload failed: {str(e)}")
    
    cur.execute("""
        UPDATE video
        SET
            title = COALESCE(%s, title),
            thumbnail = %s,
            match_id = %s
        WHERE video_id = %s
    """, (
        title,
        thumb_path,
        match_id,
        video_id,
    ))

    if remove_sgf:
        cur.execute("UPDATE video SET sgf = NULL WHERE video_id = %s", (video_id,))
        # delete the SGF file from storage
        p = os.path.join(STORAGE_DIR, video["sgf"])
        if os.path.exists(p):
            os.remove(p)

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
    file: UploadFile = File(...),
    thumbnail: Optional[UploadFile] = File(None),
    match_id: Optional[int] = Form(None)
):  
    try:
        # 2. Save video file
        video_path= await save_file(file, VIDEO_DIR)

        # 3. Save thumbnail if any
        thumb_path = None
        if thumbnail:
            thumb_path = await save_file(thumbnail, THUMBNAIL_DIR)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    # 4. Insertion dans la base de données
    conn = db()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO video (title, path, thumbnail, date_upload, match_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING video_id
    """, (
        title,
        video_path,
        thumb_path,
        datetime.now(),
        match_id
    ))
    
    result = cur.fetchone()
    video_id = result["video_id"]
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "Video uploaded successfully",
        "video_id": video_id,
        "video_path": video_path,
        "thumbnail_path": thumb_path
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
    
    video_path = video['path']
    if not video_path:
        conn.close()
        raise HTTPException(status_code=400, detail="Video path is missing")
    
    # Call Analysis module API
    try:
        response = requests.post(ANALYSIS_SERVICE_URL + "/video/process",
                                 json={"video_id": video_id,
                                       "video_path": os.path.join(STORAGE_DIR, video_path),
                                       "callback_url": ANALYSIS_CALLBACK_URL.replace("video_id", str(video_id))
                                       },
                                 timeout=300)
        
        response.raise_for_status()
        return {"message": "Analysis succesfully launched"}
    
    except requests.RequestException as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Analyse module error: {str(e)}")
    
@router.post("/video/{video_id}/analysis-complete")
def video_analysis_complete(video_id: int, payload: AnalysisCallback):
    """
    Endpoint called by Analysis module when video analysis is complete.
    Deals with both success and error cases.
    1. On success, saves the SGF to file storage and updates the video record
    2. On error, logs the error (for now, just raises an HTTPException)
    3. On invalid payload, raises HTTPException
    """
    conn = db()
    cur = conn.cursor()
    
    # Fetch video details
    cur.execute("SELECT * FROM video WHERE video_id = %s", (video_id,))
    video = cur.fetchone()
    if not video:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Case 1 : success
    if payload.status == "success" and payload.sgf:
        try:
            # Save SGF to file storage
            sgf_path = save_file_from_content(
                f"video_{video_id}.sgf", 
                payload.sgf.encode('utf-8'), 
                SGF_DIR
            )
            
            # Update video record
            cur.execute("UPDATE video SET sgf = %s WHERE video_id = %s", (sgf_path, video_id))
            conn.commit()
            conn.close()
            return {"message": "SGF saved successfully"}
            
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=500, detail=f"Error saving SGF: {str(e)}")
    
    # Case 2 : error
    elif payload.status == "error":
        print(f"Analysis failed for video {video_id}: {payload.error}")
        conn.commit()
        conn.close()
        return {"message": "Error received and logged"}
    
    # Case 3 : invalid status
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid payload: missing SGF for success status")