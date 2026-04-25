-- ==============================================================================
-- GitVision - PostgreSQL Database Schema (target PostgreSQL 14+)
-- Apply on a fresh database: createdb gitvision && psql -d gitvision -f schema.sql
-- Denormalized Users.followers / Users.following and Repository.stars are
-- derived caches maintained by triggers (not independent facts).
-- ==============================================================================

-- 1. Users
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    followers INT DEFAULT 0,
    following INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    github_id VARCHAR(100) UNIQUE,
    github_access_token TEXT
);

CREATE TABLE IF NOT EXISTS Language (
    language_id SERIAL PRIMARY KEY,
    language_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Repository (
    repo_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    language_id INT REFERENCES Language(language_id) ON DELETE SET NULL,
    repo_name VARCHAR(100) NOT NULL,
    description TEXT,
    stars INT DEFAULT 0,
    forks INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    github_repo_id VARCHAR(100) UNIQUE,
    github_url VARCHAR(255),
    UNIQUE(user_id, repo_name)
);

CREATE TABLE IF NOT EXISTS Snapshot (
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    followers INT DEFAULT 0,
    repo_count INT DEFAULT 0,
    PRIMARY KEY (user_id, date)
);

-- 5. Image (profile | repo; Firebase URL maps here)
CREATE TABLE IF NOT EXISTS Image (
    image_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    repo_id INT REFERENCES Repository(repo_id) ON DELETE CASCADE,
    image_url VARCHAR(512) NOT NULL,
    image_kind VARCHAR(20) NOT NULL DEFAULT 'profile' CHECK (image_kind IN ('profile', 'repo')),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Follow (
    follower_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    following_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id <> following_id)
);

CREATE TABLE IF NOT EXISTS Repository_Contributor (
    repo_id INT NOT NULL REFERENCES Repository(repo_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    PRIMARY KEY (repo_id, user_id)
);

CREATE TABLE IF NOT EXISTS Comment (
    comment_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    repo_id INT NOT NULL REFERENCES Repository(repo_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Activity_Log (
    log_id SERIAL PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Backup_Log (
    backup_id SERIAL PRIMARY KEY,
    backup_type VARCHAR(50) NOT NULL,
    backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS Notification (
    notification_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Session (
    session_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP,
    ip_address VARCHAR(45),
    token VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Tag (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Repository_Tag (
    repo_id INT NOT NULL REFERENCES Repository(repo_id) ON DELETE CASCADE,
    tag_id INT NOT NULL REFERENCES Tag(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (repo_id, tag_id)
);

CREATE TABLE IF NOT EXISTS Starred_Repository (
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    repo_id INT NOT NULL REFERENCES Repository(repo_id) ON DELETE CASCADE,
    starred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, repo_id)
);

-- ==============================================================================
-- INDEXES
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_repo_user_id ON Repository(user_id);
CREATE INDEX IF NOT EXISTS idx_comment_repo_id ON Comment(repo_id);
CREATE INDEX IF NOT EXISTS idx_comment_user_id ON Comment(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_user_id ON Notification(user_id);
CREATE INDEX IF NOT EXISTS idx_follow_follower ON Follow(follower_id);
CREATE INDEX IF NOT EXISTS idx_follow_following ON Follow(following_id);
CREATE INDEX IF NOT EXISTS idx_starred_repo_id ON Starred_Repository(repo_id);
CREATE INDEX IF NOT EXISTS idx_starred_user_id ON Starred_Repository(user_id);
CREATE INDEX IF NOT EXISTS idx_repo_contributor_user ON Repository_Contributor(user_id);
CREATE INDEX IF NOT EXISTS idx_session_user_id ON Session(user_id);
CREATE INDEX IF NOT EXISTS idx_session_token ON Session(token);
CREATE INDEX IF NOT EXISTS idx_image_user ON Image(user_id);
CREATE INDEX IF NOT EXISTS idx_image_repo ON Image(repo_id);
CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON Activity_Log(timestamp);

-- ==============================================================================
-- VIEWS
-- ==============================================================================
CREATE OR REPLACE VIEW user_repo_summary AS
SELECT
    u.user_id,
    u.username,
    COUNT(r.repo_id) AS total_repos,
    COALESCE(SUM(r.stars), 0) AS total_stars
FROM Users u
LEFT JOIN Repository r ON u.user_id = r.user_id
GROUP BY u.user_id, u.username;

CREATE OR REPLACE VIEW repo_engagement_summary AS
SELECT
    r.repo_id,
    r.repo_name,
    r.user_id AS owner_id,
    r.stars,
    (SELECT COUNT(*)::bigint FROM Comment c WHERE c.repo_id = r.repo_id) AS comment_count,
    (SELECT COUNT(*)::bigint FROM Repository_Contributor rc WHERE rc.repo_id = r.repo_id) AS contributor_count,
    (SELECT COUNT(*)::bigint FROM Starred_Repository s WHERE s.repo_id = r.repo_id) AS star_rows
FROM Repository r;

-- ==============================================================================
-- FUNCTIONS & PROCEDURES
-- ==============================================================================

-- Maintain denormalized follow counts on direct Follow INSERT/DELETE
CREATE OR REPLACE FUNCTION maintain_follow_counts()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE Users SET following = following + 1 WHERE user_id = NEW.follower_id;
        UPDATE Users SET followers = followers + 1 WHERE user_id = NEW.following_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE Users SET following = GREATEST(following - 1, 0) WHERE user_id = OLD.follower_id;
        UPDATE Users SET followers = GREATEST(followers - 1, 0) WHERE user_id = OLD.following_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_follow_counts
AFTER INSERT OR DELETE ON Follow
FOR EACH ROW EXECUTE FUNCTION maintain_follow_counts();

-- Activity audit: Users / Repository (no password in details)
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER AS $$
DECLARE
    d JSONB;
BEGIN
    IF TG_TABLE_NAME = 'users' THEN
        IF TG_OP = 'DELETE' THEN
            d := jsonb_build_object('user_id', OLD.user_id);
        ELSE
            d := jsonb_build_object('user_id', NEW.user_id);
        END IF;
    ELSIF TG_TABLE_NAME = 'repository' THEN
        IF TG_OP = 'DELETE' THEN
            d := jsonb_build_object('repo_id', OLD.repo_id);
        ELSE
            d := jsonb_build_object('repo_id', NEW.repo_id);
        END IF;
    ELSE
        d := NULL;
    END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO Activity_Log(action, table_name, details) VALUES ('INSERT', TG_TABLE_NAME, d);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO Activity_Log(action, table_name, details) VALUES ('UPDATE', TG_TABLE_NAME, d);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO Activity_Log(action, table_name, details) VALUES ('DELETE', TG_TABLE_NAME, d);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_users_activity
AFTER INSERT OR UPDATE OR DELETE ON Users
FOR EACH ROW EXECUTE FUNCTION log_user_activity();

CREATE TRIGGER trig_repos_activity
AFTER INSERT OR UPDATE OR DELETE ON Repository
FOR EACH ROW EXECUTE FUNCTION log_user_activity();

-- Minimal activity for social tables
CREATE OR REPLACE FUNCTION log_social_activity()
RETURNS TRIGGER AS $$
DECLARE
    d JSONB;
BEGIN
    IF TG_TABLE_NAME = 'follow' THEN
        IF TG_OP = 'DELETE' THEN
            d := jsonb_build_object('follower_id', OLD.follower_id, 'following_id', OLD.following_id);
        ELSE
            d := jsonb_build_object('follower_id', NEW.follower_id, 'following_id', NEW.following_id);
        END IF;
    ELSIF TG_TABLE_NAME = 'comment' THEN
        IF TG_OP = 'DELETE' THEN
            d := jsonb_build_object('comment_id', OLD.comment_id, 'repo_id', OLD.repo_id);
        ELSE
            d := jsonb_build_object('comment_id', NEW.comment_id, 'repo_id', NEW.repo_id);
        END IF;
    ELSIF TG_TABLE_NAME = 'starred_repository' THEN
        IF TG_OP = 'DELETE' THEN
            d := jsonb_build_object('user_id', OLD.user_id, 'repo_id', OLD.repo_id);
        ELSE
            d := jsonb_build_object('user_id', NEW.user_id, 'repo_id', NEW.repo_id);
        END IF;
    ELSE
        d := NULL;
    END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO Activity_Log(action, table_name, details) VALUES ('INSERT', TG_TABLE_NAME, d);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO Activity_Log(action, table_name, details) VALUES ('UPDATE', TG_TABLE_NAME, d);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO Activity_Log(action, table_name, details) VALUES ('DELETE', TG_TABLE_NAME, d);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_follow_activity
AFTER INSERT OR UPDATE OR DELETE ON Follow
FOR EACH ROW EXECUTE FUNCTION log_social_activity();

CREATE TRIGGER trig_comment_activity
AFTER INSERT OR UPDATE OR DELETE ON Comment
FOR EACH ROW EXECUTE FUNCTION log_social_activity();

CREATE TRIGGER trig_star_activity
AFTER INSERT OR UPDATE OR DELETE ON Starred_Repository
FOR EACH ROW EXECUTE FUNCTION log_social_activity();

CREATE OR REPLACE FUNCTION update_repo_stars()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE Repository SET stars = stars + 1 WHERE repo_id = NEW.repo_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE Repository SET stars = GREATEST(stars - 1, 0) WHERE repo_id = OLD.repo_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_update_repo_stars
AFTER INSERT OR DELETE ON Starred_Repository
FOR EACH ROW EXECUTE FUNCTION update_repo_stars();

-- follow_user_proc: insert + notify; counts via trig_follow_counts
CREATE OR REPLACE PROCEDURE follow_user_proc(p_follower_id INT, p_following_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    ins_count INT;
BEGIN
    IF p_follower_id = p_following_id THEN
        RAISE EXCEPTION 'cannot_follow_self';
    END IF;

    INSERT INTO Follow(follower_id, following_id)
    VALUES (p_follower_id, p_following_id)
    ON CONFLICT DO NOTHING;

    GET DIAGNOSTICS ins_count = ROW_COUNT;
    IF ins_count > 0 THEN
        INSERT INTO Notification(user_id, message)
        VALUES (
            p_following_id,
            CONCAT('User ', p_follower_id, ' started following you.')
        );
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE create_repository_proc(
    p_user_id INT,
    p_repo_name VARCHAR,
    p_description TEXT,
    p_language_name VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_language_id INT;
    v_repo_id INT;
BEGIN
    SELECT language_id INTO v_language_id FROM Language WHERE language_name = p_language_name;
    IF v_language_id IS NULL AND p_language_name IS NOT NULL AND length(trim(p_language_name)) > 0 THEN
        INSERT INTO Language(language_name) VALUES (p_language_name) RETURNING language_id INTO v_language_id;
    END IF;

    INSERT INTO Repository(user_id, language_id, repo_name, description)
    VALUES (p_user_id, v_language_id, p_repo_name, p_description)
    RETURNING repo_id INTO v_repo_id;

    INSERT INTO Repository_Contributor(repo_id, user_id, role)
    VALUES (v_repo_id, p_user_id, 'owner');
END;
$$;

-- Transactional backup marker: Backup_Log + Activity_Log companion row
CREATE OR REPLACE PROCEDURE backup_mark_proc(p_type VARCHAR, p_status VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO Backup_Log(backup_type, status) VALUES (p_type, p_status);
    INSERT INTO Activity_Log(action, table_name, details)
    VALUES (
        'BACKUP_RECORD',
        'Backup_Log',
        jsonb_build_object('backup_type', p_type, 'status', p_status)
    );
END;
$$;

-- Cursor demo (admin/debug): open named refcursor over recent Activity_Log
CREATE OR REPLACE FUNCTION activity_log_open_cursor(cur refcursor, p_limit INT)
RETURNS refcursor
LANGUAGE plpgsql
AS $$
BEGIN
    OPEN cur FOR
        SELECT log_id, action, table_name, details, timestamp
        FROM Activity_Log
        ORDER BY log_id DESC
        LIMIT p_limit;
    RETURN cur;
END;
$$;
