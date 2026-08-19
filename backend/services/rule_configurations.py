"""Built-in rule definitions and PostgreSQL-backed custom overrides."""

from __future__ import annotations

import ast
import copy
import json
import pprint
import re
import uuid
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any

from psycopg.errors import UniqueViolation

from services.award_registry import load_awards
from services.rule_configuration_store import (
    create_configuration as create_stored_configuration,
    delete_configuration as delete_stored_configuration,
    get_configuration as get_stored_configuration,
    list_configurations as list_stored_configurations,
    rename_configuration as rename_stored_configuration,
    update_configuration as update_stored_configuration,
)
from services.rule_questionnaire import (
    MANAGED_ATTRIBUTES,
    patch_rule_source,
    project_rule_source,
    validate_questionnaire,
)


CUSTOM_ID_PREFIX = "custom:"
BUILTIN_ID_PREFIX = "builtin:"
MAX_SOURCE_BYTES = 500_000
REQUIRED_RULE_ATTRIBUTES = set(MANAGED_ATTRIBUTES)
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_NO_CHANGE = object()


class RuleConfigurationError(ValueError):
    """Raised when a requested rule configuration is invalid."""


class RuleConfigurationNotFound(RuleConfigurationError):
    """Raised when a rule configuration cannot be found."""


class RuleConfigurationConflict(RuleConfigurationError):
    """Raised when a custom configuration already exists."""


def _award_definition(award_key: str) -> dict:
    for award in load_awards():
        if award["key"] == award_key:
            return award
    raise RuleConfigurationError(f"Unknown award: {award_key}")


def _builtin_source_path(award_key: str) -> Path:
    award = _award_definition(award_key)
    return Path(__file__).resolve().parent / "rules" / f"{award['module']}.py"


def _custom_identifier(identifier: uuid.UUID) -> str:
    return f"{CUSTOM_ID_PREFIX}{identifier}"


def _parse_custom_identifier(identifier: str) -> uuid.UUID:
    if not identifier.startswith(CUSTOM_ID_PREFIX):
        raise RuleConfigurationError("Invalid custom configuration identifier.")
    try:
        return uuid.UUID(identifier.removeprefix(CUSTOM_ID_PREFIX))
    except ValueError as error:
        raise RuleConfigurationError("Invalid custom configuration identifier.") from error


def _configuration_metadata(record: dict) -> dict:
    award = _award_definition(record["base_award"])
    return {
        "id": _custom_identifier(record["id"]),
        "name": record["name"],
        "base_award": record["base_award"],
        "class_name": award["class_name"],
        "kind": "custom",
    }


def _class_assignments(award_key: str, source: str) -> dict[str, ast.AST]:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        location = f" at line {error.lineno}" if error.lineno else ""
        raise RuleConfigurationError(
            f"Invalid Python syntax{location}: {error.msg}"
        ) from error
    expected_class = _award_definition(award_key)["class_name"]
    class_node = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == expected_class
        ),
        None,
    )
    if class_node is None:
        raise RuleConfigurationError(
            f"Expected a top-level class named {expected_class}."
        )
    assignments = {}
    for statement in class_node.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = statement.value
    return assignments


def _rule_values_from_source(award_key: str, source: str) -> dict[str, dict]:
    assignments = _class_assignments(award_key, source)
    missing_attributes = sorted(REQUIRED_RULE_ATTRIBUTES - assignments.keys())
    if missing_attributes:
        raise RuleConfigurationError(
            "Rule class is missing required canonical attributes: "
            + ", ".join(missing_attributes)
        )
    values = {}
    for attribute in REQUIRED_RULE_ATTRIBUTES:
        try:
            value = ast.literal_eval(assignments[attribute])
        except (KeyError, ValueError, TypeError) as error:
            raise RuleConfigurationError(
                f"{attribute} must be a literal dictionary."
            ) from error
        if not isinstance(value, dict):
            raise RuleConfigurationError(f"{attribute} must be a dictionary.")
        values[attribute] = value
    return values


def _deep_difference(base: Any, changed: Any) -> Any:
    """Return the smallest JSON-safe patch that turns base into changed."""
    if isinstance(base, dict) and isinstance(changed, dict):
        result = {}
        for key in changed:
            difference = _deep_difference(base.get(key, _NO_CHANGE), changed[key])
            if difference is not _NO_CHANGE:
                result[key] = difference
        return result if result else _NO_CHANGE
    return _NO_CHANGE if base == changed else copy.deepcopy(changed)


def _deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        result = copy.deepcopy(base)
        for key, value in patch.items():
            result[key] = _deep_merge(result[key], value) if key in result else copy.deepcopy(value)
        return result
    return copy.deepcopy(patch)


