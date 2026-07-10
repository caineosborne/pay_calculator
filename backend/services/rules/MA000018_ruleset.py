"""Rule engine for award pay calculations."""


class MA000018Rules:
    """Business rules for award MA000018 pay calculations."""

    ORDINARY_HOURS_LIMIT_DAILY = 8
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2
    SUNDAY_OVERTIME_RATE = 2
    SATURDAY_OVERTIME_RATE = 2
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_HOUR = 18
    GAP_PENALTY_HOURS = 10
    GAP_PENALTY_RATE = 1
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 2
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday','Sunday']
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    PENALTIES = {'afternoon_shift': {'type': 'shift_based',
                         'basis': 'start',
                         'start': 10,
                         'end': 13,
                         'rate': 0.1,
                         'description': 'Shift allowance for shifts commencing 10:00 to '
                                        'before 13:00.',
                         'applies_to': ['day', 'shift']},
     'afternoon_shift_allowance_125': {'type': 'shift_based',
                                       'basis': 'start',
                                       'start': 13,
                                       'end': 16,
                                       'rate': 0.125,
                                       'description': 'Shift allowance for shifts '
                                                      'commencing 13:00 to before 16:00.',
                                       'applies_to': ['day', 'shift']},
     'afternoon_night_shift': {'type': 'shift_based',
                               'basis': 'start',
                               'start': 16,
                               'end': 4,
                               'rate': 0.15,
                               'description': 'Shift allowance for shifts commencing 16:00 '
                                              'to before 04:00.',
                               'applies_to': ['day', 'shift']},
     'early_morning_shift': {'type': 'shift_based',
                             'basis': 'start',
                             'start': 4,
                             'end': 6,
                             'rate': 0.1,
                             'description': 'Shift allowance for shifts commencing 04:00 '
                                            'to before 06:00.',
                             'applies_to': ['day', 'shift']}}
    HOURS_PEN_RULES = {}
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': True}, 'Sunday': {'is_overtime': True}},
     'shift': {'Saturday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5},
               'Sunday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.75}}}
    DEFAULT_BREAK = 0.5

    # FIELD_EVIDENCE = {'ordinary_hours_limit_daily': {'status': 'not_found',
    #                                 'source_ruleset_keys': ['overtime_creation'],
    #                                 'source_rule_ids': ['all-employees-day-shift-and-night-shift-length-limits'],
    #                                 'clause_references': ['22.1(c)'],
    #                                 'reasoning_summary': 'The reviewed rules say '
    #                                                      'shiftworkers have ordinary-hours '
    #                                                      'limits of 8 hours for a day '
    #                                                      'shift and 10 hours for a night '
    #                                                      'shift, but do not support one '
    #                                                      'single numeric daily limit '
    #                                                      'across shiftworker day/night '
    #                                                      'types.',
    #                                 'special_case_notes': 'Two different daily limits '
    #                                                       'exist depending on day shift '
    #                                                       'versus night shift; the '
    #                                                       'questionnaire requires a single '
    #                                                       'live value.'},
    #  'ordinary_hours_limit_weekly': {'status': 'needs_review',
    #                                  'source_ruleset_keys': ['overtime_creation'],
    #                                  'source_rule_ids': ['all-employees-ordinary-hours-week-fortnight-cycle-and-span',
    #                                                      'all-employees-day-shift-and-night-shift-length-limits'],
    #                                  'clause_references': ['22.1', '22.2(a)', '22.1(c)'],
    #                                  'reasoning_summary': 'The source gives shiftworkers '
    #                                                       'shift-length caps (8 or 10 '
    #                                                       'hours) and a general 38-hour '
    #                                                       'ordinary-hours framework, but '
    #                                                       'does not clearly state a '
    #                                                       'distinct weekly shiftworker cap '
    #                                                       'separate from the general '
    #                                                       'ordinary-hours rule.',
    #                                  'special_case_notes': 'Using the general 38-hour '
    #                                                        'weekly framework as the best '
    #                                                        'live proxy; the reviewed text '
    #                                                        'may also operate through '
    #                                                        'roster/shift-length limits '
    #                                                        'rather than a distinct '
    #                                                        'shiftworker weekly cap.'},
    #  'day_worker_ordinary_hours_daily': {'status': 'not_found',
    #                                      'source_ruleset_keys': ['overtime_creation'],
    #                                      'source_rule_ids': [],
    #                                      'clause_references': ['22.2(a)'],
    #                                      'reasoning_summary': 'The reviewed rules state a '
    #                                                           'day-worker span of 6.00 am '
    #                                                           'to 6.00 pm Monday to '
    #                                                           'Friday, but they do not '
    #                                                           'clearly isolate a numeric '
    #                                                           'daily ordinary-hours limit '
    #                                                           'for day workers in the '
    #                                                           'supplied JSON.',
    #                                      'special_case_notes': 'Day-worker span is '
    #                                                            'provided, but the source '
    #                                                            'does not clearly state a '
    #                                                            'separate daily hour cap '
    #                                                            'for the calculator.'},
    #  'day_worker_ordinary_hours_weekly': {'status': 'derived',
    #                                       'source_ruleset_keys': ['overtime_creation'],
    #                                       'source_rule_ids': ['full-time-ordinary-hours-boundary-38-per-week',
    #                                                           'part-time-38-per-week-or-76-per-fortnight',
    #                                                           'casual-ordinary-hours-boundary-38-per-week'],
    #                                       'clause_references': ['10.2',
    #                                                             '22.1',
    #                                                             '25.1(b)(i)',
    #                                                             '10.4(a)'],
    #                                       'reasoning_summary': 'The reviewed rules '
    #                                                            'repeatedly set '
    #                                                            'ordinary-hours boundaries '
    #                                                            'at 38 hours per week for '
    #                                                            'full-time and casual '
    #                                                            'employees, and also '
    #                                                            'reference 38 hours as a '
    #                                                            'weekly overtime trigger, '
    #                                                            'so 38 is the standard '
    #                                                            'weekly limit.',
    #                                       'special_case_notes': 'This is the standard '
    #                                                             'weekly boundary used for '
    #                                                             'a first-pass calculator, '
    #                                                             'even though some cohorts '
    #                                                             'also have separate '
    #                                                             'daily/rostered triggers.'},
    #  'standard_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['full-time-overtime-rates-general',
    #                                                 'part-time-overtime-rates-general',
    #                                                 'casual-overtime-rates-general'],
    #                             'clause_references': ['25.1(a)(i)(A)',
    #                                                   '25.1(b)(i)',
    #                                                   '25.1(c)(i)'],
    #                             'reasoning_summary': 'Across the reviewed overtime tables, '
    #                                                  'the standard first-tier overtime '
    #                                                  'rate is 150% for weekday overtime, '
    #                                                  'which corresponds to a multiplier of '
    #                                                  '1.5.',
    #                             'special_case_notes': 'This is the standard first overtime '
    #                                                   'tier; some days or thresholds move '
    #                                                   'straight to higher rates.'},
    #  'extended_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['full-time-overtime-rates-general',
    #                                                 'part-time-overtime-rates-general',
    #                                                 'casual-overtime-rates-general'],
    #                             'clause_references': ['25.1(a)(i)(A)',
    #                                                   '25.1(a)(i)(B)',
    #                                                   '25.1(b)(i)',
    #                                                   '25.1(c)(i)'],
    #                             'reasoning_summary': 'The overtime tables show a first '
    #                                                  'overtime tier and a higher '
    #                                                  'subsequent tier for Monday to Friday '
    #                                                  'overtime. | The reviewed tables '
    #                                                  'specify 200% after the first two '
    #                                                  'overtime hours for Monday to Friday '
    #                                                  'overtime, so the extended multiplier '
    #                                                  'is 2.0.',
    #                             'special_case_notes': 'Two-tier overtime applies on '
    #                                                   'standard weekday overtime tables; '
    #                                                   'weekend/public holiday rates are '
    #                                                   'separate fixed rates. | For casual '
    #                                                   'employees the equivalent higher '
    #                                                   'rate is 250% because casual loading '
    #                                                   'is already included; however the '
    #                                                   'standard higher overtime tier in '
    #                                                   'the award is 200% for the '
    #                                                   'non-casual tables.'},
    #  'sunday_overtime_rate': {'status': 'derived',
    #                           'source_ruleset_keys': ['overtime_consequence'],
    #                           'source_rule_ids': ['full-time-overtime-rates-general',
    #                                               'part-time-overtime-rates-general',
    #                                               'casual-overtime-rates-general'],
    #                           'clause_references': ['25.1(a)(i)(C)',
    #                                                 '25.1(b)(i)',
    #                                                 '25.1(c)(i)'],
    #                           'reasoning_summary': 'Sunday overtime is specified as 200% '
    #                                                'in the overtime tables.',
    #                           'special_case_notes': 'This is a fixed Sunday overtime rate, '
    #                                                 'not part of the weekday two-tier '
    #                                                 'structure.'},
    #  'saturday_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['full-time-overtime-rates-general',
    #                                                 'part-time-overtime-rates-general',
    #                                                 'casual-overtime-rates-general'],
    #                             'clause_references': ['25.1(a)(i)(C)',
    #                                                   '25.1(b)(i)',
    #                                                   '25.1(c)(i)'],
    #                             'reasoning_summary': 'Saturday overtime is specified as '
    #                                                  '200% in the overtime tables.',
    #                             'special_case_notes': 'This is a fixed Saturday overtime '
    #                                                   'rate, not part of the weekday '
    #                                                   'two-tier structure.'},
    #  'apply_span_overtime': {'status': 'derived',
    #                          'source_ruleset_keys': ['overtime_consequence',
    #                                                  'overtime_creation'],
    #                          'source_rule_ids': ['all-employees-ordinary-hours-week-fortnight-cycle-and-span',
    #                                              'meal-break-worked-through-overtime-rate'],
    #                          'clause_references': ['22.2(a)', '24.1(b)'],
    #                          'reasoning_summary': 'The reviewed rules say day-worker '
    #                                               'ordinary hours must fall between 6.00 '
    #                                               'am and 6.00 pm Monday to Friday, and '
    #                                               'work outside those boundaries may be '
    #                                               'overtime. | This is the plain-language '
    #                                               'span rule stated in the reviewed '
    #                                               'source.',
    #                          'special_case_notes': 'The award also contains other overtime '
    #                                                'triggers; this answer captures the '
    #                                                'ordinary day-worker span rule only. | '
    #                                                'This is a simplified live summary; the '
    #                                                'source also links outside-span work to '
    #                                                'overtime consequences.'},
    #  'span_overtime_hour': {'status': 'derived',
    #                         'source_ruleset_keys': ['overtime_consequence',
    #                                                 'overtime_creation'],
    #                         'source_rule_ids': ['all-employees-ordinary-hours-week-fortnight-cycle-and-span',
    #                                             'meal-break-worked-through-overtime-rate'],
    #                         'clause_references': ['22.2(a)', '24.1(b)'],
    #                         'reasoning_summary': 'The reviewed rules say day-worker '
    #                                              'ordinary hours must fall between 6.00 am '
    #                                              'and 6.00 pm Monday to Friday, and work '
    #                                              'outside those boundaries may be '
    #                                              'overtime. | The day-worker span cutoff '
    #                                              'is 6.00 pm, so the live cutoff hour is '
    #                                              '18. | This is the plain-language span '
    #                                              'rule stated in the reviewed source.',
    #                         'special_case_notes': 'The award also contains other overtime '
    #                                               'triggers; this answer captures the '
    #                                               'ordinary day-worker span rule only. | '
    #                                               'Morning cutoff at 6.00 am is also in '
    #                                               'the clause, but the questionnaire asks '
    #                                               'for one live cutoff. | This is a '
    #                                               'simplified live summary; the source '
    #                                               'also links outside-span work to '
    #                                               'overtime consequences.'},
    #  'gap_penalty_hours': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_creation',
    #                                                'penalties',
    #                                                'overtime_consequence'],
    #                        'source_rule_ids': ['rest-break-between-rostered-work',
    #                                            'rest-period-after-overtime-10-consecutive-hours-off-duty',
    #                                            'sleepover-insufficient-rest-gap-supporting-and-consequence-rule'],
    #                        'clause_references': ['22.4(a)',
    #                                              '22.4(b)',
    #                                              '25.1(d)(i)',
    #                                              '22.9(g)(iv)',
    #                                              '22.9(j)'],
    #                        'reasoning_summary': 'The reviewed rules require a minimum '
    #                                             'break between shifts, with 10 hours as '
    #                                             'the standard rule and an 8-hour reduction '
    #                                             'by agreement. | The standard minimum rest '
    #                                             'gap between rostered work periods is 10 '
    #                                             'hours. | The source contains the standard '
    #                                             '10-hour roster break, an 8-hour agreed '
    #                                             'reduction, and specific 10-hour and '
    #                                             '8-hour post-overtime/sleepover rest '
    #                                             'rules.',
    #                        'special_case_notes': 'There are also separate 10-hour rest '
    #                                              'consequences after overtime and '
    #                                              'sleepover work, but the calculator needs '
    #                                              'one standard gap rule. | The clause '
    #                                              'allows reduction to 8 hours by mutual '
    #                                              'agreement; that is not the standard live '
    #                                              'threshold. | These thresholds are '
    #                                              'context-specific and should not be '
    #                                              'conflated into one universal monetary '
    #                                              'rule.'},
    #  'gap_penalty_rate': {'status': 'derived',
    #                       'source_ruleset_keys': ['overtime_creation',
    #                                               'penalties',
    #                                               'overtime_consequence'],
    #                       'source_rule_ids': ['rest-break-between-rostered-work',
    #                                           'rest-period-after-overtime-10-consecutive-hours-off-duty',
    #                                           'sleepover-insufficient-rest-gap-supporting-and-consequence-rule'],
    #                       'clause_references': ['22.4(a)',
    #                                             '22.4(b)',
    #                                             '25.1(d)(i)',
    #                                             '22.9(g)(iv)',
    #                                             '22.9(j)'],
    #                       'reasoning_summary': 'The reviewed rules require a minimum break '
    #                                            'between shifts, with 10 hours as the '
    #                                            'standard rule and an 8-hour reduction by '
    #                                            'agreement. | The rest-gap clause itself '
    #                                            'sets a minimum break but does not state a '
    #                                            'general monetary breach loading in the '
    #                                            'reviewed rules. | The source contains the '
    #                                            'standard 10-hour roster break, an 8-hour '
    #                                            'agreed reduction, and specific 10-hour and '
    #                                            '8-hour post-overtime/sleepover rest rules.',
    #                       'special_case_notes': 'There are also separate 10-hour rest '
    #                                             'consequences after overtime and sleepover '
    #                                             'work, but the calculator needs one '
    #                                             'standard gap rule. | Separate '
    #                                             'overtime/rest-period clauses can create '
    #                                             'double-time consequences in specific '
    #                                             'circumstances, but not a single universal '
    #                                             'gap breach multiplier. | These thresholds '
    #                                             'are context-specific and should not be '
    #                                             'conflated into one universal monetary '
    #                                             'rule.'},
    #  'penalties': {'status': 'derived',
    #                'source_ruleset_keys': ['penalties'],
    #                'source_rule_ids': ['afternoon-and-night-shift-allowances-by-commencement-time',
    #                                    'shift-allowance-paid-for-entire-shift',
    #                                    'shiftworker-weekend-ordinary-hours-penalties',
    #                                    'casual-weekend-penalty-rates',
    #                                    'sleepover-conditions-allowance-and-non-emergency-work',
    #                                    'broken-shift-conditions-and-pay'],
    #                'clause_references': ['26.1',
    #                                      '26.2',
    #                                      '23.1',
    #                                      '23.2(a)',
    #                                      '23.2(b)',
    #                                      '22.9',
    #                                      '22.8'],
    #                'reasoning_summary': 'The reviewed rules provide '
    #                                     'commencement-time-based whole-shift allowances '
    #                                     'with numeric windows that can be represented '
    #                                     'directly. | No other standard weekday-only '
    #                                     'time-based penalty windows are clearly supported '
    #                                     'in the reviewed rules. | The source includes '
    #                                     'several non-weekday or special-context payment '
    #                                     'rules that should not be treated as standard '
    #                                     'weekday penalties.',
    #                'special_case_notes': 'These are allowances, not weekend or public '
    #                                      'holiday penalties. The allowance applies to the '
    #                                      'entire shift once the start-time condition is '
    #                                      'met. | Weekend penalties, casual loading, '
    #                                      'meal-break rules, sleepover rules, and '
    #                                      'rotation-dependent or non-time conditions were '
    #                                      'excluded from the live weekday penalty list. | '
    #                                      'Casual loading is not treated as a penalty '
    #                                      'rule.'},
    #  'hours_pen_rules': {'status': 'defaulted',
    #                      'source_ruleset_keys': [],
    #                      'source_rule_ids': [],
    #                      'clause_references': [],
    #                      'reasoning_summary': 'No separate hours_pen_rules mapping is '
    #                                           'generated in step 6.1 yet.',
    #                      'special_case_notes': ''},
    #  'weekend_rules': {'status': 'derived',
    #                    'source_ruleset_keys': ['overtime_consequence', 'penalties'],
    #                    'source_rule_ids': ['full-time-overtime-rates-general',
    #                                        'part-time-overtime-rates-general',
    #                                        'shiftworker-weekend-ordinary-hours-penalties'],
    #                    'clause_references': ['25.1(a)(i)(C)', '25.1(b)(i)', '23.1'],
    #                    'reasoning_summary': 'For day workers, the reviewed overtime tables '
    #                                         'state Saturday overtime at 200%, which is '
    #                                         'overtime treatment. | For day workers, Sunday '
    #                                         'work is paid at the overtime rate in the '
    #                                         'reviewed tables. | Shiftworkers with weekend '
    #                                         'ordinary hours receive weekend ordinary-hours '
    #                                         'penalty rates for Saturday work. | '
    #                                         'Shiftworkers with weekend ordinary hours '
    #                                         'receive weekend ordinary-hours penalty rates '
    #                                         'for Sunday work. | The reviewed rules do not '
    #                                         'provide a separate day-worker Saturday '
    #                                         'penalty loading; Saturday work for day '
    #                                         'workers is dealt with through overtime rates '
    #                                         'instead. | The reviewed rules do not provide '
    #                                         'a separate day-worker Sunday penalty loading; '
    #                                         'Sunday work for day workers is dealt with '
    #                                         'through overtime rates instead. | Shiftworker '
    #                                         'ordinary hours on Saturday are paid at 1.5x, '
    #                                         'which is a 0.5 loading above base. | '
    #                                         'Shiftworker ordinary hours on Sunday are paid '
    #                                         'at 1.75x, which is a 0.75 loading above base.',
    #                    'special_case_notes': 'Weekend penalty substitution rules exist for '
    #                                          'shiftworkers and casuals, but day-worker '
    #                                          'weekend ordinary hours are not given a '
    #                                          'separate penalty regime in the reviewed '
    #                                          'rules. | These rates substitute for shift '
    #                                          'premiums and are separate from overtime-rate '
    #                                          'selection. | Do not infer a penalty loading '
    #                                          'from overtime tables. | This is a total-rate '
    #                                          'substitution for ordinary hours, not an '
    #                                          'overtime loading.'},
    #  'two_tier_overtime': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_consequence'],
    #                        'source_rule_ids': ['full-time-overtime-rates-general',
    #                                            'part-time-overtime-rates-general',
    #                                            'casual-overtime-rates-general'],
    #                        'clause_references': ['25.1(a)(i)(A)',
    #                                              '25.1(a)(i)(B)',
    #                                              '25.1(b)(i)',
    #                                              '25.1(c)(i)'],
    #                        'reasoning_summary': 'The overtime tables show a first overtime '
    #                                             'tier and a higher subsequent tier for '
    #                                             'Monday to Friday overtime.',
    #                        'special_case_notes': 'Two-tier overtime applies on standard '
    #                                              'weekday overtime tables; weekend/public '
    #                                              'holiday rates are separate fixed rates.'},
    #  'two_tier_overtime_threshold': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_consequence'],
    #                                  'source_rule_ids': ['full-time-overtime-rates-general',
    #                                                      'part-time-overtime-rates-general',
    #                                                      'casual-overtime-rates-general'],
    #                                  'clause_references': ['25.1(a)(i)(A)',
    #                                                        '25.1(a)(i)(B)',
    #                                                        '25.1(b)(i)',
    #                                                        '25.1(c)(i)'],
    #                                  'reasoning_summary': 'The overtime tables show a '
    #                                                       'first overtime tier and a '
    #                                                       'higher subsequent tier for '
    #                                                       'Monday to Friday overtime. | '
    #                                                       'The reviewed overtime tables '
    #                                                       'state that the higher weekday '
    #                                                       'overtime rate applies after the '
    #                                                       'first two overtime hours.',
    #                                  'special_case_notes': 'Two-tier overtime applies on '
    #                                                        'standard weekday overtime '
    #                                                        'tables; weekend/public holiday '
    #                                                        'rates are separate fixed '
    #                                                        'rates. | The higher rate '
    #                                                        'starts only after hours '
    #                                                        'greater than 2, not at exactly '
    #                                                        '2 hours.'},
    #  'extended_overtime_days': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['full-time-overtime-rates-general',
    #                                                 'part-time-overtime-rates-general',
    #                                                 'casual-overtime-rates-general'],
    #                             'clause_references': ['25.1(a)(i)(A)',
    #                                                   '25.1(a)(i)(B)',
    #                                                   '25.1(b)(i)',
    #                                                   '25.1(c)(i)'],
    #                             'reasoning_summary': 'The overtime tables show a first '
    #                                                  'overtime tier and a higher '
    #                                                  'subsequent tier for Monday to Friday '
    #                                                  'overtime. | The two-tier overtime '
    #                                                  'structure applies on the weekday '
    #                                                  'tables covering Monday to Friday.',
    #                             'special_case_notes': 'Two-tier overtime applies on '
    #                                                   'standard weekday overtime tables; '
    #                                                   'weekend/public holiday rates are '
    #                                                   'separate fixed rates. | Weekend '
    #                                                   'days use separate fixed overtime '
    #                                                   'rates rather than the two-tier '
    #                                                   'weekday structure.'},
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

    # GENERATION_METADATA = {'schema_version': 'calculator-rules-python-v1', 'award_code': 'MA000018'}
