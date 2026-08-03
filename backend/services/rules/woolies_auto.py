"""Rule engine for award pay calculations."""

class Woolies2024Rules:
    """Business rules for award Woolies_2024 pay calculations."""

    ORDINARY_HOURS_LIMIT_DAILY = 9
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 9
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2
    SUNDAY_OVERTIME_RATE = 2
    SATURDAY_OVERTIME_RATE = 1.5
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_HOUR = 23
    GAP_PENALTY_HOURS = 12
    GAP_PENALTY_RATE = 1
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 3
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = False
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    PENALTIES = {'day_worker_evening_wednesday_to_friday': {'type': 'time_based',
                                                'basis': 'start',
                                                'start': 18,
                                                'end': 23,
                                                'rate': 0.25,
                                                'description': 'Wednesday-Friday '
                                                               'day-worker evening penalty '
                                                               'window for full-time and '
                                                               'part-time employees.',
                                                'applies_to': ['day']}}
    HOURS_PEN_RULES = {}
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': True}, 'Sunday': {'is_overtime': True}},
     'shift': {'Saturday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5},
               'Sunday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.75}}}
    DEFAULT_BREAK = 0.5

    # FIELD_EVIDENCE = {'ordinary_hours_limit_daily': {'status': 'derived',
    #                                 'source_ruleset_keys': ['overtime_creation'],
    #                                 'source_rule_ids': ['baking-production-daily-threshold'],
    #                                 'clause_references': ['11.4(a)', '11.4(c)'],
    #                                 'reasoning_summary': 'The reviewed shiftworker rule '
    #                                                      'provides a 9-hour daily overtime '
    #                                                      'threshold for covered baking '
    #                                                      'production shiftworkers.',
    #                                 'special_case_notes': 'This threshold is expressly '
    #                                                       'stated for baking production '
    #                                                       'shiftworkers. The source does '
    #                                                       'not establish a broader single '
    #                                                       'daily threshold for every '
    #                                                       'shiftworker category.'},
    #  'ordinary_hours_limit_weekly': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_creation'],
    #                                  'source_rule_ids': ['baking-production-weekly-threshold'],
    #                                  'clause_references': ['11.4(a)', '11.4(c)'],
    #                                  'reasoning_summary': 'Covered baking production '
    #                                                       'shiftworkers incur overtime '
    #                                                       'above 38 hours per week, in '
    #                                                       'addition to the daily 9-hour '
    #                                                       'test.',
    #                                  'special_case_notes': 'Paid shiftworker breaks count '
    #                                                        'as hours worked. The reviewed '
    #                                                        'source does not establish this '
    #                                                        'weekly threshold for every '
    #                                                        'possible shiftworker '
    #                                                        'category.'},
    #  'day_worker_ordinary_hours_daily': {'status': 'derived',
    #                                      'source_ruleset_keys': ['overtime_creation'],
    #                                      'source_rule_ids': ['full-time-daily-overtime-limit',
    #                                                          'part-time-daily-overtime-limit',
    #                                                          'casual-daily-overtime-limit'],
    #                                      'clause_references': ['8.2(b)',
    #                                                            '8.3(a)',
    #                                                            '8.6(a)',
    #                                                            '10.2(a)(iii)',
    #                                                            '10.3(a)(ii)',
    #                                                            '10.4(a)(ii)'],
    #                                      'reasoning_summary': 'The standard daily overtime '
    #                                                           'threshold for full-time, '
    #                                                           'part-time and casual day '
    #                                                           'workers is above 9 hours.',
    #                                      'special_case_notes': 'Up to 11 hours may be '
    #                                                            'ordinary on one permitted '
    #                                                            'day each week. Full-time '
    #                                                            'four-day arrangements use '
    #                                                            'a 9.5-hour threshold.'},
    #  'day_worker_ordinary_hours_weekly': {'status': 'derived',
    #                                       'source_ruleset_keys': ['overtime_creation'],
    #                                       'source_rule_ids': ['part-time-weekly-hours-limit',
    #                                                           'casual-weekly-or-roster-cycle-hours-limit',
    #                                                           'full-time-four-week-hours-limit'],
    #                                       'clause_references': ['8.2(a)',
    #                                                             '8.3(a)',
    #                                                             '8.6(a)',
    #                                                             '10.2(a)(i)',
    #                                                             '10.3(a)(iii)',
    #                                                             '10.4(a)(i)'],
    #                                       'reasoning_summary': 'The standard '
    #                                                            'ordinary-hours benchmark '
    #                                                            'is 38 hours per week, with '
    #                                                            'full-time hours also '
    #                                                            'tested against 152 hours '
    #                                                            'over four weeks.',
    #                                       'special_case_notes': 'Part-time employees also '
    #                                                             'have a 144-hour four-week '
    #                                                             'limit. Casual rostered '
    #                                                             'employees use an '
    #                                                             'equivalent 38-hour '
    #                                                             'average over the roster '
    #                                                             'cycle. Full-time longer '
    #                                                             'averaging periods and '
    #                                                             'roster-day limits may '
    #                                                             'also apply.'},
    #  'standard_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['overtime-mon-sat-full-part-time-first-three-hours',
    #                                                 'overtime-mon-sat-casual-first-three-hours'],
    #                             'clause_references': ['Clause 10.5(a)'],
    #                             'reasoning_summary': 'The first three daily overtime hours '
    #                                                  'Monday to Saturday are paid at 150% '
    #                                                  'for permanent employees; casuals '
    #                                                  'have a separate 175% inclusive rate.',
    #                             'special_case_notes': 'The live standard rate is the '
    #                                                   'full-time/part-time 150% rate. '
    #                                                   'Casual rates are 175% for the first '
    #                                                   'three hours and 225% thereafter, '
    #                                                   'inclusive of casual loading.'},
    #  'extended_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['overtime-mon-sat-full-part-time-first-three-hours',
    #                                                 'overtime-mon-sat-full-part-time-after-three-hours',
    #                                                 'overtime-mon-sat-casual-first-three-hours',
    #                                                 'overtime-mon-sat-casual-after-three-hours'],
    #                             'clause_references': ['Clause 10.5(a)'],
    #                             'reasoning_summary': 'Monday-to-Saturday overtime has a '
    #                                                  'first-three-hours tier and a higher '
    #                                                  'tier after three overtime hours on '
    #                                                  'the day. | The standard '
    #                                                  'full-time/part-time rate after the '
    #                                                  'first three daily overtime hours '
    #                                                  'Monday to Saturday is 200%.',
    #                             'special_case_notes': 'Casual employees have corresponding '
    #                                                   '1.75 and 2.25 total paid-rate '
    #                                                   'tiers. Sunday is a flat Sunday '
    #                                                   'overtime rate rather than this '
    #                                                   'two-tier structure. | For casuals, '
    #                                                   'the corresponding extended rate is '
    #                                                   '225% inclusive of casual loading.'},
    #  'sunday_overtime_rate': {'status': 'derived',
    #                           'source_ruleset_keys': ['overtime_consequence'],
    #                           'source_rule_ids': ['overtime-sunday-full-part-time',
    #                                               'overtime-sunday-casual'],
    #                           'clause_references': ['Clause 10.5(a)'],
    #                           'reasoning_summary': 'Sunday overtime for full-time and '
    #                                                'part-time employees is paid at 200% '
    #                                                'for all overtime hours.',
    #                           'special_case_notes': 'Casual Sunday overtime is 225% '
    #                                                 'inclusive of casual loading.'},
    #  'saturday_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['overtime-mon-sat-full-part-time-first-three-hours',
    #                                                 'overtime-mon-sat-full-part-time-after-three-hours'],
    #                             'clause_references': ['Clause 10.5(a)'],
    #                             'reasoning_summary': 'Saturday follows the '
    #                                                  'Monday-to-Saturday overtime '
    #                                                  'structure: 150% for the first three '
    #                                                  'daily overtime hours and 200% '
    #                                                  'thereafter.',
    #                             'special_case_notes': 'Because Saturday is an '
    #                                                   'extended-overtime day, the higher '
    #                                                   '200% tier controls after three '
    #                                                   'overtime hours. Separate Saturday '
    #                                                   'penalty rules may also apply where '
    #                                                   'the hours are ordinary rather than '
    #                                                   'overtime.'},
    #  'apply_span_overtime': {'status': 'derived',
    #                          'source_ruleset_keys': ['overtime_creation'],
    #                          'source_rule_ids': ['ordinary-hours-span-non-shiftworkers'],
    #                          'clause_references': ['6.1(a)', '6.1(b)(i)', '6.1(b)(ii)'],
    #                          'reasoning_summary': 'Non-shiftworker hours outside the '
    #                                               'applicable ordinary-hours span create '
    #                                               'overtime unless the clause 6.1(b) '
    #                                               'exception applies. | The reviewed rule '
    #                                               'specifies separate ordinary-hours spans '
    #                                               'for Monday-Saturday and Sunday.',
    #                          'special_case_notes': 'Monday-Saturday ordinary span is '
    #                                                '7:00am to 11:00pm; Sunday ordinary '
    #                                                'span is 9:00am to 11:00pm. An '
    #                                                'agreement and applicable clause 6.2 '
    #                                                'penalty can prevent overtime for '
    #                                                'qualifying hours. | Outside-span hours '
    #                                                'may remain ordinary only under the '
    #                                                'applicable agreement and clause 6.2 '
    #                                                'penalty conditions.'},
    #  'span_overtime_hour': {'status': 'derived',
    #                         'source_ruleset_keys': ['overtime_creation'],
    #                         'source_rule_ids': ['ordinary-hours-span-non-shiftworkers'],
    #                         'clause_references': ['6.1(a)', '6.1(b)(i)', '6.1(b)(ii)'],
    #                         'reasoning_summary': 'Non-shiftworker hours outside the '
    #                                              'applicable ordinary-hours span create '
    #                                              'overtime unless the clause 6.1(b) '
    #                                              'exception applies. | A single live '
    #                                              'cutoff is set at 11:00pm, the common end '
    #                                              'of the ordinary-hours span on all days. '
    #                                              '| The reviewed rule specifies separate '
    #                                              'ordinary-hours spans for Monday-Saturday '
    #                                              'and Sunday.',
    #                         'special_case_notes': 'Monday-Saturday ordinary span is 7:00am '
    #                                               'to 11:00pm; Sunday ordinary span is '
    #                                               '9:00am to 11:00pm. An agreement and '
    #                                               'applicable clause 6.2 penalty can '
    #                                               'prevent overtime for qualifying hours. '
    #                                               '| The start of the span differs by day: '
    #                                               '7:00am Monday-Saturday and 9:00am '
    #                                               'Sunday. The calculator field cannot '
    #                                               'represent both start boundaries, so the '
    #                                               'full span rule must retain day-specific '
    #                                               'handling. | Outside-span hours may '
    #                                               'remain ordinary only under the '
    #                                               'applicable agreement and clause 6.2 '
    #                                               'penalty conditions.'},
    #  'gap_penalty_hours': {'status': 'derived',
    #                        'source_ruleset_keys': ['penalties', 'overtime_creation'],
    #                        'source_rule_ids': ['break-gap-required-and-consequence',
    #                                            'roster-minimum-break-full-time',
    #                                            'roster-minimum-break-part-time',
    #                                            'roster-minimum-break-casual',
    #                                            'recall-rest-period-treatment',
    #                                            'recall-disregarded-for-rest-and-rostering'],
    #                        'clause_references': ['Clause 7.3(a)-(c)',
    #                                              'Clauses 10.2(b), 10.3(b), 10.4(b)',
    #                                              'Clause 8.2(b)-(c)',
    #                                              'Clause 8.3(a),(c)',
    #                                              'Clause 8.6(a)',
    #                                              'Clause 5.2',
    #                                              'Clauses 8.2, 8.3 and 8.6'],
    #                        'reasoning_summary': 'The award requires a minimum inter-day '
    #                                             'break between completion of work and '
    #                                             'commencement on the next day. | The '
    #                                             'standard inter-day and roster gap is 12 '
    #                                             'consecutive hours. | The live calculator '
    #                                             'uses the standard 12-hour threshold, '
    #                                             'while recording the agreed 10-hour '
    #                                             'exception and recall exclusion.',
    #                        'special_case_notes': 'The standard requirement is 12 '
    #                                              'consecutive hours. A reduced period may '
    #                                              'be agreed, but not below 10 hours. | '
    #                                              'Full-time, part-time and casual '
    #                                              'employees may have an agreed reduced gap '
    #                                              'of at least 10 hours. | A breach of the '
    #                                              'applicable threshold attracts double '
    #                                              'rate until 12 consecutive hours off '
    #                                              'duty.'},
    #  'gap_penalty_rate': {'status': 'derived',
    #                       'source_ruleset_keys': ['penalties',
    #                                               'overtime_consequence',
    #                                               'overtime_creation'],
    #                       'source_rule_ids': ['break-gap-required-and-consequence',
    #                                           'insufficient-rest-double-rate-and-release',
    #                                           'recall-rest-period-treatment',
    #                                           'recall-disregarded-for-rest-and-rostering'],
    #                       'clause_references': ['Clause 7.3(a)-(c)',
    #                                             'Clauses 10.2(b), 10.3(b), 10.4(b)',
    #                                             'Clause 5.2',
    #                                             'Clauses 8.2, 8.3 and 8.6'],
    #                       'reasoning_summary': 'The award requires a minimum inter-day '
    #                                            'break between completion of work and '
    #                                            'commencement on the next day. | A breach '
    #                                            'requires double the otherwise applicable '
    #                                            'rate, so the loading above base is 1.0. | '
    #                                            'The live calculator uses the standard '
    #                                            '12-hour threshold, while recording the '
    #                                            'agreed 10-hour exception and recall '
    #                                            'exclusion.',
    #                       'special_case_notes': 'The standard requirement is 12 '
    #                                             'consecutive hours. A reduced period may '
    #                                             'be agreed, but not below 10 hours. | The '
    #                                             'double-rate treatment continues until the '
    #                                             'employee is released for 12 consecutive '
    #                                             'hours. Ordinary-time pay is preserved '
    #                                             'only for ordinary hours occurring during '
    #                                             'that release. | A breach of the '
    #                                             'applicable threshold attracts double rate '
    #                                             'until 12 consecutive hours off duty.'},
    #  'penalties': {'status': 'derived',
    #                'source_ruleset_keys': ['penalties'],
    #                'source_rule_ids': ['shiftwork-rates',
    #                                    'day-worker-penalty-table',
    #                                    'baking-production-shift-rates',
    #                                    'public-holiday-work-rates',
    #                                    'casual-loading-and-penalty-stacking'],
    #                'clause_references': ['Clause 11.3',
    #                                      'Clauses 4.1(c), 6.1, 6.2',
    #                                      'Clause 11.4(a)-(c)',
    #                                      'Clauses 19.1(f), 19.2(a)-(b)',
    #                                      'Clause 4.1(c)'],
    #                'reasoning_summary': 'The standard shiftwork rule applies a 30% loading '
    #                                     'to qualifying weekday shiftwork regardless of the '
    #                                     'particular weekday timing. | The numeric '
    #                                     'Wednesday-Friday 6:00pm to 11:00pm day-worker '
    #                                     'penalty window is represented as a weekday '
    #                                     'time-based rule. | Only standard weekday cases '
    #                                     'with a clear numeric representation were included '
    #                                     'in the live lists.',
    #                'special_case_notes': 'Casual weekday loading is 55%, inclusive of '
    #                                      'casual loading. Baking production early and '
    #                                      'night shift rates are commencement-based '
    #                                      'alternatives and are not included in this '
    #                                      'standard live rule. | Casual loading-inclusive '
    #                                      'rate for this window is 50%. Monday/Tuesday '
    #                                      '7:00am-6:00pm is base rate for '
    #                                      'full-time/part-time employees. Night windows and '
    #                                      'their first-three-hours versus subsequent-hour '
    #                                      'rates are not encoded because one numeric rule '
    #                                      'cannot safely represent the cohort and tier '
    #                                      'variations. | Casual rates stated in the source '
    #                                      'generally include the 25% casual loading and '
    #                                      'must not be stacked again.'},
    #  'hours_pen_rules': {'status': 'defaulted',
    #                      'source_ruleset_keys': [],
    #                      'source_rule_ids': [],
    #                      'clause_references': [],
    #                      'reasoning_summary': 'No separate hours_pen_rules mapping is '
    #                                           'generated in step 6.1 yet.',
    #                      'special_case_notes': ''},
    #  'weekend_rules': {'status': 'derived',
    #                    'source_ruleset_keys': ['penalties'],
    #                    'source_rule_ids': ['day-worker-penalty-table', 'shiftwork-rates'],
    #                    'clause_references': ['Clauses 4.1(c), 6.1, 6.2', 'Clause 11.3'],
    #                    'reasoning_summary': 'The day-worker penalty table expressly '
    #                                         'provides Saturday penalty rates for Saturday '
    #                                         '7:00am-11:00pm. | The day-worker penalty '
    #                                         'table expressly provides Sunday penalty rates '
    #                                         'for the Sunday time bands. | Shiftwork on '
    #                                         'Saturday is paid under the Saturday shiftwork '
    #                                         'penalty rate. | Shiftwork on Sunday is paid '
    #                                         'under the Sunday shiftwork penalty rate. | '
    #                                         'The standard full-time/part-time Saturday '
    #                                         'day-worker rate is base plus 25%. | The '
    #                                         'standard full-time/part-time Sunday '
    #                                         '9:00am-11:00pm day-worker rate is base plus '
    #                                         '50%. | The standard full-time/part-time '
    #                                         'Saturday shiftwork loading is 50%. | The '
    #                                         'standard full-time/part-time Sunday shiftwork '
    #                                         'loading is 75%.',
    #                    'special_case_notes': 'Hours outside the ordinary span or otherwise '
    #                                          'exceeding overtime limits may instead be '
    #                                          'overtime; this field represents the ordinary '
    #                                          'Saturday treatment. | Sunday hours outside '
    #                                          'the 9:00am-11:00pm span may create overtime '
    #                                          'unless the clause 6.1(b) exception applies. '
    #                                          '| Full-time/part-time shiftworkers receive '
    #                                          'base plus 50%; casuals receive base plus '
    #                                          '75%, inclusive of casual loading. Baking '
    #                                          'production alternatives may apply instead. | '
    #                                          'Full-time/part-time shiftworkers receive '
    #                                          'base plus 75%; casuals receive base plus '
    #                                          '100%, inclusive of casual loading. Baking '
    #                                          'production alternatives may apply instead. | '
    #                                          'Casual Saturday rate is base plus 50%, '
    #                                          'inclusive of casual loading. The late-night '
    #                                          'Saturday bands have higher rates. | Sunday '
    #                                          'midnight-9:00am and 11:00pm-midnight use '
    #                                          'base plus 100% for full-time/part-time '
    #                                          'employees. Casual rates are higher and '
    #                                          'include loading. | Casual Saturday shiftwork '
    #                                          'loading is 75%, inclusive of casual loading. '
    #                                          'Baking production shift rates may supersede '
    #                                          'this rule. | Casual Sunday shiftwork loading '
    #                                          'is 100%, inclusive of casual loading. Baking '
    #                                          'production shift rates may supersede this '
    #                                          'rule.'},
    #  'two_tier_overtime': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_consequence'],
    #                        'source_rule_ids': ['overtime-mon-sat-full-part-time-first-three-hours',
    #                                            'overtime-mon-sat-full-part-time-after-three-hours',
    #                                            'overtime-mon-sat-casual-first-three-hours',
    #                                            'overtime-mon-sat-casual-after-three-hours'],
    #                        'clause_references': ['Clause 10.5(a)'],
    #                        'reasoning_summary': 'Monday-to-Saturday overtime has a '
    #                                             'first-three-hours tier and a higher tier '
    #                                             'after three overtime hours on the day.',
    #                        'special_case_notes': 'Casual employees have corresponding 1.75 '
    #                                              'and 2.25 total paid-rate tiers. Sunday '
    #                                              'is a flat Sunday overtime rate rather '
    #                                              'than this two-tier structure.'},
    #  'two_tier_overtime_threshold': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_consequence'],
    #                                  'source_rule_ids': ['overtime-mon-sat-full-part-time-first-three-hours',
    #                                                      'overtime-mon-sat-full-part-time-after-three-hours',
    #                                                      'overtime-mon-sat-casual-first-three-hours',
    #                                                      'overtime-mon-sat-casual-after-three-hours'],
    #                                  'clause_references': ['Clause 10.5(a)'],
    #                                  'reasoning_summary': 'Monday-to-Saturday overtime has '
    #                                                       'a first-three-hours tier and a '
    #                                                       'higher tier after three '
    #                                                       'overtime hours on the day. | '
    #                                                       'The higher tier begins only for '
    #                                                       'overtime hours after the first '
    #                                                       '3 overtime hours worked on that '
    #                                                       'day.',
    #                                  'special_case_notes': 'Casual employees have '
    #                                                        'corresponding 1.75 and 2.25 '
    #                                                        'total paid-rate tiers. Sunday '
    #                                                        'is a flat Sunday overtime rate '
    #                                                        'rather than this two-tier '
    #                                                        'structure. | The higher rate '
    #                                                        'applies when daily overtime '
    #                                                        'exceeds 3 hours; it does not '
    #                                                        'replace the first three '
    #                                                        'hours.'},
    #  'extended_overtime_days': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['overtime-mon-sat-full-part-time-first-three-hours',
    #                                                 'overtime-mon-sat-full-part-time-after-three-hours',
    #                                                 'overtime-mon-sat-casual-first-three-hours',
    #                                                 'overtime-mon-sat-casual-after-three-hours'],
    #                             'clause_references': ['Clause 10.5(a)'],
    #                             'reasoning_summary': 'Monday-to-Saturday overtime has a '
    #                                                  'first-three-hours tier and a higher '
    #                                                  'tier after three overtime hours on '
    #                                                  'the day. | The two-tier '
    #                                                  'Monday-to-Saturday rule applies on '
    #                                                  'each named day from Monday through '
    #                                                  'Saturday.',
    #                             'special_case_notes': 'Casual employees have corresponding '
    #                                                   '1.75 and 2.25 total paid-rate '
    #                                                   'tiers. Sunday is a flat Sunday '
    #                                                   'overtime rate rather than this '
    #                                                   'two-tier structure. | Sunday '
    #                                                   'overtime is paid at a flat 200% for '
    #                                                   'full-time/part-time employees or '
    #                                                   '225% for casuals, so Sunday is not '
    #                                                   'included in the two-tier list.'},
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

    # GENERATION_METADATA = {'schema_version': 'calculator-rules-python-v1', 'award_code': 'Woolies_2024'}
