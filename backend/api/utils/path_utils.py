def clean_path_for_url(file_path: str) -> str:
    """Convert file system path to web URL path"""
    if not file_path:
        return None  # Retourne None au lieu d'une chaîne vide
    
    # Si c'est déjà une URL correcte, la retourner
    if file_path.startswith('/uploads/') or file_path.startswith('http'):
        return file_path
    
    # Convertir les backslashes en forward slashes
    cleaned = file_path.replace('\\', '/')
    
    # Extraire juste le nom de fichier
    if '/' in cleaned:
        filename = cleaned.split('/')[-1]
    else:
        filename = cleaned
    
    # Déterminer le bon sous-dossier basé sur l'extension ou le contenu du chemin
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
        return f"/uploads/thumbnails/{filename}"
    elif ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
        return f"/uploads/videos/{filename}"
    elif ext in ['sgf']:
        return f"/uploads/sgf/{filename}"
    elif 'thumbnail' in file_path.lower():
        return f"/uploads/thumbnails/{filename}"
    elif 'video' in file_path.lower():
        return f"/uploads/videos/{filename}"
    elif 'sgf' in file_path.lower():
        return f"/uploads/sgf/{filename}"
    else:
        return f"/uploads/{filename}"