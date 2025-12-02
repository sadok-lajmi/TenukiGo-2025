from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Form, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles
from typing import Optional
from datetime import datetime
from pathlib import Path
import json
import os
import requests

from api.ConnectionManager import ConnectionManager
from database.services import process_and_save_game, db
from api.utils import upload_file, upload_file_from_content
from config.settings import CLUB_PASSWORD, UPLOAD_DIR, VIDEO_DIR, THUMBNAIL_DIR, SGF_DIR, ANALYSE_SERVICE_URL

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
# UTILITY FUNCTIONS
# ======================

def clean_path_for_url(file_path: str) -> str:
    """Convert file system path to web URL path"""
    if not file_path:
        return None  # Retourne None au lieu d'une chaîne vide
    
    # Si c'est déjà une URL correcte, la retourner
    if file_path.startswith('/uploads/') or file_path.startswith('http'):
        return file_path
    
    # Convertir les backslashes en forward slashes
    cleaned = file_path.replace('\\', '/')
    
    # Extraire juste le nom de fichier
    if '/' in cleaned:
        filename = cleaned.split('/')[-1]
    else:
        filename = cleaned
    
    # Déterminer le bon sous-dossier basé sur l'extension ou le contenu du chemin
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
        return f"/uploads/thumbnails/{filename}"
    elif ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
        return f"/uploads/videos/{filename}"
    elif ext in ['sgf']:
        return f"/uploads/sgf/{filename}"
    elif 'thumbnail' in file_path.lower():
        return f"/uploads/thumbnails/{filename}"
    elif 'video' in file_path.lower():
        return f"/uploads/videos/{filename}"
    elif 'sgf' in file_path.lower():
        return f"/uploads/sgf/{filename}"
    else:
        return f"/uploads/{filename}"
# ------------------------------
# WEBSOCKET: SPECTATOR FEED
# ------------------------------
@app.websocket("/ws/spectator_feed")
async def websocket_spectator_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for spectators.
    Keeps a connection open so spectators can receive real-time updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # keep connection alive / wait for ping messages from client
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ------------------------------------------------
# WEBSOCKET: CAMERA FEED (STUB)
# ------------------------------------------------
@app.websocket("/ws/camera_feed")
async def websocket_camera_endpoint(websocket: WebSocket):
    """
    Stub endpoint to receive camera data via WebSocket.
    Expected JSON payload from camera; uses CLUB_PASSWORD for basic auth.
    """
    await websocket.accept()
    print("Camera connection (stub) accepted.")
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("password") != CLUB_PASSWORD:
                await websocket.send_json({"status": "error", "message": "Invalid password"})
                await websocket.close()
                break

            # 1. Save to DB (run in threadpool to avoid blocking)
            try:
                result_data = await run_in_threadpool(process_and_save_game, data)

                # 2. Broadcast result to spectators
                await manager.broadcast(json.dumps(result_data))

                # 3. Acknowledge the camera
                await websocket.send_json({"status": "success", "message": "Data received and broadcasted"})

            except Exception as e:
                await websocket.send_json({"status": "error", "message": f"Database error: {e}"})

    except WebSocketDisconnect:
        print("Camera connection (stub) closed.")


# ======================
# DATABASE CLEANUP ROUTES
# ======================

@app.get("/debug-urls")
def debug_urls():
    """Debug endpoint to see all URLs in database"""
    conn = db()
    cur = conn.cursor()
    
    # Check videos
    cur.execute("SELECT video_id, title, path, url, thumbnail FROM video ORDER BY video_id DESC LIMIT 10")
    videos = cur.fetchall()
    
    # Check matches
    cur.execute("SELECT match_id, title, sgf FROM match WHERE sgf IS NOT NULL ORDER BY match_id DESC LIMIT 10")
    matches = cur.fetchall()
    
    conn.close()
    
    return {
        "videos": videos,
        "matches": matches,
        "note": "Check if paths contain backslashes or absolute paths like C:\\"
    }


