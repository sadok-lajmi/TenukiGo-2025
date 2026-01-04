"""
API routes for managing players.
"""

from fastapi import APIRouter, HTTPException, Form
from typing import Optional

from api.utils.db_services import db

router = APIRouter()

@router.get("/players")
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

@router.get("/player/{player_id}")
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

@router.post("/player/create")
def create_player(
    firstname: str = Form(...),
    lastname: str = Form(...),
    level: Optional[str] = Form(None)
):
    conn = db()
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

@router.post("/player/{player_id}/edit")
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

@router.delete("/player/{player_id}/delete")
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