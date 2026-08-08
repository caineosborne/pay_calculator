"""Fast Food Industry Award 2020 [MA000003] ruleset.

Source: Fair Work Ombudsman / Fair Work Commission consolidated award,
reviewed against the award current at 8 August 2026.

This ruleset models payment rules supported by the canonical pay-calculator
contract. Comments identify the relevant award clauses and any deliberate
proxy/manual treatment.

Known limitations:
- Overnight calendar-day treatment is incomplete. The engine currently carries
  a shift-worker weekend loading into the post-midnight portion, but it does
  not split weekday time-based penalties at midnight. For example, a Monday
  10:00 pm–Tuesday 3:00 am shift may miss the Tuesday 12:00 am–6:00 am
  loading. It also does not convert a day worker's post-midnight hours to the
  next calendar day's overtime treatment.
- Clauses 20.2 and 20.3: the award's 5-days-per-week rule permits 6 days in
  one week where ordinary hours are worked on no more than 4 days in the
  following week. The engine uses a 10-worked-days-per-pay-period proxy.
- Clauses 10.3-10.9 and 20.2-20.3: overtime arising from work outside a
  full-time employee's roster or a part-time employee's agreed/varied regular
  pattern must be manually classified as overtime where required.
- Clause 20.5: the 4-hour minimum payment for non-contiguous Sunday overtime
  is not currently represented by the engine.
- Clause 21: Sunday ordinary-hour penalties differ by classification.
  Level 1 is 125% (150% casual); Levels 2 and 3 are 150% (175% casual).
  The current DAY_TREATMENT_RULES contract has no classification dimension.
  This file uses the Level 1 Sunday rate as the default and must be overridden
  for Level 2 and Level 3 employees.
"""


