import psycopg2
from config.settings import DB_URL
from psycopg2.extras import RealDictCursor

def db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def get_sgf_path(match_id: int) -> str:
    """Returns the SGF path for a given match from the database."""
    cursor = db.cursor()
    cursor.execute("SELECT sgf FROM match WHERE id = ?", (match_id,))
    sgf_url = cursor.fetchone()["sgf"]
    cursor.close()
    if sgf_url[0] == "/":
        sgf_url = sgf_url[1:]
        print(f"Jte l'avais dit !")
    return sgf_url


