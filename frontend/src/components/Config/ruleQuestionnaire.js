export const QUESTIONNAIRE_SECTIONS = [
    {
        key: 'core_hours',
        title: 'Core Hours',
        description: 'Ordinary-hours limits before overtime applies.',
        fields: [
            ['day_worker_daily_limit_hours', 'Day worker daily limit', 'number'],
            ['shift_worker_daily_limit_hours', 'Shift worker daily limit', 'number'],
            ['day_worker_weekly_limit_hours', 'Day worker weekly limit', 'number'],
            ['shift_worker_weekly_limit_hours', 'Shift worker weekly limit', 'number'],
        ],
    },
    {
        key: 'overtime',
        title: 'Overtime',
        description: 'Standard, extended, and weekend overtime multipliers.',
        fields: [
            ['standard_overtime_rate', 'Standard overtime rate', 'number'],
            ['two_tier_overtime', 'Use two-tier overtime', 'boolean'],
            ['extended_overtime_rate', 'Extended overtime rate', 'number'],
            [
                'two_tier_overtime_threshold',
                'Hours before extended overtime',
                'number',
            ],
            ['extended_overtime_days', 'Extended overtime days', 'days'],
            ['saturday_overtime_rate', 'Saturday overtime rate', 'number'],
            ['sunday_overtime_rate', 'Sunday overtime rate', 'number'],
        ],
    },
    {
        key: 'span_overtime',
        title: 'Span Overtime',
        description: 'Whether work after a time-of-day cutoff becomes overtime.',
        fields: [
            ['applies', 'Apply span overtime', 'boolean'],
            ['cutoff_hour', 'Span overtime cutoff hour', 'number'],
        ],
    },
    {
        key: 'weekend_treatment',
        title: 'Weekend Treatment',
        description:
            'Choose whether each worker/day combination is overtime, a loading, or not applicable.',
        fields: [
            ['day_saturday_treatment', 'Day worker Saturday treatment', 'weekend'],
            [
                'day_saturday_penalty_loading',
                'Day worker Saturday loading',
                'number',
            ],
            ['day_sunday_treatment', 'Day worker Sunday treatment', 'weekend'],
            [
                'day_sunday_penalty_loading',
                'Day worker Sunday loading',
                'number',
            ],
            [
                'shift_saturday_treatment',
                'Shift worker Saturday treatment',
                'weekend',
            ],
            [
                'shift_saturday_penalty_loading',
                'Shift worker Saturday loading',
                'number',
            ],
            [
                'shift_sunday_treatment',
                'Shift worker Sunday treatment',
                'weekend',
            ],
            [
                'shift_sunday_penalty_loading',
                'Shift worker Sunday loading',
                'number',
            ],
        ],
    },
    {
        key: 'gap_between_shifts',
        title: 'Gap Between Shifts',
        description: 'Insufficient-break threshold and loading.',
        fields: [
            ['applies', 'Apply an insufficient gap penalty', 'boolean'],
            ['minimum_hours', 'Minimum hours between shifts', 'number'],
            ['penalty_rate', 'Insufficient gap penalty rate', 'number'],
        ],
    },
    {
        key: 'weekday_penalties',
        title: 'Weekday Penalties',
        description:
            'Repeatable whole-shift and time-window loading definitions.',
        fields: [
            ['shift_based_penalties', 'Shift-based penalties', 'penalties'],
            ['time_based_penalties', 'Time-based penalties', 'penalties'],
        ],
    },
    {
        key: 'employment_defaults',
        title: 'Employment and Defaults',
        description: 'Defaults and contracted-hours behaviour used by Paychecker.',
        fields: [
            ['default_break', 'Default unpaid break (hours)', 'number'],
            [
                'part_time_contracted_hours_overtime',
                'Part-time overtime after contracted hours',
                'boolean',
            ],
            [
                'part_time_top_up_entitlement',
                'Part-time contracted-hours top-up',
                'boolean',
            ],
            [
                'full_time_top_up_entitlement',
                'Full-time contracted-hours top-up',
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

export const hasStructuralErrors = (issues = []) =>
    issues.some((issue) => issue.severity === 'error');