def _rule_overrides(award_key: str, source: str) -> dict:
    base_values = _rule_values_from_source(
        award_key, _builtin_source_path(award_key).read_text(encoding="utf-8")
    )
    edited_values = _rule_values_from_source(award_key, source)
    overrides = {}
    for attribute in REQUIRED_RULE_ATTRIBUTES:
        difference = _deep_difference(base_values[attribute], edited_values[attribute])
        if difference is not _NO_CHANGE:
            overrides[attribute] = difference
    return overrides


def _source_with_overrides(award_key: str, overrides: dict) -> str:
    """Rebuild editor source from core rules plus a saved JSON patch."""
    source = _builtin_source_path(award_key).read_text(encoding="utf-8")
    tree = ast.parse(source)
    expected_class = _award_definition(award_key)["class_name"]
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == expected_class
    )
    base_values = _rule_values_from_source(award_key, source)
    for statement in class_node.body:
        target = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
        elif isinstance(statement, ast.AnnAssign):
            target = statement.target
        if not isinstance(target, ast.Name) or target.id not in REQUIRED_RULE_ATTRIBUTES:
            continue
        merged = _deep_merge(base_values[target.id], overrides.get(target.id, {}))
        expression = ast.parse(
            pprint.pformat(merged, width=88, sort_dicts=False), mode="eval"
        ).body
        statement.value = expression
    return ast.unparse(ast.fix_missing_locations(tree)) + "\n"


def validate_rule_source(award_key: str, source: str) -> dict:
    """Validate syntax, expected class name, and core calculation attributes."""
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise RuleConfigurationError("Rule source is too large.")
    _rule_values_from_source(award_key, source)
    return {
        "valid": True,
        "base_award": award_key,
        "class_name": _award_definition(award_key)["class_name"],
    }


def list_rule_configurations(owner_id: uuid.UUID | None = None) -> list[dict]:
    """Return public built-ins and, when signed in, the owner's custom rules."""
    configurations = [
        {
            "id": f"{BUILTIN_ID_PREFIX}{award['key']}",
            "name": award["label"],
            "base_award": award["key"],
            "class_name": award["class_name"],
            "kind": "builtin",
        }
        for award in load_awards()
        if award.get("calculator_mode", "shift") == "shift"
    ]
    if owner_id is None:
        return configurations
    return configurations + [
        _configuration_metadata(record)
        for record in list_stored_configurations(owner_id)
    ]


def _get_stored_configuration(identifier: str, owner_id: uuid.UUID) -> dict:
    record = get_stored_configuration(
        _parse_custom_identifier(identifier), owner_id
    )
    if record is None:
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    return record


def get_rule_configuration(
    identifier: str, owner_id: uuid.UUID | None = None
) -> dict:
    """Return configuration metadata plus source reconstructed from its patch."""
    if identifier.startswith(BUILTIN_ID_PREFIX):
        award_key = identifier.removeprefix(BUILTIN_ID_PREFIX)
        award = _award_definition(award_key)
        metadata = {
            "id": identifier,
            "name": award["label"],
            "base_award": award_key,
            "class_name": award["class_name"],
            "kind": "builtin",
        }
        source = _builtin_source_path(award_key).read_text(encoding="utf-8")
    else:
        if owner_id is None:
            raise RuleConfigurationNotFound(
                f"Rule configuration not found: {identifier}"
            )
        stored = _get_stored_configuration(identifier, owner_id)
        metadata = _configuration_metadata(stored)
        source = _source_with_overrides(stored["base_award"], stored["rules_json"])

    projection = project_rule_source(metadata["base_award"], source)
    return {**metadata, "source": source, **projection}


def validate_rule_payload(
    award_key: str,
    source: str,
    questionnaire: dict | None = None,
    *,
    allow_invalid_questionnaire: bool = False,
) -> dict:
    """Validate source/questionnaire and produce the resulting source text."""
    if questionnaire is not None:
        projection = project_rule_source(award_key, source, questionnaire)
        merged_questionnaire = projection["questionnaire"]
        for section, fields in merged_questionnaire.items():
            submitted_section = questionnaire.get(section)
            if not isinstance(submitted_section, dict):
                continue
            for field, record in fields.items():
                submitted_record = submitted_section.get(field)
                if isinstance(submitted_record, dict) and "answer" in submitted_record:
                    record["answer"] = submitted_record["answer"]
        structural_issues = validate_questionnaire(merged_questionnaire)
        errors = [issue for issue in structural_issues if issue["severity"] == "error"]
        if errors:
            if allow_invalid_questionnaire:
                return {
                    "valid": False,
                    "base_award": award_key,
                    "class_name": _award_definition(award_key)["class_name"],
                    "source": source,
                    "questionnaire": merged_questionnaire,
                    "structural_issues": structural_issues,
                    "advanced_attributes": projection["advanced_attributes"],
                }
            raise RuleConfigurationError(errors[0]["message"])
        try:
            source = patch_rule_source(award_key, source, merged_questionnaire)
        except ValueError as error:
            raise RuleConfigurationError(str(error)) from error
    validation = validate_rule_source(award_key, source)
    projection = project_rule_source(award_key, source, questionnaire)
    return {**validation, "source": source, **projection}


