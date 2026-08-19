"""PostgreSQL persistence for local users, shared auth, and opaque sessions."""

from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from services.rule_configuration_store import connection, initialize_store


SESSION_COOKIE_NAME = "paychecker_session"
SESSION_TTL = timedelta(hours=12)
USERNAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,98}[a-z0-9])?$")
_password_hasher = PasswordHasher()


class AuthenticationNotConfigured(RuntimeError):
    """Raised when the local shared password has not been configured."""


def normalize_username(username: str) -> str:
    normalized = username.strip().lower()
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Username must use lowercase letters, numbers, dots, underscores, or hyphens."
        )
    return normalized


def public_user(user: dict) -> dict:
    return {
        "id": str(user["id"]),
        "username": user["username"],
        "display_name": user["display_name"],
    }


def add_user(username: str, display_name: str) -> dict:
    initialize_store()
    normalized = normalize_username(username)
    cleaned_name = display_name.strip()
    if not cleaned_name:
        raise ValueError("Display name cannot be blank.")
    identifier = uuid.uuid4()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (id, username, display_name)
            VALUES (%s, %s, %s)
            RETURNING id, username, display_name, is_active, created_at, updated_at
            """,
            (identifier, normalized, cleaned_name),
        )
        return cursor.fetchone()


def list_users() -> list[dict]:
    initialize_store()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, username, display_name, is_active, created_at, updated_at
            FROM users
            ORDER BY username COLLATE "C"
            """
        )
        return cursor.fetchall()


def delete_user(username: str) -> bool:
    """Delete a user and owned records; intended for isolated test cleanup."""
    initialize_store()
    normalized = normalize_username(username)
    with connection() as database, database.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE username = %s", (normalized,))
        return cursor.rowcount == 1


def get_user_by_username(username: str, *, include_inactive: bool = False) -> dict | None:
    initialize_store()
    try:
        normalized = normalize_username(username)
    except ValueError:
        return None
    active_clause = "" if include_inactive else "AND is_active"
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id, username, display_name, is_active, created_at, updated_at
            FROM users
            WHERE username = %s {active_clause}
            """,
            (normalized,),
        )
        return cursor.fetchone()


def set_user_active(username: str, is_active: bool) -> bool:
    initialize_store()
    normalized = normalize_username(username)
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            UPDATE users
            SET is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE username = %s
            """,
            (is_active, normalized),
        )
        updated = cursor.rowcount == 1
        if not is_active:
            cursor.execute(
                "DELETE FROM sessions WHERE user_id = (SELECT id FROM users WHERE username = %s)",
                (normalized,),
            )
        return updated


def delete_unowned_configurations() -> int:
    initialize_store()
    with connection() as database, database.cursor() as cursor:
        cursor.execute("DELETE FROM rule_configurations WHERE owner_id IS NULL")
        return cursor.rowcount


def set_shared_password(password: str) -> None:
    if not password:
        raise ValueError("The shared password cannot be blank.")
    initialize_store()
    password_hash = _password_hasher.hash(password)
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            UPDATE authentication_config
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE singleton = TRUE
            """,
            (password_hash,),
        )
        cursor.execute("DELETE FROM sessions")


def _shared_password_hash() -> str | None:
    initialize_store()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            "SELECT password_hash FROM authentication_config WHERE singleton = TRUE"
        )
        record = cursor.fetchone()
        return record["password_hash"] if record else None


def authenticate(username: str, password: str) -> tuple[str, dict] | None:
    password_hash = _shared_password_hash()
    if not password_hash:
        raise AuthenticationNotConfigured(
            "Local authentication is not configured. Run manage_auth.py set-password."
        )
    try:
        password_matches = _password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        password_matches = False
    user = get_user_by_username(username)
    if not password_matches or user is None:
        return None

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + SESSION_TTL
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO sessions (token_hash, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (token_hash, user["id"], expires_at),
        )
    return raw_token, user


def user_for_session(raw_token: str | None) -> dict | None:
    if not raw_token:
        return None
    initialize_store()
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    with connection() as database, database.cursor() as cursor:
        cursor.execute(
            """
            SELECT users.id, users.username, users.display_name, users.is_active
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = %s
              AND sessions.expires_at > CURRENT_TIMESTAMP
              AND users.is_active
            """,
            (token_hash,),
        )
        return cursor.fetchone()


def revoke_session(raw_token: str | None) -> None:
    if not raw_token:
        return
    initialize_store()
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    with connection() as database, database.cursor() as cursor:
        cursor.execute("DELETE FROM sessions WHERE token_hash = %s", (token_hash,))
