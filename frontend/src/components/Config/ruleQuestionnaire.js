export const QUESTIONNAIRE_SECTIONS = [
    {
        key: 'overtime',
        title: 'Overtime rates',
        description: 'Set the rates for standard, higher-rate, and weekend overtime.',
        fields: [
            ['daily_overtime_configuration', 'Daily ordinary-hours limit', 'overtime_limits'],
            ['weekly_overtime_configuration', 'Maximum hours and days to work in a pay period', 'period_overtime_limits'],
            [
                'part_time_contracted_hours_overtime',
                'Does overtime start after a part-time employee’s contracted hours?',
                'boolean',
            ],
            ['standard_overtime_rate', 'Standard overtime rate', 'number'],
            ['two_tier_overtime', 'Are multiple overtime rates applicable?', 'boolean'],
            ['extended_overtime_rate', 'Higher overtime rate', 'number'],
            [
                'two_tier_overtime_threshold',
                'Hours before the higher overtime rate applies',
                'number',
            ],
            ['extended_overtime_days', 'Days the higher overtime rate applies', 'days'],
            ['saturday_overtime_rate', 'Saturday overtime rate', 'number'],
            ['sunday_overtime_rate', 'Sunday overtime rate', 'number'],
        ],
    },
    {
        key: 'span_overtime',
        title: 'Overtime outside ordinary span',
        description: 'Applies to day workers only. Work before the first time and after the second time is treated as overtime.',
        fields: [
            ['applies', 'Does overtime apply outside the ordinary span?', 'boolean'],
            ['before_cutoff_hour', 'Overtime applies before (24-hour time)', 'time'],
            ['cutoff_hour', 'Ordinary time ends (24-hour time)', 'time'],
        ],
    },
    {
        key: 'long_day',
        title: 'Long-day exception',
        description: 'Allow a limited number of extended ordinary days before daily overtime applies.',
        fields: [
            ['enabled', 'Allow a long-day exception?', 'boolean'],
            ['uses_per_week', 'Long-day exceptions per week', 'number'],
            ['ordinary_limit_hours', 'Ordinary-hours limit on a long day', 'number'],
        ],
    },
    {
        key: 'weekend_treatment',
        title: 'Weekend pay treatment',
        description:
            'Choose whether each worker/day combination is overtime, a loading, or not applicable.',
        fields: [
            ['day_saturday_treatment', 'What happens when a day worker works on Saturday?', 'weekend'],
            [
                'day_saturday_penalty_loading',
                'Saturday penalty loading (day workers)',
                'number',
            ],
            ['day_sunday_treatment', 'What happens when a day worker works on Sunday?', 'weekend'],
            [
                'day_sunday_penalty_loading',
                'Sunday penalty loading (day workers)',
                'number',
            ],
            [
                'shift_saturday_treatment',
                'What happens when a shift worker works on Saturday?',
                'weekend',
            ],
            [
                'shift_saturday_penalty_loading',
                'Saturday penalty loading (shift workers)',
                'number',
            ],
            [
                'shift_sunday_treatment',
                'What happens when a shift worker works on Sunday?',
                'weekend',
            ],
            [
                'shift_sunday_penalty_loading',
                'Sunday penalty loading (shift workers)',
                'number',
            ],
        ],
    },
    {
        key: 'gap_between_shifts',
        title: 'Break between shifts',
        description: 'Set the minimum break and any extra pay when it is not met.',
        fields: [
            ['applies', 'Is extra pay due when the break between shifts is too short?', 'boolean'],
            ['minimum_hours', 'Minimum break between shifts (hours)', 'number'],
            ['penalty_rate', 'Extra-pay rate for an insufficient break', 'number'],
        ],
    },
    {
        key: 'weekday_penalties',
        title: 'Weekday Penalties',
        description:
            'Use whole-shift penalties when a loading applies to every hour of a shift because of its start or end time. Use time-based penalties when a loading applies only to work performed during specific times.',
        fields: [
            ['shift_based_penalties', 'Whole-shift penalty loadings (based on start or end time)', 'penalties'],
            ['time_based_penalties', 'Time-based penalty loadings (for specific work times)', 'penalties'],
        ],
    },
    {
        key: 'employment_defaults',
        title: 'Employment settings',
        description: 'Set unpaid-break and contracted-hours rules.',
        fields: [
            ['default_break', 'Default unpaid break duration (hours)', 'number'],
            [
                'part_time_top_up_entitlement',
                'Contracted-hours top-up for part-time employees',
                'boolean',
            ],
            [
                'full_time_top_up_entitlement',
                'Contracted-hours top-up for full-time employees',
                'boolean',
            ],
        ],
    },
];

export const DAYS = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
];

export const fieldPath = (section, field) => `${section}.${field}`;
