"""Coles Retail Enterprise Agreement 2024 ruleset.

Source: Coles Retail Enterprise Agreement 2024.

Base-case configuration for core Coles retail team members. The core payment
rules are materially very similar to the Woolworths Australian Food Group
Agreement 2024, but this file uses the Coles clause references and terminology.

Important modelling notes:
- Maximum ordinary hours are 9 per day, with one permitted 11-hour day per week.
- Ordinary hours are generally limited to 5 days per week, with 6 days permitted
  in one week where no more than 4 are worked in the next week of the fixed
  2-week cycle. The calculator uses 10 worked days per fortnight as a proxy.
- Part-time hours above the agreed pattern are overtime unless validly varied
  under clause 4.3.4(f). The calculator cannot determine whether that variation
  exists, so this remains manual.
- The normal inter-shift break is 12 hours, reducible to 10 hours by agreement.
- Baking-production shiftworkers have separate rules and are excluded from the
  generic shiftworker configuration below.
"""


class Coles2024Rules:
    SHIFT_RULES = {
        "default_break_hours": 0.5,

        # Clause 4.3.4(b): PT minimum hours per day = 3.
        # Clause 4.3.5(a): casual minimum daily engagement = 3.
        # No separate FT minimum engagement is identified in the same Coles
        # rostering provisions, so 0 is used rather than importing Woolworths'
        # 4-hour FT minimum.
        "minimum_paid_shift_hours": {
            "variation": "employment_type",
            "full_time": 0,
            "part_time": 3,
            "casual": 3,
        },
    }

    ORDINARY_TIME_RULES = {
        # Casual penalty rates in clause 3.3 are inclusive of casual loading.
        # Base ordinary casual treatment is modelled as +25%.
        "ordinary_rates": {"casual_loading": 0.25},

        # Clause 4.2.3:
        # Non-shiftworker ordinary spread:
        # Mon-Sat 7am-11pm; Sunday 9am-11pm.
        #
        # Clause 4.9.5 permits outside-span hours to be treated as ordinary
        # by agreement provided the applicable OT rate is still paid.
        "span_overtime": {
            "day": {
                "default": {"start": 7, "end": 23, "enabled": True},
                "Sunday": {"start": 9, "end": 23, "enabled": True},
            }
        },

        # Clauses 4.3.1-4.3.2 and 4.9.3:
        # 9 ordinary hours/day, with one 11-hour day per week.
        "daily": {
            "variation": "employment_type",
            "full_time": 9,
            "part_time": 9,
            "casual": 9,
        },
        "long_day": {
            "uses_per_week": 1,
            "ordinary_limit_hours": 11,
        },

        "period": {
            "variation": "employment_type",

            # FT employment averages 38 hours/week. The calculator's
            # fortnight representation uses 76 hours.
            "full_time": 76,

            # Clause 4.9.2(b): PT >38 hours/week is OT.
            "part_time": 38,

            # Clause 4.9.3(a): casual >38 ordinary hours/week is OT.
            "casual": 38,

            "basis": {
                "full_time": "pay_period",
                "part_time": "weekly",
                "casual": "weekly",
            },

            # Clauses 4.3.1 and 4.3.2(c):
            # 5 days/week, or 6 + 4 across the fixed two-week cycle.
            # Ten days/fortnight is used as the practical proxy.
            "max_work_days": 10,
            "max_work_days_basis": "pay_period",

            # Clause 4.3.4(e)-(f) / 4.9.2(b):
            # PT excess agreed-pattern hours are OT unless validly varied.
            # The calculator cannot distinguish an accepted variation from
            # unagreed excess hours, so use manual OT where required.
            "part_time_uses_contracted_hours": False,
        },
    }

    DAY_TREATMENT_RULES = {
        "Saturday": {
            # Clause 3.3.1:
            # Saturday 7am-11pm = 125% FT/PT, 150% casual.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.25,
                "casual_rate": 0.50,
                "overtime_rate_key": "saturday",
            },

            # Clause 4.5.4(c):
            # Saturday shiftwork = 150% FT/PT, 175% casual.
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.50,
                "casual_rate": 0.75,
                "overtime_rate_key": "saturday",
            },
        },

        "Sunday": {
            # Clause 3.3.1:
            # Sunday 9am-11pm = 150% FT/PT, 175% casual.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.50,
                "casual_rate": 0.75,
                "overtime_rate_key": "sunday",
            },

            # Clause 4.5.4(d):
            # Sunday shiftwork = 175% FT/PT, 200% casual.
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.75,
                "casual_rate": 1.00,
                "overtime_rate_key": "sunday",
            },
        },

        "public_holiday": {
            # Clause 3.3.1:
            # Public holiday = base +125% FT/PT (225% total)
            # and base +150% casual (250% total).
            #
            # Clause 4.5.4(e) sends shiftworkers back to clause 3.3.1
            # for public-holiday shifts.
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
            # Clause 4.9.2(c) / 4.9.3(b):
            # Mon-Sat first 3 OT hours:
            # 150% FT/PT; 175% casual.
            "weekday": {"multiplier": 1.50, "casual": 1.75},
            "manual": {"multiplier": 1.50, "casual": 1.75},
            "saturday": {"multiplier": 1.50, "casual": 1.75},

            # Sunday OT:
            # 200% FT/PT; 225% casual.
            "sunday": {"multiplier": 2.00, "casual": 2.25},

            # Public holiday OT:
            # 250% FT/PT; 275% casual.
            "public_holiday": {"multiplier": 2.50, "casual": 2.75},

            # Mon-Sat OT after first 3 hours:
            # 200% FT/PT; 225% casual.
            "extended": {"multiplier": 2.00, "casual": 2.25},

            # Clause 4.9.2(d): OT is calculated daily.
            "two_tier": {
                "enabled": True,
                "threshold": 3,
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

    # Clause 4.3.2(b):
    # Standard break = 12 hours.
    # If work recommences without 12 hours off, rate = 200% until the
    # employee has had a 12-hour consecutive break.
    # The employee can agree to reduce the minimum period to 10 hours.
    GAP_BETWEEN_SHIFTS_RULE = {
        "minimum_hours": 12,
        "loading": 1.0,
        "casual_rate": 1.0,
    }

    ORDINARY_HOUR_PENALTIES = {
        "evening_hours_6pm_to_11pm": {
            # Clause 3.3.1:
            # Mon-Fri 6pm-11pm = +25% FT/PT, +50% casual.
            # Shiftworkers are excluded and instead use clause 4.5.
            "type": "time_based",
            "basis": "time",
            "start": 18,
            "end": 23,
            "rate": 0.25,
            "casual_rate": 0.50,
            "description": "Monday-Friday 6pm to 11pm loading",
            "applies_to": ["day"],
            "days": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
            ],
        },

        "weekday_shiftwork": {
            # Clauses 4.5.1-4.5.4:
            # Applies only to employees specifically employed as shiftworkers.
            # Shiftwork between midnight Sunday and midnight Friday =
            # 130% FT/PT and 155% casual.
            #
            # Clause 4.5.3 defines qualifying shiftwork, including a shift
            # starting at/after 6pm on one day and before 5am the next.
            "type": "shift_based",
            "basis": "start",
            "start": 18,
            "end": 5,
            "rate": 0.30,
            "casual_rate": 0.55,
            "description": "Weekday shiftwork loading",
            "applies_to": ["shift"],
            "days": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
            ],
        },
    }

    TOP_UP_RULES = {
        "part_time": False,
        "full_time": False,
    }


