"""Woolworths Australian Food Group Agreement 2024 ruleset.

Source: Woolworths Australian Food Group Agreement 2024.

This represents the calculator's base-case interpretation of the core
hours, penalties and overtime provisions.

Important modelling notes:
- Full-time, part-time and casual ordinary hours are generally limited to
  9 hours per day, with one permitted 11-hour day per week.
- The Agreement permits 5 ordinary-work days per week, or 6 in one week
  with the corresponding conditions. The calculator uses 10 worked days
  per fortnight as a practical proxy.
- Part-time hours above contract hours can be ordinary under an accepted
  clause 8.4 flex-up arrangement. Because the current request model does
  not separately identify flex-up hours, contracted-hours OT requires
  manual treatment.
- The default break between work periods is 12 hours. It may be reduced
  by agreement to not less than 10 hours; the ruleset cannot know whether
  that agreement exists. Update - set to 10 hours for Woolworths 2024 demo.
"""


class Woolies2024Rules:
    SHIFT_RULES = {
        "default_break_hours": 0.5,

        # Clauses 8.2, 8.3 and 8.6:
        # FT minimum daily engagement = 4 hours.
        # PT and casual minimum daily engagement = 3 hours.
        "minimum_paid_shift_hours": {
            "variation": "employment_type",
            "full_time": 4,
            "part_time": 3,
            "casual": 3,
        },
    }

    ORDINARY_TIME_RULES = {
        # Clause 4.1(c):
        # Casuals receive a 25% casual loading where no other applicable
        # loading/penalty replaces it. Clause 6.2 casual penalty rates are
        # inclusive of this loading.
        "ordinary_rates": {"casual_loading": 0.25},

        # Clause 6.1:
        # Ordinary span for non-shiftworkers:
        # Mon-Sat 7:00am-11:00pm; Sunday 9:00am-11:00pm.
        #
        # Clause 6.1(b) permits hours outside these spans to remain ordinary
        # where agreement/conditions are satisfied, but they are paid at
        # clause 6.2 rates equivalent to overtime. The engine represents the
        # base case as span overtime.
        "span_overtime": {
            "day": {
                "default": {"start": 7, "end": 23, "enabled": True},
                "Sunday": {"start": 9, "end": 23, "enabled": True},
            }
        },

        # Clauses 8.2, 8.3, 8.6 and 10.2-10.4:
        # Maximum ordinary hours = 9 per day, with one permitted
        # 11-hour day each week.
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

            # Clause 8.2:
            # FT hours may be averaged as 76 hours over 2 consecutive weeks.
            "full_time": 76,

            # Clause 10.3:
            # PT overtime applies above 38 hours in any one week.
            "part_time": 38,

            # Clause 10.4:
            # Casual overtime applies above 38 ordinary hours per week
            # (or averaged over the roster cycle where applicable).
            "casual": 38,

            "basis": {
                "full_time": "pay_period",
                "part_time": "weekly",
                "casual": "weekly",
            },

            # Clauses 8.2, 8.3 and 8.6:
            # Base rostering rule is up to 5 days/week, with mechanisms for
            # a sixth day. Ten days/fortnight is used as a practical proxy.
            "max_work_days": 10,
            "max_work_days_basis": "pay_period",

            # Clause 10.3(a)(v) makes PT hours above contract hours overtime,
            # except additional hours accepted under clause 8.4 flex-up.
            # The current engine cannot distinguish flex-up acceptance, so
            # leave this False and manually classify OT where required.
            "part_time_uses_contracted_hours": False,
        },
    }

    DAY_TREATMENT_RULES = {
        "Saturday": {
            # Clause 6.2:
            # Non-shiftworker Saturday 7am-11pm =
            # 125% FT/PT, 150% casual.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.25,
                "casual_rate": 0.50,
                "overtime_rate_key": "saturday",
            },

            # Clause 11.3:
            # Saturday shiftwork = 150% FT/PT, 175% casual.
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.50,
                "casual_rate": 0.75,
                "overtime_rate_key": "saturday",
            },
        },

        "Sunday": {
            # Clause 6.2:
            # Sunday 9am-11pm ordinary hours =
            # 150% FT/PT, 175% casual.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.50,
                "casual_rate": 0.75,
                "overtime_rate_key": "sunday",
            },

            # Clause 11.3:
            # Sunday shiftwork = 175% FT/PT, 200% casual.
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.75,
                "casual_rate": 1.00,
                "overtime_rate_key": "sunday",
            },
        },

        "public_holiday": {
            # Clause 19.2:
            # Public holiday rates override clause 6.2 and shiftwork rates.
            # FT/PT = 225%; casual = 250% inclusive of casual loading.
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
            # Clause 10.5:
            # Monday-Saturday first 3 OT hours =
            # 150% FT/PT; 175% casual.
            "weekday": {"multiplier": 1.50, "casual": 1.75},
            "manual": {"multiplier": 1.50, "casual": 1.75},
            "saturday": {"multiplier": 1.50, "casual": 1.75},

            # Clause 10.5:
            # Sunday OT = 200% FT/PT; 225% casual.
            "sunday": {"multiplier": 2.00, "casual": 2.25},

            # Clause 10.5:
            # Public holiday OT = 250% FT/PT; 275% casual.
            "public_holiday": {"multiplier": 2.50, "casual": 2.75},

            # Clause 10.5:
            # Monday-Saturday after first 3 OT hours =
            # 200% FT/PT; 225% casual.
            "extended": {"multiplier": 2.00, "casual": 2.25},

            # Clause 10.5:
            # Overtime is calculated on a daily basis.
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

    # Clause 7.3:
    # Default entitlement is 12 hours between work periods.
    # If work recommences without the required break, the employee is paid
    # double the rate they would otherwise be entitled to until released
    # for 12 consecutive hours.
    #
    # By agreement this can be reduced to not less than 10 hours.
    # The engine has no agreement flag, so 12 hours is the base case.
    GAP_BETWEEN_SHIFTS_RULE = {
        "minimum_hours": 10,
        "loading": 1.0,
        "casual_rate": 1.0,
    }

    ORDINARY_HOUR_PENALTIES = {
        "evening_hours_6pm_to_11pm": {
            # Clause 6.2:
            # Monday-Friday 6pm-11pm =
            # 125% FT/PT; 150% casual.
            #
            # Applies only to non-shiftworkers. Shiftworkers are paid under
            # clause 11 instead.
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
            # Clauses 11.1-11.3:
            # Applies only to employees specifically employed as shiftworkers.
            # Qualifying weekday shiftwork = base +30% FT/PT, +55% casual.
            #
            # Clause 11.2 defines shiftwork by the shift start/finish pattern.
            # The request must correctly identify the worker as a shiftworker.
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
# Clause 6.1(b):
# Hours outside the normal span can remain ordinary by agreement while being
# paid at clause 6.2 rates equivalent to overtime. The base config treats
# these as OT because the calculator has no outside-span agreement input.
#
# Clause 8.4 / clause 10.3(a)(v):
# PT flex-up hours can be accepted as additional ordinary hours. Unagreed
# hours above contract hours can be OT. The current request does not identify
# flex-up acceptance, so this requires manual treatment.
#
# Clause 7.3(c):
# A 12-hour inter-shift break can be reduced by agreement to 10 hours.
# The base config assumes no such agreement.
#
# Clause 8.2(h):
# A specific four-day-week arrangement changes the FT daily maximum to
# 9.5 hours and the 4-week day cap to 16. This is not represented here.
#
# Clause 11.4:
# Baking-production shiftworkers have separate early-morning/night rates
# and are not represented by the generic shiftworker configuration.
#
# Clause 11.5:
# Shiftworker meal/rest breaks are paid and form part of hours worked.
# A normal unpaid-break request for a shiftworker would therefore be wrong.
