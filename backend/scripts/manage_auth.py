#!/usr/bin/env python3
"""Configure the shared password used by named local testing accounts."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.auth_store import set_shared_password  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("set-password",))
    parser.parse_args()

    password = getpass.getpass("Shared testing password: ")
    confirmation = getpass.getpass("Confirm shared testing password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")
    try:
        set_shared_password(password)
    except ValueError as error:
        parser.error(str(error))
    print("Shared testing password updated. Existing sessions were revoked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
