from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from datetime import datetime
import requests

from api.utils.db_services import db
from api.utils.file_storage import save_file_from_content
from config.settings import (
    SGF_DIR,
    ANALYSIS_SERVICE_URL,
    WS_STREAMING_URL,
    MEDIAMTX_RTSP_URL,
    MEDIAMTX_HLS_URL
)

router = APIRouter()

@router.get("/streams")
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

@router.get("/stream/{stream_id}")
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

@router.post("/stream/create")
def create_stream(
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
        INSERT INTO stream (url, match_id, date)
        VALUES (%s, %s, %s)
        RETURNING stream_id
    """, (url, match_id, datetime.now()))
    stream_id = cur.fetchone()["stream_id"]

    sgf_path = save_file_from_content(
        f"stream_{stream_id}.sgf", 
        "".encode('utf-8'), 
        SGF_DIR
    )
    cur.execute("""
        UPDATE match
        SET sgf = %s
        WHERE match_id = %s
    """, (sgf_path, match_id))

    conn.commit()
    conn.close()    

    return {"message": "Stream created", "stream_id": stream_id}

@router.post("/stream/{stream_id}/start-analysis")
def start_stream(stream_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT match_id, url FROM stream WHERE stream_id = %s", (stream_id,))
    stream = cur.fetchone()
    conn.close()

    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    match_id = stream["match_id"]
    rtsp_url = MEDIAMTX_RTSP_URL + stream["url"].removeprefix(MEDIAMTX_HLS_URL).removesuffix("/index.m3u8")

    try:
        requests.post(ANALYSIS_SERVICE_URL + "/stream/start", 
                      json={"rtsp_url": rtsp_url, "match_id": match_id, "ws_url": WS_STREAMING_URL + f"/{match_id}"}, 
                      timeout=10)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to start stream analysis: {str(e)}")

    return {"message": "Stream analysis started"}

@router.post("/stream/{stream_id}/stop-analysis")
def stop_stream(stream_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT match_id FROM stream WHERE stream_id = %s", (stream_id,))
    stream = cur.fetchone()
    conn.close()

    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    match_id = stream["match_id"]

    try:
        requests.post(ANALYSIS_SERVICE_URL + "/stream/stop", 
                      json={"match_id": match_id}, 
                      timeout=10)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop stream analysis: {str(e)}")

    return {"message": "Stream analysis stopped"}