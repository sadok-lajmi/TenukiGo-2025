from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles
from typing import Optional
from datetime import datetime
from pathlib import Path
import os
import requests

from websockets.ConnectionManager import ConnectionManager
from utils.db_services import db
from utils.file_storage import upload_file, upload_file_from_content
from config.settings import (
    UPLOAD_DIR, 
    VIDEO_DIR, 
    THUMBNAIL_DIR, 
    SGF_DIR, 
    ANALYSIS_SERVICE_URL,
    WS_STREAMING_URL,
    MEDIAMTX_RTSP_URL
)

app = FastAPI(title="Go Game API")

# ======================
# CONFIGURATION
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount static files for serving uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Manager for WebSocket connections
manager = ConnectionManager()


# ======================
# LIST ROUTES
# ======================

@app.get("/videos")
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


@app.get("/matches")
def list_matches():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            m.match_id, m.title, m.result, m.date, m.duration, m.description,
            m.style,
            w.firstname || ' ' || w.lastname AS white,
            b.firstname || ' ' || b.lastname AS black,
            v.video_id, v.thumbnail, v.title As video_title
        FROM match m
        LEFT JOIN player w ON m.white_id = w.player_id
        LEFT JOIN player b ON m.black_id = b.player_id
        LEFT JOIN video v ON m.match_id = v.match_id
        ORDER BY m.date DESC
    """)
    matches = cur.fetchall()
    
    conn.close()
    return {"matches": matches, "count": len(matches)}


@app.get("/players")
def list_players():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT player_id, firstname, lastname, level
        FROM player
        ORDER BY lastname
    """)
    players = cur.fetchall()
    conn.close()
    return {"players": players, "count": len(players)}

# ======================
# DETAIL ROUTES
# ======================
@app.get("/video/{video_id}")
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


