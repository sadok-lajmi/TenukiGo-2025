"""
Database services utilities.
Provides functions to interact with the database.
"""

import psycopg2
from config.settings import settings
from psycopg2.extras import RealDictCursor

def db():
    return psycopg2.connect(settings.DB_URL, cursor_factory=RealDictCursor)

def get_sgf_path(match_id: int) -> str:
    """Returns the SGF path for a given match from the database."""
    cursor = db().cursor()
    cursor.execute("SELECT sgf FROM match WHERE match_id = %s", (match_id,))
    sgf_path = cursor.fetchone()["sgf"]
    cursor.close()
    return sgf_path