@app.post("/cleanup-all-urls")
def cleanup_all_urls():
    """Comprehensive cleanup of ALL URLs in the database"""
    conn = db()
    cur = conn.cursor()
    
    stats = {
        "video_thumbnails": 0,
        "video_urls": 0,
        "match_sgf": 0,
        "video_paths": 0
    }
    
    try:
        print("\n" + "=" * 50)
        print("🧹 STARTING COMPREHENSIVE URL CLEANUP")
        print("=" * 50)
        
        # 1. Clean video thumbnails
        cur.execute("SELECT video_id, thumbnail FROM video WHERE thumbnail IS NOT NULL")
        videos = cur.fetchall()
        
        for video in videos:
            old_thumbnail = video['thumbnail']
            new_thumbnail = clean_path_for_url(old_thumbnail)
            
            if new_thumbnail and new_thumbnail != old_thumbnail:
                cur.execute(
                    "UPDATE video SET thumbnail = %s WHERE video_id = %s",
                    (new_thumbnail, video['video_id'])
                )
                stats["video_thumbnails"] += 1
                print(f"✓ Video {video['video_id']} thumbnail: {old_thumbnail} -> {new_thumbnail}")
        
        # 2. Clean video URLs
        cur.execute("SELECT video_id, url FROM video WHERE url IS NOT NULL")
        videos_url = cur.fetchall()
        
        for video in videos_url:
            old_url = video['url']
            new_url = clean_path_for_url(old_url)
            
            if new_url and new_url != old_url:
                cur.execute(
                    "UPDATE video SET url = %s WHERE video_id = %s",
                    (new_url, video['video_id'])
                )
                stats["video_urls"] += 1
                print(f"✓ Video {video['video_id']} url: {old_url} -> {new_url}")
        
        # 3. Clean video paths (convert to relative paths)
        cur.execute("SELECT video_id, path FROM video WHERE path IS NOT NULL")
        video_paths = cur.fetchall()
        
        for video in video_paths:
            old_path = video['path']
            # Extract just the filename for the path column too
            if old_path and ('\\' in old_path or '/' in old_path):
                filename = old_path.replace('\\', '/').split('/')[-1]
                new_path = f"uploads/videos/{filename}"
                if new_path != old_path:
                    cur.execute(
                        "UPDATE video SET path = %s WHERE video_id = %s",
                        (new_path, video['video_id'])
                    )
                    stats["video_paths"] += 1
                    print(f"✓ Video {video['video_id']} path: {old_path} -> {new_path}")
        
        # 4. Clean match SGF paths
        cur.execute("SELECT match_id, sgf FROM match WHERE sgf IS NOT NULL")
        matches = cur.fetchall()
        
        for match in matches:
            old_sgf = match['sgf']
            if old_sgf and ('\\' in old_sgf or '/' in old_sgf):
                filename = old_sgf.replace('\\', '/').split('/')[-1]
                new_sgf = f"uploads/sgf/{filename}"
                if new_sgf != old_sgf:
                    cur.execute(
                        "UPDATE match SET sgf = %s WHERE match_id = %s",
                        (new_sgf, match['match_id'])
                    )
                    stats["match_sgf"] += 1
                    print(f"✓ Match {match['match_id']} sgf: {old_sgf} -> {new_sgf}")
        
        conn.commit()
        print("\n" + "=" * 50)
        print("✅ CLEANUP COMPLETED")
        print(f"   Video thumbnails: {stats['video_thumbnails']}")
        print(f"   Video URLs: {stats['video_urls']}")
        print(f"   Video paths: {stats['video_paths']}")
        print(f"   Match SGF: {stats['match_sgf']}")
        print("=" * 50 + "\n")
        
        return {
            "message": "Comprehensive URL cleanup completed",
            "stats": stats
        }
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Cleanup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
    finally:
        conn.close()