@app.get("/match/{match_id}")
def get_match(match_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            m.match_id, m.title, m.result, m.style,
            m.white_id AS white, m.black_id AS black,
            m.duration, m.date,
            v.video_id, v.url AS video, v.thumbnail, v.sgf AS video_sgf,
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

@app.get("/player/{player_id}")
def get_player(player_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT player_id, firstname, lastname, level
        FROM player
        WHERE player_id = %s
    """, (player_id,))
    player = cur.fetchone()

    if not player:
        conn.close()
        raise HTTPException(status_code=404, detail="Player not found")

    cur.execute("""
        SELECT match_id FROM match
        WHERE white_id = %s OR black_id = %s
    """, (player_id, player_id))
    matches = [row["match_id"] for row in cur.fetchall()]
    count_matches = len(matches)

    cur.execute("""
        SELECT COUNT(*) FROM match
        WHERE (white_id = %s AND result = 'white')
           OR (black_id = %s AND result = 'black')
    """, (player_id, player_id))
    wins = cur.fetchone()["count"]

    conn.close()
    player["matches"] = matches
    player["count_matches"] = count_matches
    player["wins"] = wins
    return player

# ======================
# CREATE / UPLOAD ROUTES
# ======================

@app.post("/create_player")
def create_player(
    firstname: str = Form(...),
    lastname: str = Form(...),
    level: Optional[str] = Form(None)
):
    print(f"Creating player: {firstname} {lastname}, level: {level}")
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO player (firstname, lastname, level)
        VALUES (%s, %s, %s)
        RETURNING player_id
    """, (firstname, lastname, level))
    print(f"Created player: {firstname} {lastname}, level: {level}")
    player_id = cur.fetchone()["player_id"]
    conn.commit()
    conn.close()
    return {"message": "Player created", "player_id": player_id}

@app.post("/upload_video")
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

@app.post("/create_match")
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

    sgf_url = None
    if sgf:
        # Use the utility to save the SGF file
        _, sgf_url = await upload_file(sgf, SGF_DIR)

    # Insert Match record first
    cur.execute("""
        INSERT INTO match (title, style, white_id, black_id, result, date, duration, description, sgf)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING match_id
    """, (title, style, white, black, result, date, duration, description, sgf_url)) # sgf_url is a str
    match_id = cur.fetchone()["match_id"]

    if video:
        # Save video and get URLs
        video_path, video_url = await upload_file(video, VIDEO_DIR)

        thumb_url = None
        if thumbnail:
            _, thumb_url = await upload_file(thumbnail, THUMBNAIL_DIR)
        
        # Insert Video record
        cur.execute("""
            INSERT INTO video (title, path, url, thumbnail, match_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, video_path, video_url, thumb_url, match_id))
        
    elif video_id:
        cur.execute("UPDATE video SET match_id = %s WHERE video_id = %s", (match_id, video_id))

    conn.commit()
    conn.close()
    return {"message": "Match created", "match_id": match_id}

@app.post("/create_match")
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

    sgf_url = None
    if sgf:
        _, sgf_url = await upload_file(sgf, SGF_DIR)

    cur.execute("""
        INSERT INTO match (title, style, white_id, black_id, result, date, duration, description, sgf)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING match_id
    """, (title, style, white, black, result, date, duration, description, sgf_url))
    match_id = cur.fetchone()["match_id"]

    if video:
        video_path, video_url = await upload_file(video, VIDEO_DIR)

        thumb_url = None
        if thumbnail:
            _, thumb_url = await upload_file(thumbnail, THUMBNAIL_DIR)
        
        cur.execute("""
            INSERT INTO video (title, path, url, thumbnail, match_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, video_path, video_url, thumb_url, match_id))

    elif video_id:
        cur.execute("UPDATE video SET match_id = %s WHERE video_id = %s", (match_id, video_id))

    conn.commit()
    conn.close()
    return {"message": "Match created", "match_id": match_id}

# ======================
# HEALTH CHECK
# ======================

@app.get("/")
def read_root():
    return {"message": "Go Game API is running"}

# -----------------------------------------------------------
# EDITING ROUTES
# -----------------------------------------------------------
@app.post("/video/{video_id}/edit")
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

@app.post("/match/{match_id}/edit")
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
        _, sgf_path = await upload_file(sgf, SGF_DIR)

    elif remove_sgf == "true" and sgf_path:
        # delete old file
        p = Path(sgf_path)
        if p.exists():
            p.unlink()
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
        video_path, video_url = await upload_file(video, VIDEO_DIR)

        cur.execute("""
            INSERT INTO video (title, path, url, thumbnail)
            VALUES (%s, %s, %s, %s)
            RETURNING video_id
        """, (title, video_path, video_url, None))

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


@app.post("/player/{player_id}/edit")
def edit_player(
    player_id: int,
    firstname: Optional[str] = Form(None),
    lastname: Optional[str] = Form(None),
    level: Optional[str] = Form(None)
):
    conn = db()
    cur = conn.cursor()

    # Check exists
    cur.execute("SELECT * FROM player WHERE player_id = %s", (player_id,))
    player = cur.fetchone()
    if not player:
        conn.close()
        raise HTTPException(status_code=404, detail="Player not found")

    cur.execute("""
        UPDATE player
        SET firstname = COALESCE(%s, firstname),
            lastname = COALESCE(%s, lastname),
            level = %s
        WHERE player_id = %s
    """, (firstname, lastname, level, player_id))

    conn.commit()
    conn.close()

    return get_player(player_id)

# -----------------------------------------------------------
# DELETE ROUTES
# -----------------------------------------------------------

@app.delete("/video/{video_id}/delete")
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

@app.delete("/match/{match_id}/delete")
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

    # Delete match record
    cur.execute("DELETE FROM match WHERE match_id = %s", (match_id,))

    conn.commit()
    conn.close()
    return {"message": "Match deleted"}

@app.delete("/player/{player_id}/delete")
def delete_player(player_id: int):
    conn = db()
    cur = conn.cursor()

    # Check exists
    cur.execute("SELECT * FROM player WHERE player_id = %s", (player_id,))
    player = cur.fetchone()
    if not player:
        conn.close()
        raise HTTPException(status_code=404, detail="Player not found")

    # Check for associated matches
    cur.execute("SELECT COUNT(*) FROM match WHERE white_id = %s OR black_id = %s", (player_id, player_id))
    count = cur.fetchone()["count"]
    if count > 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot delete player with associated matches")

    # Delete player record
    cur.execute("DELETE FROM player WHERE player_id = %s", (player_id,))

    conn.commit()
    conn.close()
    return {"message": "Player deleted"}

# -----------------------------------------------------------
# LIVESTREAMING ROUTES
# -----------------------------------------------------------

@app.post("/start_stream")
def start_stream(
    title: str = Form(...),
    style: Optional[str] = Form(...),
    description: Optional[str] = Form(None),
    white: int = Form(...),
    black: int = Form(...),
    url: str = Form(...)
):
    sgf_url = SGF_DIR + f"/{int(datetime.now().timestamp())}.sgf"
    rtsp_url = MEDIAMTX_RTSP_URL + url.removeprefix("http://mediamtx:8080").removesuffix("/index.m3u8")

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO match (title, style, white_id, black_id, description, date, sgf)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING match_id
    """, (title, style, white, black, description, datetime.now(), sgf_url))
    match_id = cur.fetchone()["match_id"]
    cur.execute("""
        INSERT INTO stream (url, match_id)
        VALUES (%s, %s)
    """, (url, match_id))
    conn.commit()
    conn.close()

    try:
        requests.post(ANALYSIS_SERVICE_URL + "/stream/start", 
                      json={"rtsp_url": rtsp_url, "match_id": match_id, "ws_url": WS_STREAMING_URL + f"/{match_id}"}, 
                      timeout=10)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to start stream analysis: {str(e)}")

    return {"message": "Stream started", "match_id": match_id}

@app.get("/streams")
def list_streams():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            s.stream_id, s.url,
            m.title AS title
        FROM stream s
        LEFT JOIN match m ON s.match_id = m.match_id
    """)
    streams = cur.fetchall()
    conn.close()
    return {"streams": streams, "count": len(streams)}

