"""Filesystem-backed built-in and custom rule configuration management."""

from __future__ import annotations

import ast
import os
import re
import tempfile
import types
from pathlib import Path

from services.award_registry import load_awards


CUSTOM_RULES_ENV = "PAYCHECKER_CUSTOM_RULES_DIR"
DEFAULT_CUSTOM_RULES_DIR = Path(__file__).resolve().parents[1] / "custom_rules"
CUSTOM_ID_PREFIX = "custom:"
BUILTIN_ID_PREFIX = "builtin:"
MAX_SOURCE_BYTES = 500_000
REQUIRED_RULE_ATTRIBUTES = {
    "ORDINARY_HOURS_LIMIT_DAILY",
    "ORDINARY_HOURS_LIMIT_WEEKLY",
    "DAY_WORKER_ORDINARY_HOURS_DAILY",
    "DAY_WORKER_ORDINARY_HOURS_WEEKLY",
    "STANDARD_OVERTIME_RATE",
    "EXTENDED_OVERTIME_RATE",
    "SUNDAY_OVERTIME_RATE",
    "SATURDAY_OVERTIME_RATE",
    "WEEKEND_RULES",
    "TWO_TIER_OVERTIME",
}
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class RuleConfigurationError(ValueError):
    """Raised when a requested rule configuration is invalid."""


class RuleConfigurationNotFound(RuleConfigurationError):
    """Raised when a rule configuration cannot be found."""


class RuleConfigurationConflict(RuleConfigurationError):
    """Raised when a custom rule configuration already exists."""


def _award_definition(award_key: str) -> dict:
    for award in load_awards():
        if award["key"] == award_key:
            return award
    raise RuleConfigurationError(f"Unknown award: {award_key}")


def _custom_rules_dir() -> Path:
    configured_path = os.getenv(CUSTOM_RULES_ENV)
    return Path(configured_path) if configured_path else DEFAULT_CUSTOM_RULES_DIR


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise RuleConfigurationError(
            "Configuration name must contain at least one letter or number."
        )
    return slug


def _custom_identifier(award_key: str, slug: str) -> str:
    return f"{CUSTOM_ID_PREFIX}{award_key}:{slug}"


def _parse_custom_identifier(identifier: str) -> tuple[str, str]:
    parts = identifier.split(":")
    if len(parts) != 3 or parts[0] != "custom":
        raise RuleConfigurationError("Invalid custom configuration identifier.")
    award_key, slug = parts[1], parts[2]
    _award_definition(award_key)
    if not _SLUG_PATTERN.fullmatch(slug):
        raise RuleConfigurationError("Invalid custom configuration identifier.")
    return award_key, slug


def _custom_path(award_key: str, slug: str) -> Path:
    return _custom_rules_dir() / f"{award_key}__{slug}.py"


def _builtin_path(award: dict) -> Path:
    return Path(__file__).resolve().parent / "rules" / f"{award['module']}.py"


def _assigned_class_attributes(class_node: ast.ClassDef) -> set[str]:
    assigned = set()
    for statement in class_node.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
            )
            for target in targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
    return assigned


def validate_rule_source(award_key: str, source: str) -> dict:
    """Validate syntax, expected class name, and core calculation attributes."""
    award = _award_definition(award_key)
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise RuleConfigurationError("Rule source is too large.")

    try:
        syntax_tree = ast.parse(source)
    except SyntaxError as error:
        location = f" at line {error.lineno}" if error.lineno else ""
        raise RuleConfigurationError(
            f"Invalid Python syntax{location}: {error.msg}"
        ) from error

    expected_class = award["class_name"]
    class_node = next(
        (
            node
            for node in syntax_tree.body
            if isinstance(node, ast.ClassDef) and node.name == expected_class
        ),
        None,
    )
    if class_node is None:
        raise RuleConfigurationError(
            f"Expected a top-level class named {expected_class}."
        )

    missing_attributes = sorted(
        REQUIRED_RULE_ATTRIBUTES - _assigned_class_attributes(class_node)
    )
    if missing_attributes:
        raise RuleConfigurationError(
            "Rule class is missing required attributes: "
            + ", ".join(missing_attributes)
        )

    return {
        "valid": True,
        "base_award": award_key,
        "class_name": expected_class,
    }


