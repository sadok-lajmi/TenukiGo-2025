from fastapi import FastAPI, UploadFile, Form, HTTPException
import psycopg2, os

app = FastAPI()
#DB_URL = "postgresql://go_user:secret@localhost:5432/go_db"
DB_URL= "postgresql://go_user:secret@10.129.165.85:5432/go_db"

CLUB_PASSWORD = "clubgo2025"

# Fonction pour créer une connexion PostgreSQL
def db():
    return psycopg2.connect(DB_URL)


# Normalisation simple pour éviter les doublons
def normalize_name(name: str) -> str:
    return name.strip().title()  # "lee sedol" → "Lee Sedol"


# -----------------------------
# 1) AUTOCOMPLÉTION DES JOUEURS
# -----------------------------
@app.get("/search_joueurs")
def search_joueurs(q: str):
    conn = db()
    cur = conn.cursor()

    q_norm = q.strip().title()

    cur.execute("""
        SELECT joueur_id, prenom, nom_de_famille
        FROM joueurs
        WHERE prenom ILIKE %s OR nom_de_famille ILIKE %s
        ORDER BY nom_de_famille ASC
        LIMIT 15
    """, (f"%{q_norm}%", f"%{q_norm}%"))

    joueurs = [
        {"id": row[0], "prénom": row[1], "nom": row[2], "full": f"{row[1]} {row[2]}"}
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()
    return joueurs


# -----------------------------
# 2) CRÉATION D'UN JOUEUR
# -----------------------------
@app.post("/create_joueur")
def create_joueur(
    prénom: str = Form(...),
    nom: str = Form(...),
    niveau: str = Form(None)
):
    prénom_norm = normalize_name(prénom)
    nom_norm = normalize_name(nom)

    conn = db()
    cur = conn.cursor()

    # Vérifier si le joueur existe déjà
    cur.execute("""
        SELECT joueur_id
        FROM joueurs
        WHERE prenom = %s AND nom_de_famille = %s
    """, (prénom_norm, nom_norm))

    existing = cur.fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Ce joueur existe déjà.")

    # Création du joueur
    cur.execute("""
        INSERT INTO joueurs (prenom, nom_de_famille, niveau)
        VALUES (%s, %s, %s)
        RETURNING joueur_id
    """, (prénom_norm, nom_norm, niveau))

    joueur_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"id": joueur_id, "prénom": prénom_norm, "nom": nom_norm}


# -----------------------------
# 3) UPLOAD DE PARTIE
# -----------------------------
@app.post("/upload_partie")
async def upload_partie(
    password: str = Form(...),
    blanc_prenom: str = Form(...),
blanc_nom: str = Form(...),             
    noir_prenom: str = Form(...),
    noir_nom: str = Form(...),
    description: str = Form(""),
    video: UploadFile = Form(None),
    sgf: UploadFile = Form(None)
):
    if password != CLUB_PASSWORD:
        raise HTTPException(status_code=403, detail="Mot de passe incorrect")

    # Normalisation des noms
    bp = normalize_name(blanc_prenom)
    bn = normalize_name(blanc_nom)
    np = normalize_name(noir_prenom)
    nn = normalize_name(noir_nom)

    conn = db()
    cur = conn.cursor()

    # Récupérer joueur blanc
    cur.execute("""
        SELECT joueur_id FROM joueurs
        WHERE prenom=%s AND nom_de_famille=%s
    """, (bp, bn))
    row = cur.fetchone()
    if not row:
        raise HTTPException(400, f"Le joueur blanc '{bp} {bn}' n'existe pas.")
    blanc_id = row[0]

    # Récupérer joueur noir
    cur.execute("""
        SELECT joueur_id FROM joueurs
        WHERE prenom=%s AND nom_de_famille=%s
    """, (np, nn))
    row = cur.fetchone()
    if not row:
        raise HTTPException(400, f"Le joueur noir '{np} {nn}' n'existe pas.")
    noir_id = row[0]

    # Créer la partie
    cur.execute("""
        INSERT INTO parties (style, date, duree, blanc_id, noir_id, victoire, sgf, description)
        VALUES ('classique', CURRENT_DATE, 60, %s, %s, 'blanc', NULL, %s)
        RETURNING partie_id
    """, (blanc_id, noir_id, description))
    partie_id = cur.fetchone()[0]


    # Gestion du fichier uploadé
    os.makedirs("uploads", exist_ok=True)

    # Upload vidéo
    if video:
        ext = os.path.splitext(video.filename)[1]
        if ext.lower() != ".mp4":
            raise HTTPException(400, "La vidéo doit être un fichier .mp4")

        video_path = f"uploads/partie_{partie_id}.mp4"
        with open(video_path, "wb") as f:
            f.write(await video.read())

        cur.execute("""
            INSERT INTO video (titre, chemin, partie_id)
            VALUES (%s, %s, %s)
        """, (f"Partie {partie_id}", video_path, partie_id))

    # Upload SGF
    if sgf:
        ext = os.path.splitext(sgf.filename)[1]
        if ext.lower() != ".sgf":
            raise HTTPException(400, "Le fichier SGF doit être un .sgf")

        sgf_path = f"uploads/partie_{partie_id}.sgf"
        with open(sgf_path, "wb") as f:
            f.write(await sgf.read())

        with open(sgf_path, "r", encoding="utf-8") as s:
            sgf_content = s.read()

        cur.execute("UPDATE parties SET sgf=%s WHERE partie_id=%s", (sgf_content, partie_id))

    conn.commit()
    cur.close()
    conn.close()
    return {"status": "ok", "partie_id": partie_id}

@app.get("/joueurs")
def get_joueurs():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT joueur_id, prenom, nom_de_famille, niveau FROM joueurs")
    joueurs = [{"id": r[0], "prenom": r[1], "nom": r[2], "niveau": r[3]} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return joueurs

    