@app.post("/cleanup-thumbnail-urls")
def cleanup_thumbnail_urls():
    """Clean up all thumbnail URLs in the database (legacy endpoint)"""
    return cleanup_all_urls()

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
    
    # Clean up URLs before returning
    for video in videos:
        if video['thumbnail']:
            video['thumbnail'] = clean_path_for_url(video['thumbnail'])
        if video['url']:
            video['url'] = clean_path_for_url(video['url'])
    
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
    
    # Clean up thumbnail URLs
    for match in matches:
        if match['thumbnail']:
            match['thumbnail'] = clean_path_for_url(match['thumbnail'])
    
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
    if video['url']:
        video['url'] = clean_path_for_url(video['url'])
        
    if video['thumbnail']:
        video['thumbnail'] = clean_path_for_url(video['thumbnail'])

    if video['video_sgf']:
        video['video_sgf'] = clean_path_for_url(video['video_sgf'])
        
    if video['sgf']:
        video['sgf'] = clean_path_for_url(video['sgf'])

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
    if match['sgf']:
        match['sgf'] = clean_path_for_url(match['sgf'])
    
    if match.get('video'):
        match['video'] = clean_path_for_url(match['video'])
    if match.get('thumbnail'):
        match['thumbnail'] = clean_path_for_url(match['thumbnail'])
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
# -----------------------------------------------------------
# CREATE / UPLOAD ROUTES
# -----------------------------------------------------------

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
        video_url = await upload_file(file, VIDEO_DIR)

        # 3. Sauvegarde de la miniature
        thumb_url = None
        if thumbnail:
            thumb_url = await upload_file(thumbnail, THUMBNAIL_DIR)

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
        video_url,
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
        sgf_url = await upload_file(sgf, SGF_DIR)

    # Insert Match record first
    cur.execute("""
        INSERT INTO match (title, style, white_id, black_id, result, date, duration, description, sgf)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING match_id
    """, (title, style, white, black, result, date, duration, description, sgf_url)) # sgf_url is a str
    match_id = cur.fetchone()["match_id"]

    if video:
        # Save video and get URLs
        video_url = await upload_file(video, VIDEO_DIR)

        thumb_url = None
        if thumbnail:
            thumb_url = await upload_file(thumbnail, THUMBNAIL_DIR)
        
        # Insert Video record
        cur.execute("""
            INSERT INTO video (title, path, url, thumbnail, match_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, video_url, video_url, thumb_url, match_id))
        
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
        sgf_url = upload_file(sgf, SGF_DIR)

    cur.execute("""
        INSERT INTO match (title, style, white_id, black_id, result, date, duration, description, sgf)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING match_id
    """, (title, style, white, black, result, date, duration, description, sgf_url))
    match_id = cur.fetchone()["match_id"]

    if video:
        video_url = upload_file(video, VIDEO_DIR)

        thumb_url = None
        if thumbnail:
            thumb_url = upload_file(thumbnail, THUMBNAIL_DIR)
        
        cur.execute("""
            INSERT INTO video (title, path, url, thumbnail, match_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, video_url, video_url, thumb_url, match_id))

    elif video_id:
        cur.execute("UPDATE video SET match_id = %s WHERE video_id = %s", (match_id, video_id))

    conn.commit()
    conn.close()
    return {"message": "Match created", "match_id": match_id}

@app.post("/generate_sgf_from_video")
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
        response = requests.post(ANALYSE_SERVICE_URL, json={"video_url": os.path.basename(video_url)}, timeout=300)
        response.raise_for_status()
        sgf_content = response.json().get("sgf")
        
        if not sgf_content:
            raise HTTPException(status_code=500, detail="SGF generation failed")
        
        # Save SGF to file
        sgf_url = upload_file_from_content("video_{video_id}.sgf", sgf_content, SGF_DIR)
        
        # Update database
        cur.execute("UPDATE match SET sgf = %s WHERE match_id = %s", (sgf_url, video['match_id']))
        conn.commit()
        conn.close()
        
        return {"message": "SGF generated and saved", "sgf_url": sgf_url}
    
    except requests.RequestException as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Analyse module error: {str(e)}")

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
def edit_video(
    video_id: int,
    title: Optional[str] = Form(None),
    match_id: Optional[int] = Form(None),
    thumbnail: Optional[UploadFile] = File(None)
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
        thumb_url = upload_file(thumbnail, THUMBNAIL_DIR)

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

    conn.commit()
    conn.close()

    # Return updated result
    return get_video(video_id)

@app.post("/match/{match_id}/edit")
def edit_match(
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
        sgf_path = upload_file(sgf, SGF_DIR)

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
        video_url = upload_file(video, VIDEO_DIR)

        cur.execute("""
            INSERT INTO video (title, path, url, thumbnail)
            VALUES (%s, %s, %s, %s)
            RETURNING video_id
        """, (title, video_url, video_url, None))

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
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO match (title, style, white_id, black_id, description, date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING match_id
    """, (title, style, white, black, description, datetime.now()))
    match_id = cur.fetchone()["match_id"]
    cur.execute("""
        INSERT INTO stream (url, match_id)
        VALUES (%s, %s)
    """, (url, match_id))
    conn.commit()
    conn.close()
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
            s.stream_id, s.url,
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
        response = requests.post("http://analyse:5000/process", json={"filename": os.path.basename(video_url)}, timeout=300)
        sgf_content: str = response.json().get("sgf")
        
        if not sgf_content:
            raise HTTPException(status_code=500, detail="SGF generation failed")
        
        # Save SGF to file
        sgf_url = upload_file_from_content("video_{video_id}.sgf", sgf_content.encode('utf-8'), SGF_DIR)
        
        # Update database if video is linked to a match
        if video['match_id']:
            cur.execute("UPDATE match SET sgf = %s WHERE match_id = %s", (sgf_url, video['match_id']))
            conn.commit()
        
        conn.close()
        return {"message": "SGF generated and saved", "sgf": sgf_url}
    
    except requests.RequestException as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Analyse module error: {str(e)}")