# ---------------------------------------------------------------------------
# Important manual / unsupported cases
# ---------------------------------------------------------------------------
#
# Clause 4.3.4(e)-(f) / 4.9.2(b):
# PT hours beyond the agreed pattern are OT unless validly varied in writing
# or through the relevant standing-consent mechanism. Use manual OT where the
# calculator cannot determine whether a valid variation exists.
#
# Clause 4.9.5:
# Outside-span hours may remain ordinary by agreement but must still be paid
# at the applicable overtime rate. The base ruleset classifies them as OT.
#
# Clause 4.3.2(b):
# The standard 12-hour inter-shift break can be reduced to 10 hours by Roster
# Choice. The base config assumes the 12-hour rule.
#
# Clause 4.3.3:
# Adult PT/casual employees may agree to a Voluntary Additional Shift, creating
# two ordinary work blocks on the same day separated by at least 2 unpaid hours.
# Both blocks are treated as one shift for other rostering/OT purposes. This is
# not explicitly represented by the generic ruleset.
#
# Clause 4.5.5:
# Shiftworker rest and meal breaks are paid and form part of hours worked.
# Do not use the normal unpaid-break treatment for shiftworkers.
#
# Appendix A3.4:
# Baking-production shiftworkers have separate early-morning/night rates and
# are excluded from this generic shiftworker configuration.
#
# Saved provisions in Appendix A3.6 are employee-specific and are not included.
