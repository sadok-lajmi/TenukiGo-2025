"""
API routes for managing Go matches.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from datetime import datetime
import os

from api.routes.utils.db_services import db
from api.routes.utils.file_storage import save_file
from config.Settings import settings

router = APIRouter()

@router.get("/matches")
def list_matches():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            m.match_id, m.title, m.result, m.date, m.duration, m.description,
            m.style, m.sgf,
            w.firstname || ' ' || w.lastname AS white,
            b.firstname || ' ' || b.lastname AS black,
            v.video_id, v.thumbnail, v.title As video_title, v.path AS video_path, v.sgf AS video_sgf
        FROM match m
        LEFT JOIN player w ON m.white_id = w.player_id
        LEFT JOIN player b ON m.black_id = b.player_id
        LEFT JOIN video v ON m.match_id = v.match_id
        ORDER BY m.date DESC
    """)
    matches = cur.fetchall()
    
    conn.close()
    return {"matches": matches, "count": len(matches)}

@router.get("/match/{match_id}")
def get_match(match_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            m.match_id, m.title, m.result, m.style,
            m.white_id AS white, m.black_id AS black,
            m.duration, m.date,
            v.video_id, v.path AS video, v.thumbnail, v.sgf AS video_sgf,
            m.sgf
        FROM match m
        LEFT JOIN video v ON m.match_id = v.match_id
        WHERE m.match_id = %s
    """, (match_id,))
    match = cur.fetchone()
    conn.close()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    return match

@router.post("/match/create")
async def create_match(
    title: str = Form(...),
    style: Optional[str] = Form(None),
    white: int = Form(...),
    black: int = Form(...),
    result: str = Form(...),
    date: Optional[datetime] = Form(None),
    duration: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    video: Optional[UploadFile] = File(None),
    video_id: Optional[int] = Form(None),
    thumbnail: Optional[UploadFile] = File(None),
    sgf: Optional[UploadFile] = File(None)
):
    conn = db()
    cur = conn.cursor()

    sgf_path = None
    if sgf:
        sgf_path = await save_file(sgf, settings.SGF_DIR)

    # Insert Match record first
    cur.execute("""
        INSERT INTO match (title, style, white_id, black_id, result, date, duration, description, sgf)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING match_id
    """, (title, style, white, black, result, date, duration, description, sgf_path))
    match_id = cur.fetchone()["match_id"]

    if video:
        # Save video
        video_path = await save_file(video, settings.VIDEO_DIR)

        # Save thumbnail if any
        thumb_path = None
        if thumbnail:
            thumb_path = await save_file(thumbnail, settings.THUMBNAIL_DIR)
        
        # Insert Video record
        cur.execute("""
            INSERT INTO video (title, path, thumbnail, date_upload, match_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, video_path, thumb_path, datetime.now(), match_id))
        
    elif video_id:
        cur.execute("UPDATE video SET match_id = %s WHERE video_id = %s", (match_id, video_id))

    conn.commit()
    conn.close()
    return {"message": "Match created", "match_id": match_id}

@router.post("/match/{match_id}/edit")
async def edit_match(
    match_id: int,
    title: Optional[str] = Form(None),
    style: Optional[str] = Form(None),
    white: Optional[int] = Form(None),
    black: Optional[int] = Form(None),
    result: Optional[str] = Form(None),
    date: Optional[datetime] = Form(None),
    duration: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    video: Optional[UploadFile] = File(None),
    sgf: Optional[UploadFile] = File(None),
    video_id: Optional[str] = Form(None),  # match selects an existing video
    remove_video: Optional[str] = Form(None),  # explicit removal
    remove_sgf: Optional[str] = Form(None)
):
    conn = db()
    cur = conn.cursor()
    # ------------------------------------------------------
    # 1. Load match
    # ------------------------------------------------------
    cur.execute("SELECT * FROM match WHERE match_id = %s", (match_id,))
    match = cur.fetchone()
    if not match:
        raise HTTPException(404, "Match not found")

    # Get old video id if any
    cur.execute("SELECT video_id FROM video WHERE match_id = %s", (match_id,))
    video_row = cur.fetchone()
    old_video_id = video_row["video_id"] if video_row else None

    # ------------------------------------------------------
    # 2. Update simple text fields
    # ------------------------------------------------------
    cur.execute("""
        UPDATE match SET
            title = COALESCE(%s, title),
            style = COALESCE(%s, style),
            white_id = COALESCE(%s, white_id),
            black_id = COALESCE(%s, black_id),
            result = COALESCE(%s, result),
            date = COALESCE(%s, date),
            duration = COALESCE(%s, duration),
            description = COALESCE(%s, description)
        WHERE match_id = %s
    """, (title, style, white, black, result, date, duration, description, match_id))

    # ------------------------------------------------------
    # 3. SGF HANDLING
    # ------------------------------------------------------
    sgf_path = match["sgf"]

    if sgf:  # replace SGF
        sgf_path = await save_file(sgf, settings.SGF_DIR)

    elif remove_sgf == "true" and sgf_path:
        # delete old file
        p = os.path.join(settings.STORAGE_DIR, sgf_path)
        if os.path.exists(p):
            os.remove(p)
        sgf_path = None

    # save sgf path
    cur.execute("UPDATE match SET sgf = %s WHERE match_id = %s", (sgf_path, match_id))

    # ------------------------------------------------------
    # 4. VIDEO HANDLING
    # ------------------------------------------------------

    # CASE A — remove video
    if remove_video == "true":
        if old_video_id:
            cur.execute("UPDATE video SET match_id = NULL WHERE video_id = %s", (old_video_id,))

    # CASE B — NEW VIDEO UPLOAD
    if video:  
        video_path = await save_file(video, settings.VIDEO_DIR)

        cur.execute("""
            INSERT INTO video (title, path, date_upload)
            VALUES (%s, %s, %s)
            RETURNING video_id
        """, (title, video_path, datetime.now()))

        new_video_id = cur.fetchone()["video_id"]
        # Remove old association if any
        if old_video_id:
            cur.execute("UPDATE video SET match_id = NULL WHERE video_id = %s", (old_video_id,))

        # Link new video to match
        cur.execute("UPDATE video SET match_id = %s WHERE video_id = %s",
                    (match_id, new_video_id))

    # CASE C — EXISTING VIDEO SELECTED (only if no new upload!)
    elif video_id and video_id != "" and video_id != str(old_video_id):
        # Remove old association if any
        if old_video_id:
            cur.execute("UPDATE video SET match_id = NULL WHERE video_id = %s", (old_video_id,))
        # Link new video to match
        cur.execute("UPDATE video SET match_id = %s WHERE video_id = %s",
                    (match_id, video_id))

    # ------------------------------------------------------
    # END
    # ------------------------------------------------------
    conn.commit()
    conn.close()
    return get_match(match_id)

@router.delete("/match/{match_id}/delete")
def delete_match(match_id: int):
    conn = db()
    cur = conn.cursor()

    # Check exists
    cur.execute("SELECT * FROM match WHERE match_id = %s", (match_id,))
    match = cur.fetchone()
    if not match:
        conn.close()
        raise HTTPException(status_code=404, detail="Match not found")

    # Remove association from video if any
    cur.execute("UPDATE video SET match_id = NULL WHERE match_id = %s", (match_id,))

    # Remove SGF file if any
    if match["sgf"]:
        p = os.path.join(settings.STORAGE_DIR, match["sgf"])
        if os.path.exists(p):
            os.remove(p)

    # Delete match record
    cur.execute("DELETE FROM match WHERE match_id = %s", (match_id,))

    conn.commit()
    conn.close()
    return {"message": "Match deleted"}