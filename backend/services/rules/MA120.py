"""Rule engine for award pay calculations."""


class MA000120Rules:
    """Business rules for award MA000120 pay calculations."""

    ORDINARY_HOURS_LIMIT_DAILY = 8
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2
    SUNDAY_OVERTIME_RATE = 2
    SATURDAY_OVERTIME_RATE = 1.5
    SATURDAY_PENALTY_RATE = 0.5
    SUNDAY_PENALTY_RATE = None
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_HOUR = 18.5
    GAP_PENALTY_HOURS = 10
    GAP_PENALTY_RATE = 1
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 2
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    PENALTIES = {'early_morning_shift_loading': {'type': 'shift_based',
                                     'basis': 'start',
                                     'start': 0,
                                     'end': 6,
                                     'rate': 0.1,
                                     'description': 'Shiftworker early morning shift '
                                                    'loading',
                                     'applies_to': ['shift']},
     'afternoon_shift_loading': {'type': 'shift_based',
                                 'basis': 'start',
                                 'start': 12,
                                 'end': 18,
                                 'rate': 0.15,
                                 'description': 'Shiftworker afternoon shift loading',
                                 'applies_to': ['shift']},
     'rotating_night_shift_loading': {'type': 'shift_based',
                                      'basis': 'start',
                                      'start': 18,
                                      'end': 24,
                                      'rate': 0.175,
                                      'description': 'Shiftworker rotating night shift '
                                                     'loading',
                                      'applies_to': ['shift']}}
    HOURS_PEN_RULES = {}
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': True}, 'Sunday': {'is_overtime': True}},
     'shift': {'Saturday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5},
               'Sunday': {'is_overtime': True}}}
    DEFAULT_BREAK = 0.5

    # FIELD_EVIDENCE = {'ordinary_hours_limit_daily': {'status': 'derived',
    #                                 'source_ruleset_keys': ['overtime_creation'],
    #                                 'source_rule_ids': ['daily-ordinary-hours-limit-and-agreement-extension',
    #                                                     'shiftworker-average-thirty-eight-hours'],
    #                                 'clause_references': ['21.2', '23.4(a)', '23.4(b)'],
    #                                 'reasoning_summary': 'The reviewed rules do not '
    #                                                      'provide a different daily limit '
    #                                                      'for shiftworkers, so the '
    #                                                      'standard daily ordinary-hours '
    #                                                      'limit of 8 hours is the live '
    #                                                      'threshold.',
    #                                 'special_case_notes': 'The shiftworker rule in the '
    #                                                       'reviewed JSON addresses weekly '
    #                                                       'average ordinary hours, not a '
    #                                                       'separate daily ordinary-hours '
    #                                                       'limit. If a worker has an '
    #                                                       'individual agreement allowing '
    #                                                       'up to 10 hours, that is a '
    #                                                       'special case.'},
    #  'ordinary_hours_limit_weekly': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_creation'],
    #                                  'source_rule_ids': ['shiftworker-average-thirty-eight-hours'],
    #                                  'clause_references': ['23.4(a)', '23.4(b)'],
    #                                  'reasoning_summary': 'The shiftworker rule expressly '
    #                                                       'states ordinary hours inclusive '
    #                                                       'of meal breaks must not exceed '
    #                                                       'an average of 38 hours per week '
    #                                                       'over a 1, 2 or 4 week cycle.',
    #                                  'special_case_notes': 'This is the standard weekly '
    #                                                        'threshold for shiftworkers. '
    #                                                        'Daily limits are not '
    #                                                        'separately specified in the '
    #                                                        'reviewed shiftworker rule.'},
    #  'day_worker_ordinary_hours_daily': {'status': 'derived',
    #                                      'source_ruleset_keys': ['overtime_creation'],
    #                                      'source_rule_ids': ['daily-ordinary-hours-limit-and-agreement-extension',
    #                                                          'full-time-outside-ordinary-hours',
    #                                                          'part-time-over-eight-hours-in-a-day',
    #                                                          'casual-over-eight-hours-or-thirty-eight-hours'],
    #                                      'clause_references': ['21.2',
    #                                                            '23.1(a)',
    #                                                            '23.1(b)',
    #                                                            '23.1(c)'],
    #                                      'reasoning_summary': 'Standard daily '
    #                                                           'ordinary-hours limit is 8 '
    #                                                           'hours, with an individual '
    #                                                           'agreement allowing up to 10 '
    #                                                           'hours. This limit is '
    #                                                           'supported across the daily '
    #                                                           'ordinary-hours rule and the '
    #                                                           'employee-specific overtime '
    #                                                           'creation rules.',
    #                                      'special_case_notes': 'Use 8 hours as the '
    #                                                            'standard live threshold. A '
    #                                                            'separate individual '
    #                                                            'agreement can extend daily '
    #                                                            'ordinary hours to 10 '
    #                                                            'hours; do not use that as '
    #                                                            'the default calculator '
    #                                                            'threshold.'},
    #  'day_worker_ordinary_hours_weekly': {'status': 'derived',
    #                                       'source_ruleset_keys': ['overtime_creation'],
    #                                       'source_rule_ids': ['full-time-outside-ordinary-hours',
    #                                                           'daily-standalone-calculation-for-overtime',
    #                                                           'shiftworker-average-thirty-eight-hours'],
    #                                       'clause_references': ['21.1',
    #                                                             '23.2(a)',
    #                                                             '23.2(b)',
    #                                                             '23.4(a)',
    #                                                             '23.4(b)'],
    #                                       'reasoning_summary': 'Full-time ordinary hours '
    #                                                            'average 38 hours per week '
    #                                                            'over a 1, 2 or 4 week '
    #                                                            'cycle, and the rules also '
    #                                                            'state shiftworkers average '
    #                                                            '38 hours per week. The '
    #                                                            'standard live weekly '
    #                                                            'threshold is 38 hours.',
    #                                       'special_case_notes': 'For the calculator, use '
    #                                                             '38 hours as the standard '
    #                                                             'weekly threshold. The '
    #                                                             'rules also state each day '
    #                                                             'stands alone for overtime '
    #                                                             'calculation, so weekly '
    #                                                             'averaging does not '
    #                                                             'replace daily checks.'},
    #  'standard_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['merged-23-2a-full-time-part-time-overtime-rates',
    #                                                 'merged-23-2b-casual-overtime-rates'],
    #                             'clause_references': ['23.2(a)', '23.2(b)'],
    #                             'reasoning_summary': 'The standard overtime rate is 150% '
    #                                                  'for full-time/part-time employees '
    #                                                  'and 175% for casuals. The calculator '
    #                                                  'standard live multiplier is the '
    #                                                  'first overtime tier, so 1.5 is the '
    #                                                  'general default.',
    #                             'special_case_notes': 'Casual employees have a different '
    #                                                   'first overtime rate of 1.75, but '
    #                                                   'the standard live overtime '
    #                                                   'multiplier for the main calculator '
    #                                                   'should be 1.5.'},
    #  'extended_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['merged-23-2a-full-time-part-time-overtime-rates',
    #                                                 'merged-23-2b-casual-overtime-rates',
    #                                                 'cla-23-5-saturday-overtime-rates'],
    #                             'clause_references': ['23.2(a)', '23.2(b)', '23.5(a)'],
    #                             'reasoning_summary': 'The reviewed overtime rules clearly '
    #                                                  'provide a first tier and a higher '
    #                                                  'tier after 2 hours for '
    #                                                  'full-time/part-time, casual, and '
    #                                                  'Saturday overtime. | The higher '
    #                                                  'overtime tier is 200% for '
    #                                                  'full-time/part-time employees, '
    #                                                  'casuals, and Saturday overtime after '
    #                                                  'the first 2 hours.',
    #                             'special_case_notes': 'Saturday overtime also has a '
    #                                                   'two-tier structure. The threshold '
    #                                                   'is 2 hours. | This is the standard '
    #                                                   'higher tier used by the calculator, '
    #                                                   'although casual first-tier overtime '
    #                                                   'is 175% before the 200% tier.'},
    #  'sunday_overtime_rate': {'status': 'derived',
    #                           'source_ruleset_keys': ['overtime_consequence'],
    #                           'source_rule_ids': ['cla-23-5-sunday-overtime-rate'],
    #                           'clause_references': ['23.5(c)'],
    #                           'reasoning_summary': 'All time worked on a Sunday is paid at '
    #                                                'double time.',
    #                           'special_case_notes': 'No separate first-tier Sunday '
    #                                                 'overtime rate is provided in the '
    #                                                 'reviewed rules.'},
    #  'saturday_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['cla-23-5-saturday-overtime-rates'],
    #                             'clause_references': ['23.5(a)'],
    #                             'reasoning_summary': 'Saturday overtime is paid at 150% '
    #                                                  'for the first 2 overtime hours.',
    #                             'special_case_notes': 'The Saturday rule has a second tier '
    #                                                   'after 2 hours at 200%; this field '
    #                                                   'records the first tier above base.'},
    #  'saturday_penalty_rate': {'status': 'derived',
    #                            'source_ruleset_keys': ['overtime_consequence', 'penalties'],
    #                            'source_rule_ids': ['cla-23-5-saturday-overtime-rates',
    #                                                'shiftworkers-saturday-ordinary-hours-time-and-a-half'],
    #                            'clause_references': ['23.5(a)', '23.5(b)'],
    #                            'reasoning_summary': 'For day workers, Saturday work is '
    #                                                 'treated as overtime rather than a '
    #                                                 'separate penalty loading in the '
    #                                                 'reviewed rules. | Shiftworkers '
    #                                                 'working ordinary hours on Saturday '
    #                                                 'receive time and a half, so the '
    #                                                 'penalty loading above base is 0.5.',
    #                            'special_case_notes': 'Not encoded as a penalty loading '
    #                                                  'because the rule is an overtime rate '
    #                                                  'schedule (150% first 2 hours, 200% '
    #                                                  'thereafter). | This captures only '
    #                                                  'the ordinary-hours Saturday penalty '
    #                                                  'for shiftworkers, not Saturday '
    #                                                  'overtime.'},
    #  'sunday_penalty_rate': {'status': 'not_found',
    #                          'source_ruleset_keys': ['overtime_consequence'],
    #                          'source_rule_ids': ['cla-23-5-sunday-overtime-rate'],
    #                          'clause_references': ['23.5(c)'],
    #                          'reasoning_summary': 'Sunday work is paid at double time as '
    #                                               'overtime; no separate penalty loading '
    #                                               'is provided for day workers. | The '
    #                                               'reviewed rules do not provide a '
    #                                               'separate shiftworker Sunday penalty '
    #                                               'loading; Sunday work is simply paid at '
    #                                               'double time.',
    #                          'special_case_notes': ''},
    #  'apply_span_overtime': {'status': 'derived',
    #                          'source_ruleset_keys': ['overtime_creation'],
    #                          'source_rule_ids': ['ordinary-hours-span-and-broken-shift-spread',
    #                                              'full-time-outside-ordinary-hours',
    #                                              'part-time-over-eight-hours-in-a-day',
    #                                              'casual-over-eight-hours-or-thirty-eight-hours'],
    #                          'clause_references': ['21.3', '23.1(a)', '23.1(b)', '23.1(c)'],
    #                          'reasoning_summary': 'Day workers have an ordinary-hours span '
    #                                               'of 6:00 am to 6:30 pm, and work outside '
    #                                               'that span is overtime. | The reviewed '
    #                                               'rule states the ordinary-hours span and '
    #                                               'notes the broken-shift spread '
    #                                               'exception.',
    #                          'special_case_notes': 'Broken-shift spread can extend to a '
    #                                                '12-hour spread, but the standard live '
    #                                                'span cutoff is the ordinary 6:00 am to '
    #                                                '6:30 pm span. | Use 6:00 am to 6:30 pm '
    #                                                'as the standard live span. '
    #                                                'Broken-shift arrangements need '
    #                                                'separate handling if implemented.'},
    #  'span_overtime_hour': {'status': 'derived',
    #                         'source_ruleset_keys': ['overtime_creation'],
    #                         'source_rule_ids': ['ordinary-hours-span-and-broken-shift-spread',
    #                                             'full-time-outside-ordinary-hours',
    #                                             'part-time-over-eight-hours-in-a-day',
    #                                             'casual-over-eight-hours-or-thirty-eight-hours'],
    #                         'clause_references': ['21.3', '23.1(a)', '23.1(b)', '23.1(c)'],
    #                         'reasoning_summary': 'Day workers have an ordinary-hours span '
    #                                              'of 6:00 am to 6:30 pm, and work outside '
    #                                              'that span is overtime. | The '
    #                                              'ordinary-hours span ends at 6:30 pm, '
    #                                              'which is 18.5 hours in 24-hour time. | '
    #                                              'The reviewed rule states the '
    #                                              'ordinary-hours span and notes the '
    #                                              'broken-shift spread exception.',
    #                         'special_case_notes': 'Broken-shift spread can extend to a '
    #                                               '12-hour spread, but the standard live '
    #                                               'span cutoff is the ordinary 6:00 am to '
    #                                               '6:30 pm span. | This is the best single '
    #                                               'live cutoff for the calculator. The '
    #                                               'rule also refers to broken-shift spread '
    #                                               'of 12 hours, which is not captured by a '
    #                                               'single cutoff. | Use 6:00 am to 6:30 pm '
    #                                               'as the standard live span. Broken-shift '
    #                                               'arrangements need separate handling if '
    #                                               'implemented.'},
    #  'gap_penalty_hours': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_creation', 'penalties'],
    #                        'source_rule_ids': ['insufficient-rest-between-work-periods',
    #                                            'break-between-work-periods-10-hour-rest'],
    #                        'clause_references': ['22.3(a)', '22.3(b)', '22.3(c)'],
    #                        'reasoning_summary': 'The award requires a 10-hour rest period '
    #                                             'between shifts, with a possible reduction '
    #                                             'to 8 hours by agreement. | The default '
    #                                             'minimum break between work periods is 10 '
    #                                             'hours. | The reviewed rules state a '
    #                                             'default 10-hour break with an '
    #                                             'agreement-based reduction to 8 hours.',
    #                        'special_case_notes': 'This is the standard live rule. The '
    #                                              'agreement-reduced 8-hour case is a '
    #                                              'special case. | By agreement, the break '
    #                                              'can be reduced to not less than 8 hours, '
    #                                              'but 10 hours is the standard calculator '
    #                                              'threshold. | The calculator should use '
    #                                              '10 hours as the live threshold and '
    #                                              'retain the 8-hour agreed exception as a '
    #                                              'special case.'},
    #  'gap_penalty_rate': {'status': 'derived',
    #                       'source_ruleset_keys': ['overtime_creation',
    #                                               'penalties',
    #                                               'overtime_consequence'],
    #                       'source_rule_ids': ['insufficient-rest-between-work-periods',
    #                                           'break-between-work-periods-10-hour-rest',
    #                                           'merged-22-3b-rest-period-release-pay',
    #                                           'break-between-work-periods-insufficient-rest-consequence'],
    #                       'clause_references': ['22.3(a)', '22.3(b)', '22.3(c)'],
    #                       'reasoning_summary': 'The award requires a 10-hour rest period '
    #                                            'between shifts, with a possible reduction '
    #                                            'to 8 hours by agreement. | If the employee '
    #                                            'recommences without the required rest, the '
    #                                            'award pays overtime rates until released '
    #                                            'for 10 consecutive hours. The loading '
    #                                            'above base for the standard overtime rate '
    #                                            'is 1.0. | The reviewed rules state a '
    #                                            'default 10-hour break with an '
    #                                            'agreement-based reduction to 8 hours.',
    #                       'special_case_notes': 'This is the standard live rule. The '
    #                                             'agreement-reduced 8-hour case is a '
    #                                             'special case. | The paid rate may be 150% '
    #                                             'or higher depending on employee type and '
    #                                             'overtime context; the calculator field '
    #                                             'asks for the loading above base, so the '
    #                                             'standard value is 1.0. | The calculator '
    #                                             'should use 10 hours as the live threshold '
    #                                             'and retain the 8-hour agreed exception as '
    #                                             'a special case.'},
    #  'penalties': {'status': 'derived',
    #                'source_ruleset_keys': ['penalties',
    #                                        'overtime_consequence',
    #                                        'overtime_creation'],
    #                'source_rule_ids': ['shiftwork-loadings',
    #                                    'casual-loading-and-minimum-engagement',
    #                                    'broken-shift-allowance',
    #                                    'meal-allowance-for-unnotified-overtime',
    #                                    'saturday-overtime-time-and-a-half-first-two-hours-double-time-after',
    #                                    'sunday-double-time-all-hours',
    #                                    'public-holiday-double-time-and-a-half-all-hours',
    #                                    'weekend-and-public-holiday-minimum-payment',
    #                                    'roster-change-without-7-days-notice',
    #                                    'roster-change-emergency-carve-out'],
    #                'clause_references': ['23.4(c)',
    #                                      '23.4(d)(i)',
    #                                      '23.4(d)(ii)',
    #                                      '23.4(d)(iii)',
    #                                      '23.4(d)(iv)',
    #                                      '10.5(a)',
    #                                      '15.1',
    #                                      '15.5',
    #                                      '21.7(b)(i)',
    #                                      '21.7(b)(ii)',
    #                                      '23.5(a)',
    #                                      '23.5(c)',
    #                                      '23.5(d)',
    #                                      '23.5(e)',
    #                                      '23.5(f)'],
    #                'reasoning_summary': 'The reviewed shiftwork clause provides '
    #                                     'whole-shift loadings for early morning, '
    #                                     'afternoon, and rotating night shifts that can be '
    #                                     'represented with start-time windows. | The '
    #                                     'reviewed weekday penalties are shift-based '
    #                                     'whole-shift loadings rather than time-based '
    #                                     'penalties tied to duration. | These items are '
    #                                     'excluded because the weekday penalty field should '
    #                                     'only contain ordinary weekday penalties that can '
    #                                     'be represented as numeric time windows.',
    #                'special_case_notes': 'Non-rotating night shift systems are excluded '
    #                                      'from the live list because they are a special '
    #                                      'classification-based case rather than a simple '
    #                                      'weekday time window. | The shiftwork loadings '
    #                                      'are the only standard weekday penalty rows '
    #                                      'supported by the reviewed rules.'},
    #  'hours_pen_rules': {'status': 'defaulted',
    #                      'source_ruleset_keys': [],
    #                      'source_rule_ids': [],
    #                      'clause_references': [],
    #                      'reasoning_summary': 'No separate hours_pen_rules mapping is '
    #                                           'generated in step 6.1 yet.',
    #                      'special_case_notes': ''},
    #  'weekend_rules': {'status': 'derived',
    #                    'source_ruleset_keys': ['overtime_consequence', 'penalties'],
    #                    'source_rule_ids': ['cla-23-5-saturday-overtime-rates',
    #                                        'cla-23-5-sunday-overtime-rate',
    #                                        'shiftworkers-saturday-ordinary-hours-time-and-a-half'],
    #                    'clause_references': ['23.5(a)', '23.5(c)', '23.5(b)'],
    #                    'reasoning_summary': 'Saturday work is treated as overtime for day '
    #                                         'workers, with a two-tier overtime rate. | All '
    #                                         'Sunday work is paid at double time as an '
    #                                         'overtime treatment. | Shiftworkers required '
    #                                         'to work ordinary hours on Saturday are paid '
    #                                         'time and a half for those ordinary hours, '
    #                                         'which is a penalty rather than overtime. | '
    #                                         'Sunday work is paid at double time. | For day '
    #                                         'workers, Saturday work is treated as overtime '
    #                                         'rather than a separate penalty loading in the '
    #                                         'reviewed rules. | Sunday work is paid at '
    #                                         'double time as overtime; no separate penalty '
    #                                         'loading is provided for day workers. | '
    #                                         'Shiftworkers working ordinary hours on '
    #                                         'Saturday receive time and a half, so the '
    #                                         'penalty loading above base is 0.5. | The '
    #                                         'reviewed rules do not provide a separate '
    #                                         'shiftworker Sunday penalty loading; Sunday '
    #                                         'work is simply paid at double time.',
    #                    'special_case_notes': 'Shiftworkers have a separate Saturday '
    #                                          'ordinary-hours penalty at time and a half '
    #                                          'for ordinary Saturday hours, but the '
    #                                          'standard day-worker treatment is overtime. | '
    #                                          'Saturday overtime for shiftworkers may also '
    #                                          'apply if the work is overtime; this field '
    #                                          'records the ordinary-hours Saturday penalty. '
    #                                          '| No separate shiftworker Sunday '
    #                                          'ordinary-hours penalty is identified in the '
    #                                          'reviewed rules. | Not encoded as a penalty '
    #                                          'loading because the rule is an overtime rate '
    #                                          'schedule (150% first 2 hours, 200% '
    #                                          'thereafter). | This captures only the '
    #                                          'ordinary-hours Saturday penalty for '
    #                                          'shiftworkers, not Saturday overtime.'},
    #  'two_tier_overtime': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_consequence'],
    #                        'source_rule_ids': ['merged-23-2a-full-time-part-time-overtime-rates',
    #                                            'merged-23-2b-casual-overtime-rates',
    #                                            'cla-23-5-saturday-overtime-rates'],
    #                        'clause_references': ['23.2(a)', '23.2(b)', '23.5(a)'],
    #                        'reasoning_summary': 'The reviewed overtime rules clearly '
    #                                             'provide a first tier and a higher tier '
    #                                             'after 2 hours for full-time/part-time, '
    #                                             'casual, and Saturday overtime.',
    #                        'special_case_notes': 'Saturday overtime also has a two-tier '
    #                                              'structure. The threshold is 2 hours.'},
    #  'two_tier_overtime_threshold': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_consequence'],
    #                                  'source_rule_ids': ['merged-23-2a-full-time-part-time-overtime-rates',
    #                                                      'merged-23-2b-casual-overtime-rates',
    #                                                      'cla-23-5-saturday-overtime-rates'],
    #                                  'clause_references': ['23.2(a)', '23.2(b)', '23.5(a)'],
    #                                  'reasoning_summary': 'The reviewed overtime rules '
    #                                                       'clearly provide a first tier '
    #                                                       'and a higher tier after 2 hours '
    #                                                       'for full-time/part-time, '
    #                                                       'casual, and Saturday overtime. '
    #                                                       '| The higher overtime rate '
    #                                                       'applies after the first 2 hours '
    #                                                       'of overtime.',
    #                                  'special_case_notes': 'Saturday overtime also has a '
    #                                                        'two-tier structure. The '
    #                                                        'threshold is 2 hours. | '
    #                                                        'Applies as a general two-tier '
    #                                                        'overtime threshold for the '
    #                                                        'reviewed rules.'},
    #  'use_contracted_hours_for_pt_overtime': {'status': 'defaulted',
    #                                           'source_ruleset_keys': [],
    #                                           'source_rule_ids': [],
    #                                           'clause_references': [],
    #                                           'reasoning_summary': 'Defaulted to True '
    #                                                                'because the source '
    #                                                                'rulesets do not answer '
    #                                                                'this field.',
    #                                           'special_case_notes': ''},
    #  'pt_employees_entitled_to_contracted_topup': {'status': 'defaulted',
    #                                                'source_ruleset_keys': [],
    #                                                'source_rule_ids': [],
    #                                                'clause_references': [],
    #                                                'reasoning_summary': 'Defaulted to True '
    #                                                                     'because the '
    #                                                                     'source rulesets '
    #                                                                     'do not answer '
    #                                                                     'this field.',
    #                                                'special_case_notes': ''},
    #  'ft_employees_entitled_to_contracted_topup': {'status': 'defaulted',
    #                                                'source_ruleset_keys': [],
    #                                                'source_rule_ids': [],
    #                                                'clause_references': [],
    #                                                'reasoning_summary': 'Defaulted to True '
    #                                                                     'because the '
    #                                                                     'source rulesets '
    #                                                                     'do not answer '
    #                                                                     'this field.',
    #                                                'special_case_notes': ''}}

    # GENERATION_METADATA = {'schema_version': 'calculator-rules-python-v1', 'award_code': 'MA000120'}