def list_rule_configurations() -> list[dict]:
    """Return all registry-backed built-ins and saved custom rule files."""
    configurations = [
        {
            "id": f"{BUILTIN_ID_PREFIX}{award['key']}",
            "name": award["label"],
            "base_award": award["key"],
            "class_name": award["class_name"],
            "kind": "builtin",
        }
        for award in load_awards()
    ]

    custom_dir = _custom_rules_dir()
    if not custom_dir.exists():
        return configurations

    for path in sorted(custom_dir.glob("*.py")):
        stem_parts = path.stem.split("__", 1)
        if len(stem_parts) != 2:
            continue
        award_key, slug = stem_parts
        try:
            award = _award_definition(award_key)
        except RuleConfigurationError:
            continue
        configurations.append(
            {
                "id": _custom_identifier(award_key, slug),
                "name": slug.replace("-", " ").title(),
                "base_award": award_key,
                "class_name": award["class_name"],
                "kind": "custom",
            }
        )
    return configurations


def get_rule_configuration(identifier: str) -> dict:
    """Return configuration metadata and editable source text."""
    if identifier.startswith(BUILTIN_ID_PREFIX):
        award_key = identifier.removeprefix(BUILTIN_ID_PREFIX)
        award = _award_definition(award_key)
        path = _builtin_path(award)
        metadata = {
            "id": identifier,
            "name": award["label"],
            "base_award": award_key,
            "class_name": award["class_name"],
            "kind": "builtin",
        }
    else:
        award_key, slug = _parse_custom_identifier(identifier)
        path = _custom_path(award_key, slug)
        award = _award_definition(award_key)
        metadata = {
            "id": identifier,
            "name": slug.replace("-", " ").title(),
            "base_award": award_key,
            "class_name": award["class_name"],
            "kind": "custom",
        }

    if not path.is_file():
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )

    return {**metadata, "source": path.read_text(encoding="utf-8")}


def create_custom_rule(award_key: str, name: str, source: str) -> dict:
    """Validate and save a new custom copy without touching built-in files."""
    validate_rule_source(award_key, source)
    slug = _slugify(name)
    path = _custom_path(award_key, slug)
    if path.exists():
        raise RuleConfigurationConflict(
            f"A custom configuration named '{name}' already exists."
        )
    _write_custom_source(path, source)
    return get_rule_configuration(_custom_identifier(award_key, slug))


def update_custom_rule(identifier: str, source: str) -> dict:
    """Validate and replace an existing custom file."""
    award_key, slug = _parse_custom_identifier(identifier)
    path = _custom_path(award_key, slug)
    if not path.is_file():
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    validate_rule_source(award_key, source)
    _write_custom_source(path, source)
    return get_rule_configuration(identifier)


def _write_custom_source(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.stem}-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(source)
            temporary_path = Path(temporary_file.name)
        temporary_path.replace(path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def load_custom_rule_class(identifier: str, award_key: str) -> type:
    """Load a selected custom class from its dedicated filesystem file."""
    identifier_award, slug = _parse_custom_identifier(identifier)
    if identifier_award != award_key:
        raise RuleConfigurationError(
            "The selected configuration does not belong to the requested award."
        )

    path = _custom_path(identifier_award, slug)
    if not path.is_file():
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    source = path.read_text(encoding="utf-8")
    validation = validate_rule_source(identifier_award, source)
    module = types.ModuleType(
        f"paychecker_custom_{identifier_award}_{slug.replace('-', '_')}"
    )
    module.__file__ = str(path)
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
    except Exception as error:
        raise RuleConfigurationError(
            f"Custom rule configuration could not be loaded: {error}"
        ) from error
    rule_class = getattr(module, validation["class_name"], None)
    if not isinstance(rule_class, type):
        raise RuleConfigurationError(
            f"Custom rule configuration did not define "
            f"{validation['class_name']} at runtime."
        )
    missing_attributes = sorted(
        attribute
        for attribute in REQUIRED_RULE_ATTRIBUTES
        if not hasattr(rule_class, attribute)
    )
    if missing_attributes:
        raise RuleConfigurationError(
            "Loaded rule class is missing required attributes: "
            + ", ".join(missing_attributes)
        )
    return rule_class
