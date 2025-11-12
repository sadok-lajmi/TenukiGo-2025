-- ------------------------------------------------
-- Tables
-- ------------------------------------------------

-- Table joueurs
CREATE TABLE joueurs (
    joueur_id SERIAL PRIMARY KEY,
    prenom VARCHAR(100),
    nom VARCHAR(100),
    niveau VARCHAR(20)
);

-- Table parties
CREATE TABLE parties (
    partie_id SERIAL PRIMARY KEY,
    style VARCHAR(50), -- "tournoi","amicale","pedagogique"
    blanc_id INTEGER,  -- FK vers joueurs
    noir_id INTEGER,   -- FK vers joueurs
    victoire VARCHAR(20), -- "blanc","noir","nulle","pedagogique"
    date TIMESTAMP,
    duree INTEGER,
    sgf TEXT,
    description TEXT,
    FOREIGN KEY (blanc_id) REFERENCES joueurs(joueur_id) ON DELETE SET NULL,
    FOREIGN KEY (noir_id) REFERENCES joueurs(joueur_id) ON DELETE SET NULL
);

-- Table video (1-1 avec parties via partie_id unique)
CREATE TABLE video (
    video_id SERIAL PRIMARY KEY,
    titre VARCHAR(200),
    description TEXT,
    chemin TEXT, -- chemin local ou URL
    partie_id INTEGER NOT NULL UNIQUE, -- garantit 1-1 : une vidéo → une partie
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partie_id) REFERENCES parties(partie_id) ON DELETE CASCADE
);


-- ------------------------------------------------
-- Indexes utiles
-- ------------------------------------------------
CREATE INDEX idx_parties_blanc_id ON parties(blanc_id);
CREATE INDEX idx_parties_noir_id ON parties(noir_id);
CREATE INDEX idx_video_partie_id ON video(partie_id);
CREATE INDEX idx_parties_date ON parties(date);
