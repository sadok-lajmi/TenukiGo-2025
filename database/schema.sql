-- ------------------------------------------------
-- Tables
-- ------------------------------------------------

-- Table player
CREATE TABLE player (
    player_id SERIAL PRIMARY KEY,
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    level VARCHAR(20)
);

-- Table match
CREATE TABLE match (
    match_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    style VARCHAR(50), -- "tournament", "friendly", "educational"
    white_id INTEGER,  -- FK vers player
    black_id INTEGER,  -- FK vers player
    result VARCHAR(20), -- "white", "black", "draw", "educational"
    duration INTEGER,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_id INTEGER, -- FK vers video (optionnel)
    sgf TEXT, -- chemin vers le fichier sgf de la partie
    description TEXT,
    FOREIGN KEY (white_id) REFERENCES player(player_id) ON DELETE SET NULL,
    FOREIGN KEY (black_id) REFERENCES player(player_id) ON DELETE SET NULL,
    FOREIGN KEY (video_id) REFERENCES video(video_id) ON DELETE SET NULL
);

-- Table video (1-1 avec match via match_id unique)
CREATE TABLE video (
    video_id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    path TEXT, -- chemin local
    url TEXT,
    thumbnail TEXT, -- chemin vers la miniature
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration INTEGER,
    match_id INTEGER UNIQUE, -- garantit 1-1 : une vidéo → un match
    FOREIGN KEY (match_id) REFERENCES match(match_id) ON DELETE SET NULL
);

-- Table stream (liée au match en cours)
CREATE TABLE stream (
    stream_id SERIAL PRIMARY KEY,
    url TEXT NOT NULL, -- URL du flux en direct
    match_id INTEGER NOT NULL UNIQUE, -- lien avec le match
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- correspond à la date du match
    FOREIGN KEY (match_id) REFERENCES match(match_id) ON DELETE CASCADE
);

-- ------------------------------------------------
-- Indexes utiles
-- ------------------------------------------------
CREATE INDEX idx_match_white_id ON match(white_id);
CREATE INDEX idx_match_black_id ON match(black_id);
CREATE INDEX idx_video_match_id ON video(match_id);
CREATE INDEX idx_match_date ON match(date);
CREATE INDEX idx_stream_match_id ON stream(match_id);


-- ------------------------------------------------
-- Trigger : copie automatique de la durée de la vidéo vers le match
-- ------------------------------------------------

CREATE OR REPLACE FUNCTION sync_match_duration()
RETURNS TRIGGER AS $$
BEGIN
    -- Met à jour la durée du match seulement si elle est NULL
    UPDATE match
    SET duration = NEW.duration
    WHERE match.match_id = NEW.match_id
      AND match.duration IS NULL;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_match_duration
AFTER INSERT ON video
FOR EACH ROW
EXECUTE FUNCTION sync_match_duration();