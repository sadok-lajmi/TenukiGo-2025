import psycopg2
from datetime import datetime, timezone

# --- Configuration ---
DB_URL = "postgresql://go_user:secret@localhost:5432/go_db"


def db():
    return psycopg2.connect(DB_URL)

def get_or_create_joueur(cur, prenom, nom, niveau=None):
    # Vérifier existence
    cur.execute("""
        SELECT joueur_id
        FROM joueurs
        WHERE prenom=%s AND nom=%s
    """, (prenom, nom))
    
    row = cur.fetchone()
    if row:
        return row[0] #renvoie l'id du joueur

    # Sinon créer
    cur.execute("""
        INSERT INTO joueurs (prenom, nom, niveau)
        VALUES (%s, %s, %s)
        RETURNING joueur_id
    """, (prenom, nom, niveau))

    return cur.fetchone()[0] #renvoie l'id du joueur


# Normalisation simple pour éviter les doublons
def normalize_name(name: str) -> str:
    return name.strip().title()  


def process_and_save_game(data: dict) -> dict:
    """Fonction synchrone qui gère la logique de la base de données."""
    conn = None
    try:
        blanc_nom = data.get("blanc_nom", "Joueur").strip().title()
        blanc_prenom = data.get("blanc_prenom", "Blanc").strip().title()
        noir_nom = data.get("noir_nom", "Joueur").strip().title()
        noir_prenom = data.get("noir_prenom", "Noir").strip().title()
        sgf_content = data.get("sgf_content", "(;GM[1])")

        conn = db()
        cur = conn.cursor()

        # --- Gérer Joueur Blanc ---
        cur.execute(
            "SELECT joueur_id FROM joueurs WHERE prénom = %s AND nom_de_famille = %s",
            (blanc_prenom, blanc_nom)
        )
        blanc_row = cur.fetchone()
        if blanc_row:
            blanc_id = blanc_row[0]
        else:
            cur.execute(
                "INSERT INTO joueurs (prénom, nom_de_famille) VALUES (%s, %s) RETURNING joueur_id",
                (blanc_prenom, blanc_nom)
            )
            blanc_id = cur.fetchone()[0]

        # --- Gérer Joueur Noir ---
        cur.execute(
            "SELECT joueur_id FROM joueurs WHERE prénom = %s AND nom_de_famille = %s",
            (noir_prenom, noir_nom)
        )
        noir_row = cur.fetchone()
        if noir_row:
            noir_id = noir_row[0]
        else:
            cur.execute(
                "INSERT INTO joueurs (prénom, nom_de_famille) VALUES (%s, %s) RETURNING joueur_id",
                (noir_prenom, noir_nom)
            )
            noir_id = cur.fetchone()[0]
        
        # --- Insérer la partie ---
        cur.execute("""
            INSERT INTO parties (style, blanc_id, noir_id, date, sgf, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING partie_id
        """, ("amicale", blanc_id, noir_id, datetime.now(timezone.utc), sgf_content, "Partie live (broadcast)"))
        
        partie_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"SUCCÈS: Partie {partie_id} insérée en BDD.")
        
        # Retourner les données à diffuser
        return {
            "status": "succes",
            "partie_id": partie_id,
            "sgf_content": sgf_content,
            "joueur_blanc": f"{blanc_prenom} {blanc_nom}",
            "joueur_noir": f"{noir_prenom} {noir_nom}"
        }
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Erreur lors de l'insertion DB: {error}")
        if conn: conn.rollback()
        raise error
    finally:
        if conn:
            cur.close()
            conn.close()