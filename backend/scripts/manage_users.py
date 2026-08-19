#!/usr/bin/env python3
"""Manage local testing users without exposing an administration API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from psycopg.errors import UniqueViolation

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.auth_store import (  # noqa: E402
    add_user,
    delete_unowned_configurations,
    list_users,
    set_user_active,
)


def parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(description=__doc__)
    commands = command_parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Add one named local user")
    add.add_argument("username")
    add.add_argument("--display-name", required=True)
    commands.add_parser("list", help="List local users")
    for name in ("deactivate", "reactivate"):
        action = commands.add_parser(name, help=f"{name.title()} one local user")
        action.add_argument("username")
    commands.add_parser(
        "delete-unowned-rules",
        help="Delete legacy custom rules that do not belong to a user",
    )
    return command_parser


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "add":
            user = add_user(args.username, args.display_name)
            print(f"Added {user['username']} ({user['display_name']}).")
        elif args.command == "list":
            users = list_users()
            if not users:
                print("No local users configured.")
            for user in users:
                status = "active" if user["is_active"] else "inactive"
                print(f"{user['username']}\t{user['display_name']}\t{status}")
        elif args.command in {"deactivate", "reactivate"}:
            active = args.command == "reactivate"
            if not set_user_active(args.username, active):
                parser().error(f"Unknown user: {args.username}")
            print(f"{args.username} is now {'active' if active else 'inactive'}.")
        else:
            count = delete_unowned_configurations()
            print(f"Deleted {count} unowned custom configuration(s).")
    except UniqueViolation:
        parser().error(f"User already exists: {args.username}")
    except ValueError as error:
        parser().error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