class FastFoodAward2026Rules:
    CANONICAL_RULESET = True

    SHIFT_RULES = {
        # Clause 10.2 and 10.3(e):
        # Part-time employees must be rostered for at least 3 consecutive hours.
        # Clause 11.3:
        # Casual employees have a minimum daily engagement of 3 consecutive hours.
        # No equivalent minimum engagement is configured for full-time employees.
        "default_break_hours": 0.5,
        "minimum_paid_shift_hours": {
            "variation": "employment_type",
            "full_time": 0,
            "part_time": 3,
            "casual": 3,
        },
    }

    ORDINARY_TIME_RULES = {
        # Clause 11.2:
        # Casual ordinary hours are paid at the minimum hourly rate plus 25%.
        # This is an additional loading, not a total multiplier.
        "ordinary_rates": {"casual_loading": 0.25},

        # The award does not prescribe a general daily span of ordinary hours.
        # Clauses 20.2(b)-(d) and 20.3(b)-(d) instead make work outside an
        # employee's rostered/agreed hours overtime. Those roster-boundary
        # triggers must be handled using manual overtime where applicable.
        "span_overtime": {},

        # Clauses 13.5, 20.2(a)(iii), 20.3(a) and 20.4(b):
        # Maximum ordinary hours on any one day are 11 hours.
        "daily": {
            "variation": "employment_type",
            "full_time": 11,
            "part_time": 11,
            "casual": 11,
        },

        "period": {
            "variation": "employment_type",

            # Clauses 13.1-13.2:
            # Full-time ordinary hours average 38 per week and may be rostered
            # as 76 ordinary hours over 2 consecutive weeks.
            "full_time": 76,

            # Clauses 10.3-10.9 and 20.3:
            # Part-time ordinary hours are the employee's agreed/varied hours.
            # The configured numeric value is a fallback; where contracted
            # weekly hours are supplied, the engine uses those instead.
            "part_time": 38,

            # Clauses 11.1 and 20.4(a):
            # Casual ordinary hours may not exceed 38 per week, or average
            # 38 per week over the applicable roster cycle.
            "casual": 38,

            "basis": {
                "full_time": "pay_period",
                "part_time": "weekly",
                "casual": "weekly",
            },

            # Clauses 20.2(a)(ii) and 20.3(a):
            # Award rule: overtime after 5 days in one week, except 6 days may
            # be worked where ordinary hours are worked on no more than 4 days
            # in the following week.
            #
            # Engine proxy: maximum 10 worked days across the fortnight.
            # This is close to, but not identical to, the award test.
            "max_work_days": 10,
            "max_work_days_basis": "pay_period",

            # Clauses 10.3-10.9 and 20.3(a)(iii)-(v):
            # Part-time hours above the agreed/varied ordinary hours are OT.
            "part_time_uses_contracted_hours": True,
        },
    }

    DAY_TREATMENT_RULES = {
        "Saturday": {
            # Clause 21, Table 6:
            # Saturday ordinary hours = 125% FT/PT and 150% casual.
            # Clause 20.6:
            # If Saturday hours become overtime, Mon-Sat OT rates apply.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.25,
                "casual_rate": 0.50,
                "overtime_rate_key": "saturday",
            },
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.25,
                "casual_rate": 0.50,
                "overtime_rate_key": "saturday",
            },
        },

        "Sunday": {
            # Clause 21, Table 6:
            # Level 1 ordinary hours = 125% FT/PT and 150% casual.
            # Levels 2 and 3 ordinary hours = 150% FT/PT and 175% casual.
            #
            # MODEL LIMITATION:
            # DAY_TREATMENT_RULES does not currently vary by classification.
            # These configured values are the Level 1 rates. Level 2/3 require
            # a classification-specific override or future engine enhancement.
            #
            # Clause 20.6:
            # Sunday overtime = 200% FT/PT and 225% casual.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.25,
                "casual_rate": 0.50,
                "overtime_rate_key": "sunday",
            },
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.25,
                "casual_rate": 0.50,
                "overtime_rate_key": "sunday",
            },
        },

        "public_holiday": {
            # Clauses 21 and 27.3:
            # Public-holiday ordinary hours = 225% FT/PT and 250% casual.
            # Clause 20.6:
            # Public-holiday overtime = 250% FT/PT and 275% casual.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 1.25,
                "casual_rate": 1.50,
                "overtime_rate_key": "public_holiday",
            },
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 1.25,
                "casual_rate": 1.50,
                "overtime_rate_key": "public_holiday",
            },
        },
    }

    PAY_RATES = {
        "overtime": {
            # Clause 20.6, Table 5:
            # Monday-Saturday first 2 OT hours = 150% FT/PT, 175% casual.
            "weekday": {"multiplier": 1.50, "casual": 1.75},

            # Manual OT uses the standard first-tier weekday rate unless the
            # day treatment supplies a more specific OT rate key.
            "manual": {"multiplier": 1.50, "casual": 1.75},

            # Clause 20.6:
            # Saturday is included in the Monday-Saturday two-tier structure.
            "saturday": {"multiplier": 1.50, "casual": 1.75},

            # Clause 20.6:
            # Sunday all OT hours = 200% FT/PT, 225% casual.
            "sunday": {"multiplier": 2.00, "casual": 2.25},

            # Clause 20.6:
            # Public holiday all OT hours = 250% FT/PT, 275% casual.
            "public_holiday": {"multiplier": 2.50, "casual": 2.75},

            # Clause 20.6:
            # Monday-Saturday OT after the first 2 hours =
            # 200% FT/PT and 225% casual.
            "extended": {"multiplier": 2.00, "casual": 2.25},

            # Clause 20.6(b):
            # Each Monday-Saturday day's overtime stands alone, so the
            # first-2-hours threshold resets each day.
            "two_tier": {
                "enabled": True,
                "threshold": 2,
                "days": [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                ],
            },
        }
    }

    # No applicable minimum gap-between-shifts payment rule identified in the
    # Fast Food Industry Award for this calculator's rule family.
    GAP_BETWEEN_SHIFTS_RULE = {}

    ORDINARY_HOUR_PENALTIES = {
        "late_night_10pm_to_midnight": {
            # Clause 21, Table 6:
            # Monday-Friday 10:00 pm-midnight ordinary hours =
            # 110% FT/PT and 135% casual.
            "type": "time_based",
            "basis": "time",
            "start": 22,
            "end": 24,
            "rate": 0.10,
            "casual_rate": 0.35,
            "description": "Monday-Friday 10pm to midnight loading",
            "applies_to": ["day", "shift"],
            "days": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
            ],
        },
        "early_morning_midnight_to_6am": {
            # Clause 21, Table 6:
            # Monday-Friday midnight-6:00 am ordinary hours =
            # 115% FT/PT and 140% casual.
            "type": "time_based",
            "basis": "time",
            "start": 0,
            "end": 6,
            "rate": 0.15,
            "casual_rate": 0.40,
            "description": "Monday-Friday midnight to 6am loading",
            "applies_to": ["day", "shift"],
            "days": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
            ],
        },
    }

    # No contracted-hours top-up entitlement is modelled from the award.
    # Part-time agreed hours are instead used as an overtime threshold above.
    TOP_UP_RULES = {
        "part_time": False,
        "full_time": False,
    }


# ---------------------------------------------------------------------------
# Rules requiring manual treatment / not fully represented
# ---------------------------------------------------------------------------
#
# Clauses 10.3-10.9 and 20.3:
# Part-time employees have an agreed regular pattern including daily hours,
# days, start/finish times and meal breaks. Work beyond the agreed/validly
# varied pattern is overtime. Use manual_overtime where the engine cannot
# infer this from contracted weekly hours.
#
# Clause 20.2(b)-(d):
# Full-time work before rostered start, after rostered finish, or outside
# ordinary hours is overtime. Use manual_overtime for those hours where needed.
#
# Clause 20.5:
# Non-contiguous Sunday overtime has a minimum payment of 4 hours at the
# applicable Sunday OT rate. The current engine has no minimum-OT-payment rule.
#
# Clause 21:
# Sunday ordinary penalty differs by classification. This file defaults to
# Level 1. Levels 2 and 3 require 0.50 ordinary loading / 0.75 casual rate.
