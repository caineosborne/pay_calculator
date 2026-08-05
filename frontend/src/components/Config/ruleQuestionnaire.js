export const QUESTIONNAIRE_SECTIONS = [
    {
        key: 'overtime',
        title: 'Overtime rates',
        description: 'Set the rates for standard, higher-rate, and weekend overtime.',
        fields: [
            ['daily_overtime_configuration', 'Daily ordinary-hours limit', 'overtime_limits'],
            ['weekly_overtime_configuration', 'Period ordinary-hours and days limit', 'period_overtime_limits'],
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
        description: 'Applies to day workers only. Set overtime before and/or after the ordinary span.',
        fields: [
            ['applies', 'Does overtime apply outside the ordinary span?', 'boolean'],
            ['before_cutoff_hour', 'Span overtime morning cut-off (24-hour time)', 'number'],
            ['cutoff_hour', 'Ordinary span ends at (24-hour time)', 'number'],
        ],
    },
    {
        key: 'weekend_treatment',
        title: 'Weekend pay treatment',
        description:
            'Choose whether each worker/day combination is overtime, a loading, or not applicable.',
        fields: [
            ['day_saturday_treatment', 'Saturday pay treatment (day workers)', 'weekend'],
            [
                'day_saturday_penalty_loading',
                'Saturday penalty loading (day workers)',
                'number',
            ],
            ['day_sunday_treatment', 'Sunday pay treatment (day workers)', 'weekend'],
            [
                'day_sunday_penalty_loading',
                'Sunday penalty loading (day workers)',
                'number',
            ],
            [
                'shift_saturday_treatment',
                'Saturday pay treatment (shift workers)',
                'weekend',
            ],
            [
                'shift_saturday_penalty_loading',
                'Saturday penalty loading (shift workers)',
                'number',
            ],
            [
                'shift_sunday_treatment',
                'Sunday pay treatment (shift workers)',
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
            'Whole-shift loadings apply to every hour when a shift meets its start, end, duration, or combined start-and-end condition. Time-based loadings apply only to hours worked in the selected time window.',
        fields: [
            ['shift_based_penalties', 'Whole-shift penalty loadings', 'penalties'],
            ['time_based_penalties', 'Time-based penalty loadings', 'penalties'],
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
