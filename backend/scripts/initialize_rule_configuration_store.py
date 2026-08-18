"""Create the local PostgreSQL schema for custom rule overrides."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.rule_configuration_store import initialize_store


if __name__ == "__main__":
    initialize_store()
    print("Rule configuration database is ready.")
