from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import psycopg2
import os
from datetime import datetime
from pathlib import Path
import shutil
from fastapi.middleware.cors import CORSMiddleware
from services import get_or_create_joueur, normalize_name


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ton front React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#DB_URL = "postgresql://postgres:15370@localhost:5432/postgres"  # change le nom de la base si besoin
DB_URL = "postgresql://go_user:secret@localhost:5432/go_db"

#dossier d'upload video 
path=r"C:\Users\samue\Documents\Cours\cours IMT atlantique\A2\commande entreprise\videos"
videoS_DIR = Path(path)

# Création des dossiers si absents
videoS_DIR.mkdir(parents=True, exist_ok=True)

# Fonction pour créer une connexion PostgreSQL
def db():
    return psycopg2.connect(DB_URL)


@app.get("/tables")
def get_tables():
    try:
        conn = db()
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
        conn = db()
        cur = conn.cursor()
        # Utiliser les guillemets doubles pour respecter la majuscule
        cur.execute('SELECT * FROM "joueurs";')
        rows = cur.fetchall()
        conn.close()
        return {"joueurs": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------
# 1) AUTOCOMPLÉTION DES JOUEURS
# -----------------------------
@app.get("/search_joueurs")
def search_joueurs(q: str):
    conn = db()
    cur = conn.cursor()

    q_norm = q.strip().title()

    cur.execute("""
        SELECT "joueur_id", "prenom", "nom"
        FROM "joueurs"
        WHERE "prenom" ILIKE %s OR "nom" ILIKE %s
        ORDER BY "nom" ASC
        LIMIT 15
    """, (f"%{q_norm}%", f"%{q_norm}%"))

    joueurs = [
        {"id": row[0], "prenom": row[1], "nom": row[2], "full": f"{row[1]} {row[2]}"}
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()
    return joueurs


# -----------------------------
# 2) CRÉATION D'UN joueur
# -----------------------------
@app.post("/joueurs")
def create_joueur(
    prenom: str = Form(...),
    nom: str = Form(...),
    niveau: str = Form(None)
):
    prenom_norm = normalize_name(prenom)
    nom_norm = normalize_name(nom)
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT "joueur_id"
        FROM "joueurs"
        WHERE "prenom" = %s AND "nom" = %s
    """, (prenom_norm, nom_norm))

    # Création du joueur
    cur.execute("""
        INSERT INTO "joueurs" ("prenom", "nom", "niveau")
        VALUES (%s, %s, %s)
        RETURNING joueur_id
    """, (prenom_norm, nom_norm, niveau))

    joueur_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"id": joueur_id, "prenom": prenom_norm, "nom": nom_norm}
# -----------------------------
# CRÉATION D'UNE PARTIE (CORRIGÉ)
# -----------------------------
@app.post("/parties")
def create_partie(
    blanc_prenom: str = Form(...),
    blanc_nom: str = Form(...),           
    noir_prenom: str = Form(...),
    noir_nom: str = Form(...),
    niveau_blanc: str = Form(None),
    niveau_noir: str = Form(None),
    date: str = Form(None),  # Format: "YYYY-MM-DD" ou "YYYY-MM-DD HH:MM:SS"
    victoire: str = Form(None),  # Ex: "blanc", "noir", "nul"
    duree: int = Form(None),  # Durée en minutes
    sgf: str = Form(None),  # Fichier SGF en texte
    description: str = Form(None)
):
    

     # Normalisation des noms
    bp = normalize_name(blanc_prenom)
    bn = normalize_name(blanc_nom)
    np = normalize_name(noir_prenom)
    nn = normalize_name(noir_nom)

    """
    Crée une nouvelle partie entre deux joueurs
    """
    conn = db()
    cur = conn.cursor()
    
    try:
        #Créer ou trouver joueur blanc
        blanc_id = get_or_create_joueur(cur, bp, bn, niveau_blanc)

        # Créer ou trouver joueur noir
        noir_id = get_or_create_joueur(cur, np, nn, niveau_noir)
        
        # Si aucune date fournie → on met maintenant()
        if not date or date.strip() == "":
            date_obj = datetime.now()
        else:
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
            INSERT INTO "parties" (blanc_id, noir_id, victoire, date, duree, sgf, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING partie_id
        """, (blanc_id, noir_id, victoire, date_obj, duree, sgf, description))
        
        partie_id = cur.fetchone()[0]
        
        conn.commit()
        
        return {
            "partie_id": partie_id,
            "blanc_id": blanc_id,
            "noir_id": noir_id,
            "date": date_obj.isoformat(),
            "victoire": victoire,
            "duree": duree,
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
    conn = db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                p."partie_id", 
                p.date, 
                p.victoire,
                p.duree,
                p.description,
                jb."prenom" as blanc_prenom, 
                jb."nom" as blanc_nom,
                jn."prenom" as noir_prenom,
                jn."nom" as noir_nom
            FROM "parties" p
            LEFT JOIN "joueurs" jb ON p.blanc_id = jb."joueur_id"
            LEFT JOIN "joueurs" jn ON p.noir_id = jn."joueur_id"
            ORDER BY p.date DESC
        """)
        
        parties = cur.fetchall()
        
        result = []
        for partie in parties:
            result.append({
                "partie_id": partie[0],
                "date": partie[1].isoformat() if partie[1] else None,
                "victoire": partie[2],
                "duree": partie[3],
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
    conn = db()
    cur = conn.cursor()
    
    try:
        # Récupérer la partie avec les infos des joueurs
        cur.execute("""
            SELECT 
                p.partie_id, 
                p.date, 
                p.victoire,
                p.duree,
                p.sgf,
                p.description,
                p.blanc_id,
                p.noir_id,
                jb."prenom" as blanc_prenom, 
                jb."nom" as blanc_nom,
                jn."prenom" as noir_prenom,
                jn."nom" as noir_nom
            FROM "parties" p
            LEFT JOIN "joueurs" jb ON p.blanc_id = jb."joueur_id"
            LEFT JOIN "joueurs" jn ON p.noir_id = jn."joueur_id"
            WHERE p.partie_id = %s
        """, (partie_id,))
        
        partie = cur.fetchone()
        
        if not partie:
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        # Récupérer les vidéos associées
        cur.execute("""
            SELECT video_id, titre, chemin, date_upload
            FROM "video"
            WHERE partie_id = %s
            ORDER BY date_upload DESC
        """, (partie_id,))
        
        videos = cur.fetchall()
        
        return {
            "partie_id": partie[0],
            "date": partie[1].isoformat() if partie[1] else None,
            "victoire": partie[2],
            "duree": partie[3],
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
    duree: int = Form(None),
    sgf: str = Form(None),
    description: str = Form(None)
):
    """
    Met à jour les informations d'une partie
    """
    conn = db()
    cur = conn.cursor()
    
    try:
        # Vérifier que la partie existe
        cur.execute('SELECT partie_id FROM "parties" WHERE partie_id = %s', (partie_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        # Construire la requête de mise à jour dynamiquement
        updates = []
        params = []
        
        if victoire is not None:
            updates.append("victoire = %s")
            params.append(victoire)
        
        if duree is not None:
            updates.append("duree = %s")
            params.append(duree)
        
        if sgf is not None:
            updates.append("sgf = %s")
            params.append(sgf)
        
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if not updates:
            return {"message": "Aucune modification à effectuer"}
        
        params.append(partie_id)
        query = f'UPDATE "parties" SET {", ".join(updates)} WHERE "partie_id" = %s'
        
        cur.execute(query, params)
        conn.commit()
        
        return {
            "partie_id": partie_id,
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

# Monter le dossier pour servir les vidéos
app.mount("/videos", StaticFiles(directory=videoS_DIR), name="videos")

@app.post("/upload_video")
async def upload_video(
    file: UploadFile = File(...),
    titre: str = Form(...),
    partie_id: int = Form(...)
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
    
    conn = db()
    cur = conn.cursor()
    
    try:
        # Vérifier que la partie existe
        cur.execute('SELECT "partie_id" FROM "parties" WHERE "partie_id" = %s', (partie_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        # Créer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_titre = "".join(c for c in titre if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_titre = safe_titre.replace(' ', '_')[:50]  # Limiter la longueur
        
        filename = f"{safe_titre}_{timestamp}{file_ext}"
        
        # Organiser par date (optionnel mais recommandé)
        date_folder = datetime.now().strftime("%Y/%m")
        full_dir = videoS_DIR / date_folder
        full_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = full_dir / filename
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Chemin relatif pour la base de données
        relative_path = f"{date_folder}/{filename}"
        
        # Insérer dans la base de données
        cur.execute("""
            INSERT INTO "video" ("titre", "chemin", "partie_id", "date_upload")
            VALUES (%s, %s, %s, %s)
            RETURNING "video_id"
        """, (titre, relative_path, partie_id, datetime.now()))
        
        video_id = cur.fetchone()[0]
        
        conn.commit()
        
        return {
            "video_id": video_id,
            "titre": titre,
            "chemin": relative_path,
            "url": f"/videos/{relative_path}",
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
    conn = db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT v."video_id", v."titre", v."chemin", v."partie_id", v."date_upload",
                   p.date as partie_date
            FROM "video" v
            LEFT JOIN "parties" p ON v."partie_id" = p.partie_id
            ORDER BY v."date_upload" DESC
        """)
        
        videos = cur.fetchall()
        
        result = []
        for video in videos:
            result.append({
                "video_id": video[0],
                "titre": video[1],
                "chemin": video[2],
                "url": f"/videos/{video[2]}",
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