def create_custom_rule(
    award_key: str,
    name: str,
    source: str,
    questionnaire: dict | None = None,
    owner_id: uuid.UUID | None = None,
) -> dict:
    """Save only the fields changed from the selected immutable base award."""
    validation = validate_rule_payload(award_key, source, questionnaire)
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug or not _SLUG_PATTERN.fullmatch(slug):
        raise RuleConfigurationError(
            "Configuration name must contain at least one letter or number."
        )
    if owner_id is None:
        raise RuleConfigurationError("Sign in to save a custom configuration.")
    identifier = create_stored_configuration(
        award_key,
        name.strip(),
        slug,
        _rule_overrides(award_key, validation["source"]),
        owner_id,
    )
    if identifier is None:
        raise RuleConfigurationConflict(
            f"A custom configuration named '{name}' already exists."
        )
    return get_rule_configuration(_custom_identifier(identifier), owner_id)


def update_custom_rule(
    identifier: str,
    source: str,
    questionnaire: dict | None = None,
    owner_id: uuid.UUID | None = None,
) -> dict:
    """Replace one saved override patch without modifying core rule files."""
    if owner_id is None:
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    stored = _get_stored_configuration(identifier, owner_id)
    validation = validate_rule_payload(stored["base_award"], source, questionnaire)
    if not update_stored_configuration(
        stored["id"],
        _rule_overrides(stored["base_award"], validation["source"]),
        owner_id,
    ):
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    _load_custom_rule_class_cached.cache_clear()
    return get_rule_configuration(identifier, owner_id)


def _slug_for_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug or not _SLUG_PATTERN.fullmatch(slug):
        raise RuleConfigurationError(
            "Configuration name must contain at least one letter or number."
        )
    return slug


def rename_custom_rule(
    identifier: str, name: str, owner_id: uuid.UUID | None = None
) -> dict:
    """Rename a saved custom configuration without changing its rule values."""
    if owner_id is None:
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    stored = _get_stored_configuration(identifier, owner_id)
    try:
        renamed = rename_stored_configuration(
            stored["id"], name.strip(), _slug_for_name(name), owner_id
        )
    except UniqueViolation as error:
        raise RuleConfigurationConflict(
            f"A custom configuration named '{name}' already exists."
        ) from error
    if not renamed:
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    return get_rule_configuration(identifier, owner_id)


def delete_custom_rule(
    identifier: str, owner_id: uuid.UUID | None = None
) -> None:
    """Delete one custom configuration; built-ins never enter this path."""
    if owner_id is None:
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    stored = _get_stored_configuration(identifier, owner_id)
    if not delete_stored_configuration(stored["id"], owner_id):
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    _load_custom_rule_class_cached.cache_clear()


@lru_cache(maxsize=128)
def _load_custom_rule_class_cached(
    identifier: uuid.UUID, award_key: str, version: str, overrides_text: str
) -> type:
    """Create an in-memory class by overlaying a JSON patch on core rules."""
    award = _award_definition(award_key)
    module = import_module(f"services.rules.{award['module']}")
    base_class = getattr(module, award["class_name"])
    overrides = json.loads(overrides_text)
    attributes = {
        attribute: _deep_merge(getattr(base_class, attribute), overrides.get(attribute, {}))
        for attribute in REQUIRED_RULE_ATTRIBUTES
    }
    return type(f"Custom{award['class_name']}{identifier.hex}", (base_class,), attributes)


def load_custom_rule_class(
    identifier: str, award_key: str, owner_id: uuid.UUID | None = None
) -> type:
    """Load a saved override as an in-memory derivative of its base class."""
    if owner_id is None:
        raise RuleConfigurationNotFound(
            f"Rule configuration not found: {identifier}"
        )
    stored = _get_stored_configuration(identifier, owner_id)
    if stored["base_award"] != award_key:
        raise RuleConfigurationError(
            "The selected configuration does not belong to the requested award."
        )
    return _load_custom_rule_class_cached(
        stored["id"],
        award_key,
        stored["updated_at"].isoformat(),
        json.dumps(stored["rules_json"], sort_keys=True),
    )
