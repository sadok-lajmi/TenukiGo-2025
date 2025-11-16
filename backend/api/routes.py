from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI(title="Go Game API")

# ======================
# CONFIGURATION
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = "postgresql://postgres:admingo@localhost:5432/Go"

UPLOAD_DIR = Path("uploads")
VIDEO_DIR = UPLOAD_DIR / "videos"
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"

# Create upload directories if they don't exist
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

# Correct way to serve the /uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ======================
# UTILITIES
# ======================
def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def normalize_name(name: str) -> str:
    return name.strip().title()

# -----------------------------------------------------------
# LIST ROUTES
# -----------------------------------------------------------

@app.get("/videos")
def list_videos():
    conn = get_db()
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
    conn = get_db()
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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT player_id, firstname, lastname, level
        FROM player
        ORDER BY lastname
    """)
    players = cur.fetchall()
    conn.close()
    return {"players": players, "count": len(players)}

# -----------------------------------------------------------
# DETAIL ROUTES
# -----------------------------------------------------------

@app.get("/video/{video_id}")
def get_video(video_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            v.video_id, v.title, v.path, v.url, v.thumbnail,
            v.date_upload, v.duration,
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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            m.match_id, m.title, m.result, m.style,
            m.white_id AS white, m.black_id AS black,
            m.duration, m.date,
            v.video_id, v.url AS video, v.thumbnail,
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
    conn = get_db()
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

# -----------------------------------------------------------
# CREATE / UPLOAD ROUTES
# -----------------------------------------------------------

@app.post("/create_player")
def create_player(
    firstname: str = Form(...),
    lastname: str = Form(...),
    level: Optional[str] = Form(None)
):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO player (firstname, lastname, level)
        VALUES (%s, %s, %s)
        RETURNING player_id
    """, (firstname, lastname, level))
    player_id = cur.fetchone()["player_id"]
    conn.commit()
    conn.close()
    return {"message": "Player created", "player_id": player_id}


@app.post("/upload_video")
def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    thumbnail: Optional[UploadFile] = File(None),
    match_id: Optional[int] = Form(None)
):
    filename = f"{datetime.now().timestamp()}_{file.filename}"
    file_path = VIDEO_DIR / filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    thumb_url = None
    if thumbnail:
        thumb_name = f"{datetime.now().timestamp()}_{thumbnail.filename}"
        thumb_path = THUMBNAIL_DIR / thumb_name
        with open(thumb_path, "wb") as f:
            f.write(thumbnail.file.read())
        thumb_url = str(thumb_path)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO video (title, path, url, thumbnail, match_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING video_id
    """, (title, str(file_path), str(file_path), thumb_url, match_id))
    video_id = cur.fetchone()["video_id"]
    conn.commit()
    conn.close()
    return {"message": "Video uploaded", "video_id": video_id}


@app.post("/create_match")
def create_match(
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
    conn = get_db()
    cur = conn.cursor()

    sgf_path = None
    if sgf:
        sgf_path = UPLOAD_DIR / f"{datetime.now().timestamp()}_{sgf.filename}"
        with open(sgf_path, "wb") as f:
            f.write(sgf.file.read())

    cur.execute("""
        INSERT INTO match (title, style, white_id, black_id, result, date, duration, description, sgf, video_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING match_id
    """, (title, style, white, black, result, date, duration, description, str(sgf_path), video_id))
    match_id = cur.fetchone()["match_id"]

    if video:
        vid_name = f"{datetime.now().timestamp()}_{video.filename}"
        vid_path = VIDEO_DIR / vid_name
        with open(vid_path, "wb") as f:
            f.write(video.file.read())

        thumb_path = None
        if thumbnail:
            thumb_name = f"{datetime.now().timestamp()}_{thumbnail.filename}"
            thumb_path = THUMBNAIL_DIR / thumb_name
            with open(thumb_path, "wb") as f:
                f.write(thumbnail.file.read())

        cur.execute("""
            INSERT INTO video (title, path, url, thumbnail, match_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, str(vid_path), str(vid_path), str(thumb_path), match_id))

    elif video_id:
        cur.execute("UPDATE video SET match_id = %s WHERE video_id = %s", (match_id, video_id))

    conn.commit()
    conn.close()
    return {"message": "Match created", "match_id": match_id}

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
    conn = get_db()
    cur = conn.cursor()

    # --- Fetch existing video ---
    cur.execute("SELECT * FROM video WHERE video_id = %s", (video_id,))
    video = cur.fetchone()
    if not video:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")

    # Start with current values
    new_thumbnail = video["thumbnail"]

    # --- Handle thumbnail replacement ---
    if thumbnail:
        thumb_name = f"{datetime.now().timestamp()}_{thumbnail.filename}"
        thumb_path = THUMBNAIL_DIR / thumb_name
        with open(thumb_path, "wb") as f:
            f.write(thumbnail.file.read())
        new_thumbnail = str(thumb_path)

    # --- match_id can be nullable ---
    # match_id == None → remove association
    # match_id given → set new relation

    cur.execute("""
        UPDATE video
        SET
            title = COALESCE(%s, title),
            thumbnail = %s,
            match_id = %s
        WHERE video_id = %s
    """, (
        title,
        new_thumbnail,
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

    # NEW CLEAN INPUTS
    video: Optional[UploadFile] = File(None),
    sgf: Optional[UploadFile] = File(None),
    video_id: Optional[str] = Form(None),  # match selects an existing video
    remove_video: Optional[str] = Form(None),  # explicit removal
    remove_sgf: Optional[str] = Form(None)
):
    conn = get_db()
    cur = conn.cursor()
    # ------------------------------------------------------
    # 1. Load match
    # ------------------------------------------------------
    cur.execute("SELECT * FROM match WHERE match_id = %s", (match_id,))
    match = cur.fetchone()
    if not match:
        raise HTTPException(404, "Match not found")

    old_video_id = match["video_id"]

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
        sgf_path = UPLOAD_DIR / f"{datetime.now().timestamp()}_{sgf.filename}"
        with open(sgf_path, "wb") as f:
            f.write(sgf.file.read())
        sgf_path = str(sgf_path)

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
        cur.execute("UPDATE match SET video_id = NULL WHERE match_id = %s", (match_id,))

    # CASE B — NEW VIDEO UPLOAD
    if video:  
        vid_name = f"{datetime.now().timestamp()}_{video.filename}"
        vid_path = VIDEO_DIR / vid_name

        with open(vid_path, "wb") as f:
            f.write(video.file.read())

        cur.execute("""
            INSERT INTO video (title, path, url, thumbnail)
            VALUES (%s, %s, %s, %s)
            RETURNING video_id
        """, (title, str(vid_path), str(vid_path), None))

        new_video_id = cur.fetchone()["video_id"]

        cur.execute("UPDATE match SET video_id = %s WHERE match_id = %s",
                    (new_video_id, match_id))

    # CASE C — EXISTING VIDEO SELECTED (only if no new upload!)
    elif video_id and video_id != "" and video_id != str(old_video_id):
        cur.execute("UPDATE match SET video_id = %s WHERE match_id = %s",
                    (video_id, match_id))

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
    conn = get_db()
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

