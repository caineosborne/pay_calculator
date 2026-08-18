"""PostgreSQL storage for custom rule overrides.

Only differences from a built-in ruleset are stored. The base award Python
classes remain the authoritative source for the public rules.
"""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


DATABASE_URL_ENV = "PAYCHECKER_DATABASE_URL"
DEFAULT_DATABASE_URL = (
    "postgresql://pay_checker:pay_checker_local@localhost:5432/pay_checker"
)
MIGRATIONS_DIRECTORY = Path(__file__).resolve().parents[1] / "db" / "migrations"


class DatabaseUnavailable(RuntimeError):
    """Raised when the configured PostgreSQL database cannot be reached."""


def database_url() -> str:
    return os.getenv(DATABASE_URL_ENV, DEFAULT_DATABASE_URL)


@contextmanager
def connection():
    try:
        with psycopg.connect(database_url(), row_factory=dict_row) as database:
            yield database
    except psycopg.OperationalError as error:
        raise DatabaseUnavailable(
            "The rules database is unavailable. Start local Postgres with "
            "`docker compose up -d postgres` or configure "
            "PAYCHECKER_DATABASE_URL."
        ) from error


def initialize_store() -> None:
    """Apply bundled, idempotent database migrations."""
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for migration_path in sorted(MIGRATIONS_DIRECTORY.glob("*.sql")):
            version = migration_path.name
            cursor.execute(
                "SELECT 1 FROM schema_migrations WHERE version = %s",
                (version,),
            )
            if cursor.fetchone():
                continue
            for statement in migration_path.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    cursor.execute(statement)
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,),
            )


def list_configurations(owner_id: uuid.UUID | None = None) -> list[dict]:
    initialize_store()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, base_award, name, slug, rules_json, owner_id,
                   created_at, updated_at
            FROM rule_configurations
            WHERE owner_id IS NOT DISTINCT FROM %s
            ORDER BY updated_at DESC, name COLLATE "C"
            """,
            (owner_id,),
        )
        return cursor.fetchall()


def get_configuration(
    identifier: uuid.UUID, owner_id: uuid.UUID | None = None
) -> dict | None:
    initialize_store()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, base_award, name, slug, rules_json, owner_id,
                   created_at, updated_at
            FROM rule_configurations
            WHERE id = %s AND owner_id IS NOT DISTINCT FROM %s
            """,
            (identifier, owner_id),
        )
        return cursor.fetchone()


def create_configuration(
    base_award: str,
    name: str,
    slug: str,
    rules_json: dict,
    owner_id: uuid.UUID | None = None,
) -> uuid.UUID | None:
    initialize_store()
    identifier = uuid.uuid4()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO rule_configurations (id, base_award, name, slug, rules_json, owner_id)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
            """,
            (identifier, base_award, name, slug, psycopg.types.json.Jsonb(rules_json), owner_id),
        )
        row = cursor.fetchone()
    return row["id"] if row else None


def update_configuration(
    identifier: uuid.UUID,
    rules_json: dict,
    owner_id: uuid.UUID | None = None,
) -> bool:
    initialize_store()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            UPDATE rule_configurations
            SET rules_json = %s::jsonb, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND owner_id IS NOT DISTINCT FROM %s
            """,
            (psycopg.types.json.Jsonb(rules_json), identifier, owner_id),
        )
        return cursor.rowcount == 1


def delete_configuration(
    identifier: uuid.UUID, owner_id: uuid.UUID | None = None
) -> bool:
    """Remove a record for test cleanup; no application route exposes this yet."""
    initialize_store()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM rule_configurations
            WHERE id = %s AND owner_id IS NOT DISTINCT FROM %s
            """,
            (identifier, owner_id),
        )
        return cursor.rowcount == 1


def rename_configuration(
    identifier: uuid.UUID,
    name: str,
    slug: str,
    owner_id: uuid.UUID | None = None,
) -> bool:
    """Rename one saved configuration while preserving its rule patch."""
    initialize_store()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            UPDATE rule_configurations
            SET name = %s, slug = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND owner_id IS NOT DISTINCT FROM %s
            """,
            (name, slug, identifier, owner_id),
        )
        return cursor.rowcount == 1
