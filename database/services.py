#fichier de fonction utiles pour la base de donnée et les routes


def get_or_create_joueur(cur, prenom, nom, niveau=None):
    # Vérifier existence
    cur.execute("""
        SELECT joueur_id
        FROM joueurs
        WHERE prenom=%s AND nom_de_famille=%s
    """, (prenom, nom))
    
    row = cur.fetchone()
    if row:
        return row[0] #renvoie l'id du joueur

    # Sinon créer
    cur.execute("""
        INSERT INTO joueurs (prenom, nom_de_famille, niveau)
        VALUES (%s, %s, %s)
        RETURNING joueur_id
    """, (prenom, nom, niveau))

    return cur.fetchone()[0] #renvoie l'id du joueur


# Normalisation simple pour éviter les doublons
def normalize_name(name: str) -> str:
    return name.strip().title()  
