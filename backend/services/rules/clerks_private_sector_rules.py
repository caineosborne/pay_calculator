"""Rule engine for award pay calculations."""


class ClerksPrivateSectorRules:
    """Business rules for award MA000002 pay calculations."""

    ORDINARY_HOURS_LIMIT_DAILY = 10
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 10
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2.0
    SUNDAY_OVERTIME_RATE = 2.0
    SATURDAY_OVERTIME_RATE = 1.5
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 1.0
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_HOUR = 19
    GAP_PENALTY_HOURS = 10
    GAP_PENALTY_RATE = 1.0
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 2
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    PENALTIES = {
        # 'meal_break_workthrough': {'type': 'time_based',
        #                         'start': None,
        #                         'end': None,
        #                         'rate': 1.0,
        #                         'description': 'Required to work through meal break for '
        #                                        'employees other than shiftworkers.',
        #                         'applies_to': ['day']},
     'shift_afternoon_night': {'type': 'shift_based',
                               'start': 10,
                               'end': 18,
                               'rate': 0.15,
                               'description': 'Ordinary hours worked on an afternoon or '
                                              'night shift.',
                               'applies_to': ['shift']},
     'shift_permanent_night': {'type': 'shift_based',
                               'start': 18,
                               'end': 24,
                               'rate': 0.3,
                               'description': 'Ordinary hours worked on a permanent night '
                                              'shift.',
                               'applies_to': ['shift']},
    #  'shift_weekend_public_holiday': {'type': 'shift_based',
    #                                   'start': None,
    #                                   'end': None,
    #                                   'rate': 0.5,
    #                                   'description': 'Ordinary hours worked by '
    #                                                  'shiftworkers on Saturday, Sunday or '
    #                                                  'a public holiday.',
    #                                   'applies_to': ['shift']}
    }
    HOURS_PEN_RULES = {}
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': False, 'rate': None},
             'Sunday': {'is_overtime': False, 'rate': None}},
     'shift': {'Saturday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5},
               'Sunday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5}}}
    DEFAULT_BREAK = 0.5

    # FIELD_EVIDENCE = {'use_contracted_hours_for_pt_overtime': {'status': 'defaulted',
    #                                           'source_ruleset_keys': [],
    #                                           'source_rule_ids': [],
    #                                           'clause_references': [],
    #                                           'reasoning_summary': 'Defaulted to True '
    #                                                                'because the source '
    #                                                                'rulesets do not answer '
    #                                                                'this field.'},
    #  'pt_employees_entitled_to_contracted_topup': {'status': 'defaulted',
    #                                                'source_ruleset_keys': [],
    #                                                'source_rule_ids': [],
    #                                                'clause_references': [],
    #                                                'reasoning_summary': 'Defaulted to True '
    #                                                                     'because the '
    #                                                                     'source rulesets '
    #                                                                     'do not answer '
    #                                                                     'this field.'},
    #  'ft_employees_entitled_to_contracted_topup': {'status': 'defaulted',
    #                                                'source_ruleset_keys': [],
    #                                                'source_rule_ids': [],
    #                                                'clause_references': [],
    #                                                'reasoning_summary': 'Defaulted to True '
    #                                                                     'because the '
    #                                                                     'source rulesets '
    #                                                                     'do not answer '
    #                                                                     'this field.'},
    #  'ordinary_hours_limit_daily': {'status': 'needs_review',
    #                                 'source_ruleset_keys': ['overtime_creation'],
    #                                 'source_rule_ids': ['general-daily-ordinary-hours-boundary',
    #                                                     'shiftwork-daily-ordinary-hours-boundary'],
    #                                 'clause_references': ['13.7',
    #                                                       '21.1(b)',
    #                                                       '26.2',
    #                                                       '28.1'],
    #                                 'reasoning_summary': 'No reasoning summary provided.'},
    #  'ordinary_hours_limit_weekly': {'status': 'needs_review',
    #                                  'source_ruleset_keys': ['overtime_creation'],
    #                                  'source_rule_ids': ['full-time-weekly-ordinary-hours-boundary',
    #                                                      'general-weekly-ordinary-hours-boundary',
    #                                                      'shiftwork-weekly-ordinary-hours-boundary'],
    #                                  'clause_references': ['9.1(a)',
    #                                                        '9.1(b)',
    #                                                        '13.2',
    #                                                        '21.1(a)',
    #                                                        '25.1',
    #                                                        '26.1',
    #                                                        '28.1'],
    #                                  'reasoning_summary': 'No reasoning summary provided.'},
    #  'day_worker_ordinary_hours_daily': {'status': 'needs_review',
    #                                      'source_ruleset_keys': ['overtime_creation'],
    #                                      'source_rule_ids': ['general-daily-ordinary-hours-boundary'],
    #                                      'clause_references': ['13.7', '21.1(b)'],
    #                                      'reasoning_summary': 'No reasoning summary '
    #                                                           'provided.'},
    #  'day_worker_ordinary_hours_weekly': {'status': 'needs_review',
    #                                       'source_ruleset_keys': ['overtime_creation'],
    #                                       'source_rule_ids': ['general-weekly-ordinary-hours-boundary',
    #                                                           'full-time-weekly-ordinary-hours-boundary'],
    #                                       'clause_references': ['13.2',
    #                                                             '21.1(a)',
    #                                                             '9.1(a)',
    #                                                             '9.1(b)'],
    #                                       'reasoning_summary': 'No reasoning summary '
    #                                                            'provided.'},
    #  'standard_overtime_rate': {'status': 'needs_review',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                                 'shiftwork-overtime-rate-full-time-part-time'],
    #                             'clause_references': ['clause 21.4(a)',
    #                                                   'clause 28.1',
    #                                                   'Table 6—Overtime rates for '
    #                                                   'shiftwork'],
    #                             'reasoning_summary': 'No reasoning summary provided.'},
    #  'extended_overtime_rate': {'status': 'needs_review',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                                 'shiftwork-overtime-rate-full-time-part-time',
    #                                                 'no-10-hour-break-200-percent-release',
    #                                                 'no-8-hour-break-200-percent-release'],
    #                             'clause_references': ['clause 21.4(a)',
    #                                                   'clause 22.4(a)',
    #                                                   'clause 30.5(a)',
    #                                                   'clause 28.1',
    #                                                   'Table 6—Overtime rates for '
    #                                                   'shiftwork'],
    #                             'reasoning_summary': 'No reasoning summary provided.'},
    #  'sunday_overtime_rate': {'status': 'needs_review',
    #                           'source_ruleset_keys': ['overtime_consequence'],
    #                           'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                               'nonshift-overtime-rate-casual',
    #                                               'shiftwork-overtime-rate-full-time-part-time',
    #                                               'shiftwork-overtime-rate-casual',
    #                                               'nonshift-overtime-minimum-4-hours-sunday'],
    #                           'clause_references': ['clause 21.4(a)',
    #                                                 'clause 21.4(c)',
    #                                                 'clause 28.1',
    #                                                 'Table 6—Overtime rates for shiftwork'],
    #                           'reasoning_summary': 'No reasoning summary provided.'},
    #  'saturday_overtime_rate': {'status': 'needs_review',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                                 'nonshift-overtime-rate-casual',
    #                                                 'shiftwork-overtime-rate-full-time-part-time',
    #                                                 'shiftwork-overtime-rate-casual',
    #                                                 'nonshift-overtime-minimum-3-hours-saturday'],
    #                             'clause_references': ['clause 21.4(a)',
    #                                                   'clause 21.4(b)',
    #                                                   'clause 28.1',
    #                                                   'Table 6—Overtime rates for '
    #                                                   'shiftwork'],
    #                             'reasoning_summary': 'No reasoning summary provided.'},
    #  'saturday_penalty_rate': {'status': 'needs_review',
    #                            'source_ruleset_keys': ['penalties'],
    #                            'source_rule_ids': ['ordinary-hours-saturday-24-2'],
    #                            'clause_references': ['clause 24.2', 'clause 24.1'],
    #                            'reasoning_summary': 'No reasoning summary provided.'},
    #  'sunday_penalty_rate': {'status': 'needs_review',
    #                          'source_ruleset_keys': ['penalties'],
    #                          'source_rule_ids': ['ordinary-hours-sunday-24-3',
    #                                              'shiftwork-penalty-rates-31-1-saturday-sunday-public-holiday'],
    #                          'clause_references': ['clause 24.3(a)',
    #                                                'clause 24.3(b)',
    #                                                'clause 24.3(c)',
    #                                                'clause 24.1',
    #                                                'clause 31.1',
    #                                                'Table 7—Penalty rates for shiftwork'],
    #                          'reasoning_summary': 'No reasoning summary provided.'},
    #  'apply_span_overtime': {'status': 'needs_review',
    #                          'source_ruleset_keys': ['overtime_creation'],
    #                          'source_rule_ids': ['general-spread-of-hours-boundary',
    #                                              'general-directed-hours-overtime'],
    #                          'clause_references': ['13.3', '13.4', '13.5', '21.1(c)'],
    #                          'reasoning_summary': 'No reasoning summary provided.'},
    #  'span_overtime_hour': {'status': 'needs_review',
    #                         'source_ruleset_keys': ['overtime_creation'],
    #                         'source_rule_ids': ['general-spread-of-hours-boundary'],
    #                         'clause_references': ['13.3', '13.4', '13.5', '21.1(c)'],
    #                         'reasoning_summary': 'No reasoning summary provided.'},
    #  'gap_penalty_hours': {'status': 'needs_review',
    #                        'source_ruleset_keys': [],
    #                        'source_rule_ids': [],
    #                        'clause_references': [],
    #                        'reasoning_summary': 'No field evidence was returned by the '
    #                                             'model response.'},
    #  'gap_penalty_rate': {'status': 'needs_review',
    #                       'source_ruleset_keys': [],
    #                       'source_rule_ids': [],
    #                       'clause_references': [],
    #                       'reasoning_summary': 'No field evidence was returned by the '
    #                                            'model response.'},
    #  'two_tier_overtime': {'status': 'needs_review',
    #                        'source_ruleset_keys': ['overtime_consequence'],
    #                        'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                            'nonshift-overtime-rate-casual',
    #                                            'shiftwork-overtime-rate-full-time-part-time',
    #                                            'shiftwork-overtime-rate-casual'],
    #                        'clause_references': ['clause 21.4(a)',
    #                                              'clause 28.1',
    #                                              'Table 6—Overtime rates for shiftwork'],
    #                        'reasoning_summary': 'No reasoning summary provided.'},
    #  'two_tier_overtime_threshold': {'status': 'needs_review',
    #                                  'source_ruleset_keys': ['overtime_consequence'],
    #                                  'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                                      'nonshift-overtime-rate-casual',
    #                                                      'shiftwork-overtime-rate-full-time-part-time',
    #                                                      'shiftwork-overtime-rate-casual'],
    #                                  'clause_references': ['clause 21.4(a)',
    #                                                        'clause 28.1',
    #                                                        'Table 6—Overtime rates for '
    #                                                        'shiftwork'],
    #                                  'reasoning_summary': 'No reasoning summary provided.'},
    #  'penalties': {'status': 'needs_review',
    #                'source_ruleset_keys': ['overtime_consequence', 'penalties'],
    #                'source_rule_ids': ['meal-break-workthrough-15-4',
    #                                    'shiftwork-penalty-rates-31-1-afternoon-night',
    #                                    'shiftwork-penalty-rates-31-1-permanent-night',
    #                                    'shiftwork-penalty-rates-31-1-saturday-sunday-public-holiday'],
    #                'clause_references': ['clause 15.4',
    #                                      'clause 31.1',
    #                                      'Table 7—Penalty rates for shiftwork'],
    #                'reasoning_summary': 'No reasoning summary provided.'},
    #  'hours_pen_rules': {'status': 'needs_review',
    #                      'source_ruleset_keys': [],
    #                      'source_rule_ids': [],
    #                      'clause_references': [],
    #                      'reasoning_summary': 'No reasoning summary provided.'},
    #  'weekend_rules': {'status': 'needs_review',
    #                    'source_ruleset_keys': ['overtime_consequence', 'penalties'],
    #                    'source_rule_ids': ['ordinary-hours-saturday-24-2',
    #                                        'ordinary-hours-sunday-24-3',
    #                                        'shiftwork-penalty-rates-31-1-saturday-sunday-public-holiday',
    #                                        'shiftwork-overtime-rate-full-time-part-time',
    #                                        'shiftwork-overtime-rate-casual',
    #                                        'shiftwork-not-cumulative-on-overtime-28-2'],
    #                    'clause_references': ['clause 24.1',
    #                                          'clause 24.2',
    #                                          'clause 24.3(a)',
    #                                          'clause 24.3(b)',
    #                                          'clause 24.3(c)',
    #                                          'clause 28.1',
    #                                          'clause 28.2',
    #                                          'clause 31.1'],
    #                    'reasoning_summary': 'No reasoning summary provided.'}}

    # GENERATION_METADATA = {'schema_version': 'calculator-rules-python-v1',
    #  'award_code': 'MA000002',
    #  'award_title': 'This is the Clerks—Private Sector Award 2020.'}
