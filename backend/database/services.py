import psycopg2
from datetime import datetime, timezone
from config.settings import DB_URL
from psycopg2.extras import RealDictCursor

def db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def normalize_name(name: str) -> str:
    return name.strip().title()

def get_or_create_player(cur, firstname, lastname, level=None):
    cur.execute("""
        SELECT player_id FROM player
        WHERE firstname=%s AND lastname=%s
    """, (firstname, lastname))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        INSERT INTO player (firstname, lastname, level)
        VALUES (%s, %s, %s)
        RETURNING player_id
    """, (firstname, lastname, level))
    return cur.fetchone()[0]

def process_and_save_game(data: dict) -> dict:
    """Insert a Go game into the DB using the SQL schema."""
    conn = None
    try:
        white_firstname = normalize_name(data.get("blanc_prenom", "Blanc"))
        white_lastname = normalize_name(data.get("blanc_nom", "Joueur"))
        black_firstname = normalize_name(data.get("noir_prenom", "Noir"))
        black_lastname = normalize_name(data.get("noir_nom", "Joueur"))
        sgf_content = data.get("sgf_content", "(;GM[1])")

        conn = db()
        cur = conn.cursor()

        # --- Create or get players ---
        white_id = get_or_create_player(cur, white_firstname, white_lastname)
        black_id = get_or_create_player(cur, black_firstname, black_lastname)

        # --- Insert match ---
        cur.execute("""
            INSERT INTO match (title, style, white_id, black_id, date, sgf, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING match_id
        """, (
            f"{white_firstname} vs {black_firstname}",
            "friendly",
            white_id,
            black_id,
            datetime.now(timezone.utc),
            sgf_content,
            "Partie live (broadcast)"
        ))

        match_id = cur.fetchone()[0]
        conn.commit()

        print(f"SUCCÈS: Match {match_id} inséré en BDD.")

        return {
            "status": "success",
            "match_id": match_id,
            "sgf_content": sgf_content,
            "player_white": f"{white_firstname} {white_lastname}",
            "player_black": f"{black_firstname} {black_lastname}"
        }

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Erreur lors de l'insertion DB: {error}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()
