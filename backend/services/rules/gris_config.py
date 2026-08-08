"""General Retail Industry Award 2020 [MA000004] ruleset.

Source: Fair Work Commission / Fair Work Ombudsman consolidated award,
incorporating amendments up to and including 1 July 2026.

Base-case configuration for adult retail employees under the General Retail
Industry Award. Comments identify deliberate proxies and agreement-dependent
exceptions that the calculator cannot determine from worked hours alone.

Important modelling notes:
- Maximum ordinary hours are 9 per day, with one permitted 11-hour day per week.
- Full-time ordinary hours may be worked as 76 hours over 2 consecutive weeks.
- Part-time overtime depends on guaranteed hours / valid variations and therefore
  requires manual treatment where the calculator cannot determine the agreement.
- The normal inter-work-period break is 12 hours, reducible to 10 hours by agreement.
- The ordinary span depends on retailer trading hours. The base config assumes
  clause 15.2(c) applies, extending ordinary hours to 11pm on all days.
- Baking-production shiftworkers and special newsagency/video-shop spans are excluded.
"""


class GRIA2026Rules:
    SHIFT_RULES = {
        "default_break_hours": 0.5,

        # Clause 11.2:
        # Casual minimum daily engagement = 3 hours, except the 1.5-hour
        # secondary-school-student exception in clause 11.3.
        #
        # The Award does not prescribe the same general minimum daily
        # engagement for FT/PT employees in this rule family.
        "minimum_paid_shift_hours": {
            "variation": "employment_type",
            "full_time": 0,
            "part_time": 0,
            "casual": 3,
        },
    }

    ORDINARY_TIME_RULES = {
        # Clause 11.1:
        # Casual loading = 25% for ordinary hours where not replaced by a
        # penalty rate. Casual penalty and OT rates below are total/inclusive.
        "ordinary_rates": {"casual_loading": 0.25},

        # Clauses 15.1-15.2:
        # Default Award spans are:
        #   Mon-Fri 7am-9pm
        #   Saturday 7am-6pm
        #   Sunday 9am-6pm
        #
        # Clause 15.2(c) extends ordinary hours to 11pm on all days where the
        # retailer's trading hours extend beyond 9pm Mon-Fri or 6pm Sat/Sun.
        #
        # This base config assumes clause 15.2(c) applies, matching the common
        # supermarket/late-trading retail scenario.
        "span_overtime": {
            "day": {
                "default": {"start": 7, "end": 23, "enabled": True},
                "Sunday": {"start": 9, "end": 23, "enabled": True},
            }
        },

        # Clauses 15.4-15.5:
        # Maximum ordinary hours = 9/day, with one day per week up to 11.
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

            # Clause 15.6:
            # FT ordinary hours can be worked as 76 hours over 2 consecutive weeks.
            "full_time": 76,

            # Clause 21.2:
            # PT overtime is driven by guaranteed hours rather than a generic
            # weekly 38-hour threshold. 38 is retained only as the engine's
            # fallback numeric value; part-time_uses_contracted_hours remains
            # False because valid clause 10 variations are not visible to the engine.
            "part_time": 38,

            # Clause 21.2:
            # Casual overtime applies above 38 ordinary hours/week, or averaged
            # over the applicable roster cycle.
            "casual": 38,

            "basis": {
                "full_time": "pay_period",
                "part_time": "weekly",
                "casual": "weekly",
            },

            # Clause 15 rostering rules include limits on ordinary-work days,
            # including 19 days per 4-week cycle for larger establishments.
            # The calculator uses 10 days/fortnight as a practical retail proxy.
            "max_work_days": 10,
            "max_work_days_basis": "pay_period",

            # Clauses 10.5, 10.6, 10.11 and 21.2:
            # PT hours above guaranteed hours are OT unless the guaranteed-hours
            # arrangement has been validly varied. Manual OT is safer than
            # treating all hours above a supplied contract number as OT.
            "part_time_uses_contracted_hours": False,
        },
    }

    DAY_TREATMENT_RULES = {
        "Saturday": {
            # Clause 22.1, Table 12:
            # Saturday ordinary hours = 125% FT/PT and 150% casual.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.25,
                "casual_rate": 0.50,
                "overtime_rate_key": "saturday",
            },

            # Clause 25:
            # Saturday shiftwork = 150% FT/PT and 175% casual.
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.50,
                "casual_rate": 0.75,
                "overtime_rate_key": "saturday",
            },
        },

        "Sunday": {
            # Clause 22.1, Table 12:
            # Sunday ordinary hours = 150% FT/PT and 175% casual.
            "day": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.50,
                "casual_rate": 0.75,
                "overtime_rate_key": "sunday",
            },

            # Clause 25:
            # Sunday shiftwork = 175% FT/PT and 200% casual.
            "shift": {
                "base_classification": "ordinary",
                "ordinary_loading": 0.75,
                "casual_rate": 1.00,
                "overtime_rate_key": "sunday",
            },
        },

        "public_holiday": {
            # Clause 22.1, Table 12:
            # Public-holiday ordinary hours = 225% FT/PT and 250% casual.
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
            # Clause 21.2(c), Table 11:
            # Mon-Sat first 3 OT hours = 150% FT/PT, 175% casual.
            "weekday": {"multiplier": 1.50, "casual": 1.75},
            "manual": {"multiplier": 1.50, "casual": 1.75},
            "saturday": {"multiplier": 1.50, "casual": 1.75},

            # Sunday OT = 200% FT/PT, 225% casual.
            "sunday": {"multiplier": 2.00, "casual": 2.25},

            # Public-holiday OT = 250% FT/PT, 275% casual.
            "public_holiday": {"multiplier": 2.50, "casual": 2.75},

            # Mon-Sat after first 3 OT hours = 200% FT/PT, 225% casual.
            "extended": {"multiplier": 2.00, "casual": 2.25},

            # Clause 21.2(b):
            # Overtime is calculated daily.
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

    # Clause 16.6:
    # Standard break = 12 hours.
    # If an employee recommences without 12 hours off, worked hours are paid
    # at 200% until a 12-hour consecutive break is taken.
    # This may be reduced to 10 hours by agreement.
    GAP_BETWEEN_SHIFTS_RULE = {
        "minimum_hours": 12,
        "loading": 1.0,
        "casual_rate": 1.0,
    }

    ORDINARY_HOUR_PENALTIES = {
        "evening_hours_after_6pm": {
            # Clause 22.1, Table 12:
            # Monday-Friday ordinary hours after 6pm =
            # 125% FT/PT and 150% casual.
            #
            # The base span configuration assumes clause 15.2(c) permits
            # ordinary work through 11pm.
            "type": "time_based",
            "basis": "time",
            "start": 18,
            "end": 23,
            "rate": 0.25,
            "casual_rate": 0.50,
            "description": "Monday-Friday after 6pm loading",
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
            # Clauses 23-25:
            # Applies only to employees employed as shiftworkers.
            # Shiftwork between midnight Sunday and midnight Friday =
            # 130% FT/PT and 155% casual.
            #
            # Clause 24.1 defines non-baking shiftwork as a shift starting
            # at/after 6pm on one day and before 5am the next.
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
# Clauses 10.5, 10.6, 10.11 and 21.2:
# PT overtime depends on guaranteed hours and valid variations. The engine
# cannot infer whether a valid written variation exists, so manual OT may
# be required.
#
# Clauses 15.1-15.2:
# The base config assumes clause 15.2(c) applies and ordinary hours can extend
# to 11pm. Retailers without the required late trading hours instead use the
# narrower default spans (Mon-Fri to 9pm, Sat/Sun to 6pm).
#
# Clause 11.3:
# A qualifying full-time secondary-school student casual may have a 1.5-hour
# minimum engagement between 3pm and 6:30pm on a school day. Not modelled.
#
# Clause 16.6(d):
# The 12-hour gap may be reduced to 10 hours by agreement. Base config assumes
# no such agreement.
#
# Clause 24 / clause 25:
# Baking-production shiftworkers have separate shiftwork definitions/rates.
#
# Clause 26:
# Shiftworker rest and meal breaks are paid and form part of hours worked.
# Do not apply the normal unpaid-break treatment to a shiftworker.
#
# Clause 15.2(a)-(b):
# Special newsagency and video-shop ordinary-hour spans are not represented.