@app.get("/stream/{stream_id}")
def get_stream(stream_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            s.stream_id, s.url, s.match_id,
            m.title AS title,
            w.firstname || ' ' || w.lastname AS white, w.player_id AS white_id,
            b.firstname || ' ' || b.lastname AS black, b.player_id AS black_id,
            m.style, m.description, m.date
        FROM stream s
        LEFT JOIN match m ON s.match_id = m.match_id
        LEFT JOIN player w ON m.white_id = w.player_id
        LEFT JOIN player b ON m.black_id = b.player_id
        WHERE s.stream_id = %s
    """, (stream_id,))
    stream = cur.fetchone()
    conn.close()

    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return stream

# -----------------------------------------------------------
# ANALYSIS MODULE INTEGRATION
# -----------------------------------------------------------

@app.post("/video/{video_id}/convert-to-sgf")
def generate_sgf_from_video(video_id: int):
    """Generate SGF from an uploaded video using the Analyse module"""
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
    
    # Call Analyse module API
    try:
        requests.post(ANALYSIS_SERVICE_URL + "/video/process",
                                 json={"video_id": video_id, "filename": os.path.basename(video_url)},
                                 timeout=300)
        
        return {"message": "Analysis succesfully launched"}
    
    except requests.RequestException as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Analyse module error: {str(e)}")
    
@app.post("/video/{video_id}/analysis-complete")
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

# -----------------------------------------------------------
# PHOTO MODULE INTEGRATION
# -----------------------------------------------------------

@app.post("/photo")
def complete_between_photos(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...)
):
    """Endpoint to send front and back photos to the Photo module for processing"""
    try:
        files = {
            'intial_state': (image1.filename, image1.file, image1.content_type),
            'final_state': (image2.filename, image2.file, image2.content_type)
        }
        response = requests.post("http://photo:5001/complete", files=files, timeout=300)
        result = response.json()
        return result
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Photo module error: {str(result['error'])}")
