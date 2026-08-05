"""Canonical award-rule schema and legacy compatibility adapter.

New built-in rulesets use the grouped attributes below.  Saved custom rules may
still use the historical flat attributes; ``canonical_rules`` projects either
shape into the same read-only dictionary for the calculator.
"""

from __future__ import annotations

from copy import deepcopy


DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _worker_values(rules, day_name: str, shift_name: str) -> dict:
    return {
        "day": getattr(rules, day_name),
        "shift": getattr(rules, shift_name),
    }


def _legacy_day_rules(rules) -> dict:
    weekend = getattr(rules, "WEEKEND_RULES", {})
    result = {}
    for day in ("Saturday", "Sunday"):
        result[day] = {}
        for worker in ("day", "shift"):
            value = weekend.get(worker, {}).get(day) if worker in weekend else weekend.get(day, {})
            value = value or {}
            result[day][worker] = {
                "base_classification": "overtime" if value.get("is_overtime", False) else "ordinary",
                "ordinary_loading": value.get("penalty_rate", 0),
                "overtime_rate_key": day.lower(),
            }
    return result


def canonical_rules(rules) -> dict:
    """Return the canonical grouped configuration for a rule class.

    The adapter deliberately keeps compatibility at this boundary instead of
    spreading ``getattr`` fallbacks through calculation code.
    """
    if hasattr(rules, "ORDINARY_TIME_RULES"):
        return {
            "shift": deepcopy(getattr(rules, "SHIFT_RULES", {})),
            "ordinary_time": deepcopy(rules.ORDINARY_TIME_RULES),
            "day_treatment": deepcopy(getattr(rules, "DAY_TREATMENT_RULES", {})),
            "pay_rates": deepcopy(getattr(rules, "PAY_RATES", {})),
            "gap_between_shifts": deepcopy(getattr(rules, "GAP_BETWEEN_SHIFTS_RULE", {})),
            "penalties": deepcopy(getattr(rules, "ORDINARY_HOUR_PENALTIES", {})),
            "top_up": deepcopy(getattr(rules, "TOP_UP_RULES", {})),
        }

    daily = getattr(rules, "DAILY_OVERTIME_CONFIGURATION", None)
    weekly = getattr(rules, "WEEKLY_OVERTIME_CONFIGURATION", None)
    period = deepcopy(weekly) if weekly else {
        "variation": "worker_type",
        "day": getattr(rules, "DAY_WORKER_ORDINARY_HOURS_WEEKLY"),
        "shift": getattr(rules, "ORDINARY_HOURS_LIMIT_WEEKLY"),
    }
    period["part_time_uses_contracted_hours"] = getattr(
        rules, "USE_CONTRACTED_HOURS_FOR_PT_OVERTIME", False
    )
    # Historical rulesets describe this as a weekly limit.  Retain that
    # behaviour until an award explicitly opts into a whole-pay-period limit.
    period.setdefault("basis", "weekly")
    period.setdefault("max_work_days", None)
    return {
        "shift": {
            "default_break_hours": getattr(rules, "DEFAULT_BREAK", 0.5),
            "minimum_paid_shift_hours": {},
        },
        "ordinary_time": {
            "span_overtime": {
                "day": {
                    "default": {
                        "start": getattr(rules, "SPAN_OVERTIME_START_HOUR", None),
                        "end": getattr(rules, "SPAN_OVERTIME_HOUR", None),
                        "enabled": getattr(rules, "APPLY_SPAN_OVERTIME", True),
                    }
                }
            },
            "daily": daily or {"variation": "worker_type", "day": getattr(rules, "DAY_WORKER_ORDINARY_HOURS_DAILY"), "shift": getattr(rules, "ORDINARY_HOURS_LIMIT_DAILY")},
            "period": period,
        },
        "day_treatment": _legacy_day_rules(rules),
        "pay_rates": {
            "overtime": {
                "weekday": {"multiplier": getattr(rules, "STANDARD_OVERTIME_RATE")},
                "saturday": {"multiplier": getattr(rules, "SATURDAY_OVERTIME_RATE")},
                "sunday": {"multiplier": getattr(rules, "SUNDAY_OVERTIME_RATE")},
                "extended": {"multiplier": getattr(rules, "EXTENDED_OVERTIME_RATE")},
                "two_tier": {
                    "enabled": getattr(rules, "TWO_TIER_OVERTIME", False),
                    "threshold": getattr(rules, "TWO_TIER_OVERTIME_THRESHOLD", 0),
                    "days": getattr(rules, "EXTENDED_OVERTIME_DAYS", list(DAYS[:5])),
                },
            }
        },
        "gap_between_shifts": {
            "minimum_hours": getattr(rules, "GAP_PENALTY_HOURS", None),
            "loading": getattr(rules, "GAP_PENALTY_RATE", 0),
        },
        "penalties": deepcopy(getattr(rules, "PENALTIES", {})),
        "top_up": {
            "part_time": getattr(rules, "PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP", False),
            "full_time": getattr(rules, "FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP", False),
        },
    }


def install_canonical_contract(rules) -> None:
    """Expose canonical groups on legacy built-ins during the transition.

    This is intentionally performed once at registry load.  New rulesets
    define the groups directly; legacy custom rules keep using the adapter.
    """
    if hasattr(rules, "ORDINARY_TIME_RULES"):
        return
    config = canonical_rules(rules)
    rules.SHIFT_RULES = config["shift"]
    rules.ORDINARY_TIME_RULES = config["ordinary_time"]
    rules.DAY_TREATMENT_RULES = config["day_treatment"]
    rules.PAY_RATES = config["pay_rates"]
    rules.GAP_BETWEEN_SHIFTS_RULE = config["gap_between_shifts"]
    rules.ORDINARY_HOUR_PENALTIES = config["penalties"]
    rules.TOP_UP_RULES = config["top_up"]
