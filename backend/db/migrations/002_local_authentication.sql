CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_username_normalized CHECK (username = LOWER(username)),
    CONSTRAINT users_username_not_blank CHECK (LENGTH(TRIM(username)) > 0),
    CONSTRAINT users_display_name_not_blank CHECK (LENGTH(TRIM(display_name)) > 0)
);

CREATE TABLE IF NOT EXISTS authentication_config (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    password_hash TEXT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO authentication_config (singleton, password_hash)
VALUES (TRUE, NULL)
ON CONFLICT (singleton) DO NOTHING;

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id
    ON sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
    ON sessions (expires_at);

ALTER TABLE rule_configurations
    ADD CONSTRAINT fk_rule_configurations_owner
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
