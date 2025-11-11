from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import psycopg2
import os
from datetime import datetime
from pathlib import Path
import shutil
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ton front React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = "postgresql://postgres:15370@localhost:5432/postgres"  # change le nom de la base si besoin

@app.get("/tables")
def get_tables():
    try:
        conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cur.fetchall()
        conn.close()
        return {"tables": [t[0] for t in tables]}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/joueurs")
def get_joueurs():
    try:
        conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
        cur = conn.cursor()
        # Utiliser les guillemets doubles pour respecter la majuscule
        cur.execute('SELECT * FROM "Joueur";')
        rows = cur.fetchall()
        conn.close()
        return {"joueurs": rows}
    except Exception as e:
        return {"error": str(e)}

# Normalisation simple pour éviter les doublons
def normalize_name(name: str) -> str:
    return name.strip().title()  # "lee sedol" → "Lee Sedol"


# -----------------------------
# 1) AUTOCOMPLÉTION DES JOUEURS
# -----------------------------
@app.get("/search_joueurs")
def search_joueurs(q: str):
    conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
    cur = conn.cursor()

    q_norm = q.strip().title()

    cur.execute("""
        SELECT "Joueur_Id", "prénom", "Nom"
        FROM "Joueur"
        WHERE "prénom" ILIKE %s OR "Nom" ILIKE %s
        ORDER BY "Nom" ASC
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
@app.post("/joueurs")
def create_joueur(
    prénom: str = Form(...),
    nom: str = Form(...),
    niveau: str = Form(None)
):
    prénom_norm = normalize_name(prénom)
    nom_norm = normalize_name(nom)
    conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
    cur = conn.cursor()

    cur.execute("""
        SELECT "Joueur_Id"
        FROM "Joueur"
        WHERE "prénom" = %s AND "Nom" = %s
    """, (prénom_norm, nom_norm))

    # Création du joueur
    cur.execute("""
        INSERT INTO "Joueur" ("prénom", "Nom", "Niveau")
        VALUES (%s, %s, %s)
        RETURNING joueur_id
    """, (prénom_norm, nom_norm, niveau))

    Joueur_Id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"id": Joueur_Id, "prénom": prénom_norm, "nom": nom_norm}
# -----------------------------
# CRÉATION D'UNE PARTIE (CORRIGÉ)
# -----------------------------
@app.post("/parties")
def create_partie(
    blanc_id: int = Form(...),
    noir_id: int = Form(...),
    date: str = Form(...),  # Format: "YYYY-MM-DD" ou "YYYY-MM-DD HH:MM:SS"
    victoire: str = Form(None),  # Ex: "blanc", "noir", "nul"
    durée: int = Form(None),  # Durée en minutes
    sgf: str = Form(None),  # Fichier SGF en texte
    description: str = Form(None)
):
    """
    Crée une nouvelle partie entre deux joueurs
    """
    conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
    cur = conn.cursor()
    
    try:
        # Vérifier que les joueurs existent
        cur.execute('SELECT "Joueur_Id" FROM "Joueur" WHERE "Joueur_Id" = %s', (blanc_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Joueur blanc {blanc_id} non trouvé")
        
        cur.execute('SELECT "Joueur_Id" FROM "Joueur" WHERE "Joueur_Id" = %s', (noir_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Joueur noir {noir_id} non trouvé")
        
        # Parser la date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Format de date invalide. Utilisez YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS"
                )
        
        # ⭐ CORRECTION : Ne pas spécifier partie_id, laisser PostgreSQL le générer
        # Utiliser DEFAULT pour les colonnes optionnelles
        cur.execute("""
            INSERT INTO "partie" (blanc_id, noir_id, victoire, date, durée, sgf, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING partie_id
        """, (blanc_id, noir_id, victoire, date_obj, durée, sgf, description))
        
        partie_id = cur.fetchone()[0]
        
        conn.commit()
        
        return {
            "partie_id": partie_id,
            "blanc_id": blanc_id,
            "noir_id": noir_id,
            "date": date_obj.isoformat(),
            "victoire": victoire,
            "durée": durée,
            "message": "Partie créée avec succès"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    
    finally:
        cur.close()
        conn.close()



# -----------------------------
# RÉCUPÉRER TOUTES LES PARTIES
# -----------------------------
@app.get("/parties")
def get_parties():
    """
    Retourne toutes les parties avec les noms des joueurs
    """
    conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                p."partie_Id", 
                p.date, 
                p.victoire,
                p.durée,
                p.description,
                jb."prénom" as blanc_prénom, 
                jb."Nom" as blanc_nom,
                jn."prénom" as noir_prénom,
                jn."Nom" as noir_nom
            FROM "partie" p
            LEFT JOIN "Joueur" jb ON p.blanc_id = jb."Joueur_Id"
            LEFT JOIN "Joueur" jn ON p.noir_id = jn."Joueur_Id"
            ORDER BY p.date DESC
        """)
        
        parties = cur.fetchall()
        
        result = []
        for partie in parties:
            result.append({
                "partie_id": partie[0],
                "date": partie[1].isoformat() if partie[1] else None,
                "victoire": partie[2],
                "durée": partie[3],
                "description": partie[4],
                "blanc": f"{partie[5]} {partie[6]}" if partie[5] else None,
                "noir": f"{partie[7]} {partie[8]}" if partie[7] else None
            })
        
        return {"parties": result, "count": len(result)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    
    finally:
        cur.close()
        conn.close()


# -----------------------------
# RÉCUPÉRER UNE PARTIE SPÉCIFIQUE
# -----------------------------
@app.get("/parties/{partie_id}")
def get_partie(partie_id: int):
    """
    Retourne les détails complets d'une partie avec ses vidéos
    """
    conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
    cur = conn.cursor()
    
    try:
        # Récupérer la partie avec les infos des joueurs
        cur.execute("""
            SELECT 
                p.partie_id, 
                p.date, 
                p.victoire,
                p.durée,
                p.sgf,
                p.description,
                p.blanc_id,
                p.noir_id,
                jb."prénom" as blanc_prénom, 
                jb."Nom" as blanc_nom,
                jn."prénom" as noir_prénom,
                jn."Nom" as noir_nom
            FROM "partie" p
            LEFT JOIN "Joueur" jb ON p.blanc_id = jb."Joueur_Id"
            LEFT JOIN "Joueur" jn ON p.noir_id = jn."Joueur_Id"
            WHERE p.partie_id = %s
        """, (partie_id,))
        
        partie = cur.fetchone()
        
        if not partie:
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        # Récupérer les vidéos associées
        cur.execute("""
            SELECT video_id, titre, chemin, date_upload
            FROM "Video"
            WHERE partie_id = %s
            ORDER BY date_upload DESC
        """, (partie_id,))
        
        videos = cur.fetchall()
        
        return {
            "partie_id": partie[0],
            "date": partie[1].isoformat() if partie[1] else None,
            "victoire": partie[2],
            "durée": partie[3],
            "sgf": partie[4],
            "description": partie[5],
            "blanc": {
                "id": partie[6],
                "nom_complet": f"{partie[8]} {partie[9]}" if partie[8] else None
            },
            "noir": {
                "id": partie[7],
                "nom_complet": f"{partie[10]} {partie[11]}" if partie[10] else None
            },
            "videos": [
                {
                    "video_id": v[0],
                    "titre": v[1],
                    "chemin": v[2],
                    "url": f"/uploads/{v[2]}",
                    "date_upload": v[3].isoformat() if v[3] else None
                }
                for v in videos
            ],
            "videos_count": len(videos)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    
    finally:
        cur.close()
        conn.close()


# -----------------------------
# METTRE À JOUR UNE PARTIE
# -----------------------------
@app.put("/parties/{partie_id}")
def update_partie(
    partie_id: int,
    victoire: str = Form(None),
    durée: int = Form(None),
    sgf: str = Form(None),
    description: str = Form(None)
):
    """
    Met à jour les informations d'une partie
    """
    conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
    cur = conn.cursor()
    
    try:
        # Vérifier que la partie existe
        cur.execute('SELECT partie_id FROM "partie" WHERE partie_id = %s', (partie_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        # Construire la requête de mise à jour dynamiquement
        updates = []
        params = []
        
        if victoire is not None:
            updates.append("victoire = %s")
            params.append(victoire)
        
        if durée is not None:
            updates.append("durée = %s")
            params.append(durée)
        
        if sgf is not None:
            updates.append("sgf = %s")
            params.append(sgf)
        
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if not updates:
            return {"message": "Aucune modification à effectuer"}
        
        params.append(partie_id)
        query = f'UPDATE "partie" SET {", ".join(updates)} WHERE "partie_Id" = %s'
        
        cur.execute(query, params)
        conn.commit()
        
        return {
            "partie_Id": partie_id,
            "message": "Partie mise à jour avec succès",
            "updated_fields": len(updates)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    
    finally:
        cur.close()
        conn.close()
# -----------------------------
# UPLOAD UNE VIDÉO
# -----------------------------
# Configuration
UPLOAD_DIR = Path("uploads/videos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Monter le dossier pour servir les vidéos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
@app.post("/upload_video")
async def upload_video(
    file: UploadFile = File(...),
    titre: str = Form(...),
    partie_Id: int = Form(...)
):
    """
    Upload une vidéo et l'enregistre dans la base de données
    """
    # Validation du type de fichier
    allowed_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Format non supporté. Utilisez: {', '.join(allowed_extensions)}"
        )
    
    conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
    cur = conn.cursor()
    
    try:
        # Vérifier que la partie existe
        cur.execute('SELECT "partie_Id" FROM "partie" WHERE "partie_Id" = %s', (partie_Id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        # Créer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_titre = "".join(c for c in titre if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_titre = safe_titre.replace(' ', '_')[:50]  # Limiter la longueur
        
        filename = f"{safe_titre}_{timestamp}{file_ext}"
        
        # Organiser par date (optionnel mais recommandé)
        date_folder = datetime.now().strftime("%Y/%m")
        full_dir = UPLOAD_DIR / date_folder
        full_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = full_dir / filename
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Chemin relatif pour la base de données
        relative_path = f"videos/{date_folder}/{filename}"
        
        # Insérer dans la base de données
        cur.execute("""
            INSERT INTO "Video" ("titre", "chemin", "partie_Id", "date_upload")
            VALUES (%s, %s, %s, %s)
            RETURNING "video_Id"
        """, (titre, relative_path, partie_id, datetime.now()))
        
        video_id = cur.fetchone()[0]
        
        conn.commit()
        
        return {
            "video_id": video_id,
            "titre": titre,
            "chemin": relative_path,
            "url": f"/uploads/{relative_path}",
            "message": "Vidéo uploadée avec succès"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        # Supprimer le fichier si l'insertion échoue
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    
    finally:
        cur.close()
        conn.close()


# -----------------------------
# RÉCUPÉRER TOUTES LES VIDÉOS 
# -----------------------------
@app.get("/videos")
def get_videos():
    """
    Retourne toutes les vidéos avec leurs URLs complètes
    """
    conn = psycopg2.connect("postgresql://postgres:15370@localhost:5432/postgres")
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT v."video_Id", v."titre", v."chemin", v."partie_Id", v."date_upload",
                   p.date as partie_date
            FROM "Video" v
            LEFT JOIN "partie" p ON v."partie_Id" = p.partie_id
            ORDER BY v."date_upload" DESC
        """)
        
        videos = cur.fetchall()
        
        result = []
        for video in videos:
            result.append({
                "video_id": video[0],
                "titre": video[1],
                "chemin": video[2],
                "url": f"/uploads/{video[2]}",
                "partie_id": video[3],
                "date_upload": video[4].isoformat() if video[4] else None,
                "partie_date": video[5].isoformat() if video[5] else None
            })
        
        return {"videos": result, "count": len(result)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    
    finally:
        cur.close()
        conn.close()