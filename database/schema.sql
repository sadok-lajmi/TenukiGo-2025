-- ------------------------------------------------
-- Tables
-- ------------------------------------------------

-- Player table
CREATE TABLE player (
    player_id SERIAL PRIMARY KEY,
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    level VARCHAR(20)
);

-- Match table
CREATE TABLE match (
    match_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    style VARCHAR(50), -- "tournament", "friendly", "educational"
    white_id INTEGER,  -- FK to player
    black_id INTEGER,  -- FK to player
    result VARCHAR(20), -- "white", "black", "draw", "educational"
    duration INTEGER,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sgf TEXT, -- path to the sgf file in the storage/ folder
    description TEXT,
    FOREIGN KEY (white_id) REFERENCES player(player_id) ON DELETE SET NULL,
    FOREIGN KEY (black_id) REFERENCES player(player_id) ON DELETE SET NULL
);

-- Video table (1-1 with match via unique match_id)
CREATE TABLE video (
    video_id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    path TEXT, -- path to the video file in the storage/ folder
    thumbnail TEXT, -- path to the thumbnail file in the storage/ folder
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration INTEGER,
    sgf TEXT, -- path to the sgf file associated with the video in the storage/ folder
    match_id INTEGER UNIQUE, -- ensures 1-1: one video → one match
    FOREIGN KEY (match_id) REFERENCES match(match_id) ON DELETE SET NULL
);

-- Stream table (linked to the ongoing match)
CREATE TABLE stream (
    stream_id SERIAL PRIMARY KEY,
    url TEXT NOT NULL, -- live stream URL
    match_id INTEGER NOT NULL UNIQUE, -- link to the match
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- corresponds to the match date
    FOREIGN KEY (match_id) REFERENCES match(match_id) ON DELETE CASCADE
);

-- ------------------------------------------------
-- Useful indexes
-- ------------------------------------------------
CREATE INDEX idx_match_white_id ON match(white_id);
CREATE INDEX idx_match_black_id ON match(black_id);
CREATE INDEX idx_video_match_id ON video(match_id);
CREATE INDEX idx_match_date ON match(date);
CREATE INDEX idx_stream_match_id ON stream(match_id);


-- ------------------------------------------------
-- Trigger: automatic copy of video duration to match
-- ------------------------------------------------

CREATE OR REPLACE FUNCTION sync_match_duration()
RETURNS TRIGGER AS $$
BEGIN
    -- Updates the match duration only if it is NULL
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
