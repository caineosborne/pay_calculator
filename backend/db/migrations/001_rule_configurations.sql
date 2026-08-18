CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rule_configurations (
    id UUID PRIMARY KEY,
    base_award TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    rules_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    owner_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_rule_configurations_shared_name
    ON rule_configurations (base_award, slug)
    WHERE owner_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_rule_configurations_owner_name
    ON rule_configurations (owner_id, base_award, slug)
    WHERE owner_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_rule_configurations_owner_updated
    ON rule_configurations (owner_id, updated_at DESC);
