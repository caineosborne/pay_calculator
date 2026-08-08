"""Rule engine for award pay calculations."""


class ClerksPrivateSectorRules:
    """Business rules for award MA000002 pay calculations."""

    ORDINARY_HOURS_LIMIT_DAILY = 10
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 10
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2
    SUNDAY_OVERTIME_RATE = 2
    SATURDAY_OVERTIME_RATE = 2
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 1
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_HOUR = 19
    GAP_PENALTY_HOURS = 10
    GAP_PENALTY_RATE = 1
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 2
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    PENALTIES = {'shiftwork_afternoon_or_night_shift': {'type': 'shift_based',
                                            'basis': 'end',
                                            'start': 19,
                                            'end': 24,
                                            'rate': 0.15,
                                            'description': 'Shiftwork penalty for ordinary '
                                                           'hours worked on an afternoon '
                                                           'or night shift.',
                                            'applies_to': ['shift']}}
    HOURS_PEN_RULES = {}
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': True, 'rate': 1.25},
             'Sunday': {'is_overtime': True, 'rate': 2}},
     'shift': {'Saturday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5},
               'Sunday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5}}}
    DEFAULT_BREAK = 0.5

    # FIELD_EVIDENCE = {'ordinary_hours_limit_daily': {'status': 'derived',
    #                                 'source_ruleset_keys': ['overtime_creation'],
    #                                 'source_rule_ids': ['shiftwork-daily-ordinary-hours-boundary',
    #                                                     'general-daily-ordinary-hours-boundary'],
    #                                 'clause_references': ['26.2',
    #                                                       '28.1',
    #                                                       '13.7',
    #                                                       '21.1(b)'],
    #                                 'reasoning_summary': 'Used the shiftworker-specific '
    #                                                      'daily ordinary-hours cap of 10 '
    #                                                      'hours.',
    #                                 'special_case_notes': 'Paid breaks count toward the '
    #                                                       '10-hour limit for '
    #                                                       'shiftworkers.'},
    #  'ordinary_hours_limit_weekly': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_creation'],
    #                                  'source_rule_ids': ['shiftwork-weekly-ordinary-hours-boundary'],
    #                                  'clause_references': ['25.1', '26.1', '28.1'],
    #                                  'reasoning_summary': 'Used the shiftworker-specific '
    #                                                       'weekly ordinary-hours average '
    #                                                       'of 38 hours.',
    #                                  'special_case_notes': 'The weekly limit may be '
    #                                                        'averaged over up to 4 weeks or '
    #                                                        'over an agreed roster period '
    #                                                        'of up to 12 months if agreed '
    #                                                        'with the majority of employees '
    #                                                        'concerned.'},
    #  'day_worker_ordinary_hours_daily': {'status': 'derived',
    #                                      'source_ruleset_keys': ['overtime_creation'],
    #                                      'source_rule_ids': ['general-daily-ordinary-hours-boundary',
    #                                                          'general-spread-of-hours-boundary',
    #                                                          'general-directed-hours-overtime'],
    #                                      'clause_references': ['13.7',
    #                                                            '21.1(b)',
    #                                                            '26.2',
    #                                                            '13.3',
    #                                                            '13.4',
    #                                                            '13.5',
    #                                                            '21.1(c)'],
    #                                      'reasoning_summary': 'Derived the standard daily '
    #                                                           'ordinary-hours cap for '
    #                                                           'non-shiftworkers/day '
    #                                                           'workers from the 10-hour '
    #                                                           'daily boundary, with the '
    #                                                           'spread-of-hours rule as the '
    #                                                           'day-worker context.',
    #                                      'special_case_notes': 'For non-shiftwork, unpaid '
    #                                                            'meal breaks are excluded '
    #                                                            'from the 10-hour count. '
    #                                                            'Separate spread-of-hours '
    #                                                            'overtime can also trigger '
    #                                                            'outside 7am-7pm Mon-Fri '
    #                                                            'and 7am-12:30pm Sat unless '
    #                                                            'varied.'},
    #  'day_worker_ordinary_hours_weekly': {'status': 'derived',
    #                                       'source_ruleset_keys': ['overtime_creation'],
    #                                       'source_rule_ids': ['general-weekly-ordinary-hours-boundary',
    #                                                           'full-time-weekly-ordinary-hours-boundary'],
    #                                       'clause_references': ['13.2',
    #                                                             '21.1(a)',
    #                                                             '9.1(a)',
    #                                                             '9.1(b)',
    #                                                             '26.1'],
    #                                       'reasoning_summary': 'Set the standard '
    #                                                            'non-shiftworker weekly '
    #                                                            'ordinary-hours limit at 38 '
    #                                                            'hours per week.',
    #                                       'special_case_notes': 'May be averaged over up '
    #                                                             'to 4 weeks or an agreed '
    #                                                             'roster period. Full-time '
    #                                                             'employees may also be '
    #                                                             'subject to a lesser '
    #                                                             'workplace full-time '
    #                                                             'ordinary-hours number.'},
    #  'standard_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                                 'shiftwork-overtime-rate-full-time-part-time',
    #                                                 'nonshift-overtime-rate-casual',
    #                                                 'shiftwork-overtime-rate-casual'],
    #                             'clause_references': ['clause 21.4(a)',
    #                                                   'clause 28.1',
    #                                                   'Table 6—Overtime rates for '
    #                                                   'shiftwork'],
    #                             'reasoning_summary': 'The standard first-tier overtime '
    #                                                  'rate in the reviewed rules is 150% '
    #                                                  'for both day-worker and shiftworker '
    #                                                  'overtime categories.',
    #                             'special_case_notes': 'Casual rates already include casual '
    #                                                   'loading; this field records the '
    #                                                   'first overtime tier above base, not '
    #                                                   'the total all-in percentage.'},
    #  'extended_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                                 'nonshift-overtime-rate-casual',
    #                                                 'shiftwork-overtime-rate-full-time-part-time',
    #                                                 'shiftwork-overtime-rate-casual',
    #                                                 'meal-break-overtime-consequence',
    #                                                 'no-10-hour-break-200-percent-release',
    #                                                 'no-8-hour-break-200-percent-release'],
    #                             'clause_references': ['clause 21.4(a)',
    #                                                   'clause 28.1',
    #                                                   'Table 6—Overtime rates for '
    #                                                   'shiftwork',
    #                                                   'clause 15.4',
    #                                                   'clause 22.4(a)',
    #                                                   'clause 30.5(a)'],
    #                             'reasoning_summary': 'The reviewed overtime tables show a '
    #                                                  'first overtime tier and a higher '
    #                                                  'second tier after a threshold. | The '
    #                                                  'higher overtime tier is 200% in the '
    #                                                  'reviewed rules.',
    #                             'special_case_notes': 'Two-tier overtime applies in '
    #                                                   'different ways for day-workers and '
    #                                                   'shiftworkers, with separate daily '
    #                                                   'and weekly triggers. | Some '
    #                                                   'separate breach/rest-break '
    #                                                   'provisions also pay 200%, but this '
    #                                                   'field is the standard higher '
    #                                                   'overtime tier.'},
    #  'sunday_overtime_rate': {'status': 'derived',
    #                           'source_ruleset_keys': ['overtime_consequence'],
    #                           'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                               'nonshift-overtime-rate-casual',
    #                                               'nonshift-overtime-minimum-4-hours-sunday',
    #                                               'shiftwork-overtime-rate-full-time-part-time',
    #                                               'shiftwork-overtime-rate-casual'],
    #                           'clause_references': ['clause 21.4(a)',
    #                                                 'clause 21.4(c)',
    #                                                 'clause 28.1',
    #                                                 'Table 6—Overtime rates for shiftwork'],
    #                           'reasoning_summary': 'Sunday overtime is paid at 200% in the '
    #                                                'reviewed overtime rules.',
    #                           'special_case_notes': 'The Sunday day-worker rule has a '
    #                                                 'minimum 4-hour engagement and '
    #                                                 'includes ordinary hours worked that '
    #                                                 'day.'},
    #  'saturday_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                                 'nonshift-overtime-rate-casual',
    #                                                 'shiftwork-overtime-rate-full-time-part-time',
    #                                                 'shiftwork-overtime-rate-casual'],
    #                             'clause_references': ['clause 21.4(a)',
    #                                                   'clause 28.1',
    #                                                   'Table 6—Overtime rates for '
    #                                                   'shiftwork'],
    #                             'reasoning_summary': 'Saturday overtime is paid at the '
    #                                                  'second-tier overtime rate in the '
    #                                                  'reviewed tables.',
    #                             'special_case_notes': 'For day-workers the rule is 200% '
    #                                                   'for Saturday overtime under the '
    #                                                   'overtime table; separate Saturday '
    #                                                   'ordinary-hour penalty rules exist '
    #                                                   'but are not used here.'},
    #  'saturday_penalty_rate': {'status': 'derived',
    #                            'source_ruleset_keys': ['penalties'],
    #                            'source_rule_ids': ['ordinary-hours-saturday-24-2',
    #                                                'shiftwork-penalty-rates-31-1-saturday-sunday-public-holiday'],
    #                            'clause_references': ['clause 24.2',
    #                                                  'clause 24.1',
    #                                                  'clause 31.1',
    #                                                  'Table 7—Penalty rates for shiftwork'],
    #                            'reasoning_summary': 'Non-shiftworker ordinary hours on '
    #                                                 'Saturday attract 125% total pay, i.e. '
    #                                                 '25% above base. | Shiftworker '
    #                                                 'ordinary hours on Saturday are paid '
    #                                                 'at 150%, i.e. 50% above base.',
    #                            'special_case_notes': 'This is the loading above base for '
    #                                                  'ordinary Saturday hours only; '
    #                                                  'overtime Saturday rates are '
    #                                                  'separate. | Do not cumulate with '
    #                                                  'overtime rates.'},
    #  'sunday_penalty_rate': {'status': 'derived',
    #                          'source_ruleset_keys': ['penalties'],
    #                          'source_rule_ids': ['ordinary-hours-sunday-24-3',
    #                                              'shiftwork-penalty-rates-31-1-saturday-sunday-public-holiday'],
    #                          'clause_references': ['clause 24.3(a)',
    #                                                'clause 24.3(b)',
    #                                                'clause 24.3(c)',
    #                                                'clause 13.5(b)',
    #                                                'clause 31.1',
    #                                                'Table 7—Penalty rates for shiftwork'],
    #                          'reasoning_summary': 'Non-shiftworker ordinary hours on '
    #                                               'Sunday are paid at 200%, i.e. 100% '
    #                                               'above base. | Shiftworker ordinary '
    #                                               'hours on Sunday are paid at 150%, i.e. '
    #                                               '50% above base.',
    #                          'special_case_notes': "Minimum 4 hours' pay applies. This is "
    #                                                'only for ordinary Sunday hours for '
    #                                                'non-shiftworkers. | Do not cumulate '
    #                                                'with overtime rates. Public holiday '
    #                                                'routing is separate.'},
    #  'apply_span_overtime': {'status': 'derived',
    #                          'source_ruleset_keys': ['overtime_creation'],
    #                          'source_rule_ids': ['general-spread-of-hours-boundary',
    #                                              'general-directed-hours-overtime'],
    #                          'clause_references': ['13.3', '13.4', '13.5', '21.1(c)'],
    #                          'reasoning_summary': 'Day workers have a spread-of-hours rule '
    #                                               'that makes work outside the applicable '
    #                                               'span overtime. | Summarised the default '
    #                                               'day-worker spread of hours and the '
    #                                               'overtime consequence for work outside '
    #                                               'it.',
    #                          'special_case_notes': 'The standard span is not a single '
    #                                                'unconditional live cutoff because the '
    #                                                'spread varies by agreement or another '
    #                                                'award; the calculator uses the '
    #                                                'ordinary default span as a first-pass '
    #                                                'rule. | Includes the '
    #                                                'agreement/other-award variation caveat '
    #                                                'and the Saturday shorter spread.'},
    #  'span_overtime_hour': {'status': 'derived',
    #                         'source_ruleset_keys': ['overtime_creation'],
    #                         'source_rule_ids': ['general-spread-of-hours-boundary',
    #                                             'general-directed-hours-overtime'],
    #                         'clause_references': ['13.3', '13.4', '13.5', '21.1(c)'],
    #                         'reasoning_summary': 'Day workers have a spread-of-hours rule '
    #                                              'that makes work outside the applicable '
    #                                              'span overtime. | Selected the standard '
    #                                              'weekday upper cutoff for the default '
    #                                              'day-worker span. | Summarised the '
    #                                              'default day-worker spread of hours and '
    #                                              'the overtime consequence for work '
    #                                              'outside it.',
    #                         'special_case_notes': 'The standard span is not a single '
    #                                               'unconditional live cutoff because the '
    #                                               'spread varies by agreement or another '
    #                                               'award; the calculator uses the ordinary '
    #                                               'default span as a first-pass rule. | '
    #                                               'This is the best single live cutoff for '
    #                                               'first-pass calculation. The award also '
    #                                               'has a Saturday cutoff of 12:30pm and '
    #                                               'allows ±1 hour variation by agreement '
    #                                               'or another award. | Includes the '
    #                                               'agreement/other-award variation caveat '
    #                                               'and the Saturday shorter spread.'},
    #  'gap_penalty_hours': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_consequence',
    #                                                'overtime_creation',
    #                                                'penalties'],
    #                        'source_rule_ids': ['no-10-hour-break-200-percent-release',
    #                                            'no-8-hour-break-200-percent-release',
    #                                            'ten-hour-rest-gap-22-2',
    #                                            'eight-hour-rest-gap-30-3',
    #                                            'ten-hour-rest-release-22-3',
    #                                            'ten-hour-rest-breach-22-4',
    #                                            'eight-hour-rest-release-30-4',
    #                                            'eight-hour-rest-breach-30-5'],
    #                        'clause_references': ['clause 22.2',
    #                                              'clause 22.3',
    #                                              'clause 22.4',
    #                                              'clause 30.3',
    #                                              'clause 30.4',
    #                                              'clause 30.5'],
    #                        'reasoning_summary': 'The award contains minimum rest-gap rules '
    #                                             'between shifts for both non-shiftworkers '
    #                                             'and shiftworkers. | Used the standard '
    #                                             'non-shiftworker rest break threshold of '
    #                                             '10 consecutive hours as the live '
    #                                             'calculator threshold. | Recorded the '
    #                                             'worker-group-specific exception to the '
    #                                             'standard 10-hour rest gap.',
    #                        'special_case_notes': 'There are separate 10-hour and 8-hour '
    #                                              'rest rules depending on worker group. | '
    #                                              'Shiftworkers have a separate 8-hour '
    #                                              'threshold; the calculator should use 10 '
    #                                              'hours as the standard live threshold and '
    #                                              'record the shiftworker exception '
    #                                              'separately. | The award also has a '
    #                                              'non-shiftworker 10-hour rule; the live '
    #                                              'calculator uses 10 hours as the main '
    #                                              'threshold and keeps the shiftworker '
    #                                              '8-hour exception here.'},
    #  'gap_penalty_rate': {'status': 'derived',
    #                       'source_ruleset_keys': ['overtime_consequence',
    #                                               'overtime_creation',
    #                                               'penalties'],
    #                       'source_rule_ids': ['no-10-hour-break-200-percent-release',
    #                                           'no-8-hour-break-200-percent-release',
    #                                           'ten-hour-rest-gap-22-2',
    #                                           'eight-hour-rest-gap-30-3',
    #                                           'ten-hour-rest-breach-22-4',
    #                                           'eight-hour-rest-breach-30-5',
    #                                           'eight-hour-rest-release-30-4'],
    #                       'clause_references': ['clause 22.2',
    #                                             'clause 22.3',
    #                                             'clause 22.4',
    #                                             'clause 30.3',
    #                                             'clause 30.4',
    #                                             'clause 30.5',
    #                                             'clause 22.4(a)',
    #                                             'clause 30.5(a)'],
    #                       'reasoning_summary': 'The award contains minimum rest-gap rules '
    #                                            'between shifts for both non-shiftworkers '
    #                                            'and shiftworkers. | The breach provisions '
    #                                            'pay 200% total, which is 1.0 above base. | '
    #                                            'Recorded the worker-group-specific '
    #                                            'exception to the standard 10-hour rest '
    #                                            'gap.',
    #                       'special_case_notes': 'There are separate 10-hour and 8-hour '
    #                                             'rest rules depending on worker group. | '
    #                                             'Use the loading above base, not the total '
    #                                             'paid rate. | The award also has a '
    #                                             'non-shiftworker 10-hour rule; the live '
    #                                             'calculator uses 10 hours as the main '
    #                                             'threshold and keeps the shiftworker '
    #                                             '8-hour exception here.'},
    #  'penalties': {'status': 'derived',
    #                'source_ruleset_keys': ['penalties', 'overtime_consequence'],
    #                'source_rule_ids': ['shiftwork-penalty-rates-31-1-afternoon-night',
    #                                    'shiftwork-penalty-rates-31-1-permanent-night',
    #                                    'ordinary-hours-saturday-24-2',
    #                                    'ordinary-hours-sunday-24-3',
    #                                    'public-holiday-24-4',
    #                                    'meal-break-workthrough-15-4',
    #                                    'ten-hour-rest-breach-22-4',
    #                                    'eight-hour-rest-breach-30-5'],
    #                'clause_references': ['clause 31.1',
    #                                      'Table 7—Penalty rates for shiftwork',
    #                                      'clause 24.2',
    #                                      'clause 24.3',
    #                                      'clause 24.4',
    #                                      'clause 15.4',
    #                                      'clause 22.4',
    #                                      'clause 30.5'],
    #                'reasoning_summary': 'Included the standard shiftwork weekday penalties '
    #                                     'that apply to ordinary hours on afternoon/night '
    #                                     'and permanent night shifts. | No other standard '
    #                                     'weekday extra penalties with a clean numeric time '
    #                                     'window were supported by the reviewed rules. | '
    #                                     'Captured the main excluded penalty families and '
    #                                     'noted their treatment outside the weekday penalty '
    #                                     'list.',
    #                'special_case_notes': 'These are shift-classification-based penalties, '
    #                                      'not time-of-day windows. The broad 0-24 window '
    #                                      'is used only because the rule is triggered by '
    #                                      'shift classification rather than a specific time '
    #                                      'window. | Saturday, Sunday, public holiday, '
    #                                      'meal-break, and rest-gap rules are excluded from '
    #                                      'weekday penalties by instruction. '
    #                                      'Permanent-night variants were included only '
    #                                      'where explicitly provided as the standard '
    #                                      'shiftwork classification penalty. | Shiftwork '
    #                                      'penalties are not cumulative on overtime rates.'},
    #  'hours_pen_rules': {'status': 'defaulted',
    #                      'source_ruleset_keys': [],
    #                      'source_rule_ids': [],
    #                      'clause_references': [],
    #                      'reasoning_summary': 'No separate hours_pen_rules mapping is '
    #                                           'generated in step 6.1 yet.',
    #                      'special_case_notes': ''},
    #  'weekend_rules': {'status': 'derived',
    #                    'source_ruleset_keys': ['overtime_consequence', 'penalties'],
    #                    'source_rule_ids': ['ordinary-hours-saturday-24-2',
    #                                        'nonshift-overtime-rate-part-time',
    #                                        'nonshift-overtime-rate-casual',
    #                                        'nonshift-overtime-minimum-3-hours-saturday',
    #                                        'ordinary-hours-sunday-24-3',
    #                                        'nonshift-overtime-minimum-4-hours-sunday',
    #                                        'shiftwork-overtime-rate-full-time-part-time',
    #                                        'shiftwork-overtime-rate-casual',
    #                                        'shiftwork-penalty-rates-31-1-saturday-sunday-public-holiday',
    #                                        'shiftwork-not-cumulative-on-overtime-28-2',
    #                                        'public-holiday-shiftwork-routing-37-2',
    #                                        'shiftwork-commencement-exception-31-2'],
    #                    'clause_references': ['clause 24.2',
    #                                          'clause 24.1',
    #                                          'clause 21.4(a)',
    #                                          'clause 21.4(b)',
    #                                          'clause 24.3(a)',
    #                                          'clause 24.3(b)',
    #                                          'clause 24.3(c)',
    #                                          'clause 13.5(b)',
    #                                          'clause 21.4(c)',
    #                                          'clause 28.1',
    #                                          'Table 6—Overtime rates for shiftwork',
    #                                          'clause 31.1',
    #                                          'Table 7—Penalty rates for shiftwork',
    #                                          'clause 28.2',
    #                                          'clause 37.2',
    #                                          'clause 31.2(a)',
    #                                          'clause 31.2(b)'],
    #                    'reasoning_summary': 'For day workers, Saturday ordinary hours '
    #                                         'attract a penalty rate; Saturday overtime '
    #                                         'also has a distinct overtime minimum/rate. | '
    #                                         'For day workers, Sunday ordinary hours are '
    #                                         'paid as a penalty rate rather than ordinary '
    #                                         'time. | For shiftworkers, Saturday is handled '
    #                                         'under the overtime/routing framework rather '
    #                                         'than the non-shiftworker penalty table. | For '
    #                                         'shiftworkers, Sunday is routed through the '
    #                                         'shiftwork overtime/penalty machinery rather '
    #                                         'than the day-worker penalty table. | '
    #                                         'Non-shiftworker ordinary hours on Saturday '
    #                                         'attract 125% total pay, i.e. 25% above base. '
    #                                         '| Non-shiftworker ordinary hours on Sunday '
    #                                         'are paid at 200%, i.e. 100% above base. | '
    #                                         'Shiftworker ordinary hours on Saturday are '
    #                                         'paid at 150%, i.e. 50% above base. | '
    #                                         'Shiftworker ordinary hours on Sunday are paid '
    #                                         'at 150%, i.e. 50% above base.',
    #                    'special_case_notes': 'Implemented as a penalty for ordinary hours. '
    #                                          'Overtime on Saturday is separate and may '
    #                                          'require the 3-hour minimum in some cases. | '
    #                                          'The Sunday rule requires the employee to be '
    #                                          'directed under clause 13.5(b) and carries a '
    #                                          '4-hour minimum. | Shiftwork penalties are '
    #                                          'not cumulative on top of overtime rates. '
    #                                          'Saturday ordinary hours may be paid at 150% '
    #                                          'as a shiftwork penalty, but the live '
    #                                          'calculator should treat weekend shiftwork '
    #                                          'via overtime routing. | Sunday/public '
    #                                          'holiday timing exceptions around '
    #                                          '11pm-midnight shifts exist, and shift '
    #                                          'penalties do not stack on overtime. | This '
    #                                          'is the loading above base for ordinary '
    #                                          'Saturday hours only; overtime Saturday rates '
    #                                          "are separate. | Minimum 4 hours' pay "
    #                                          'applies. This is only for ordinary Sunday '
    #                                          'hours for non-shiftworkers. | Do not '
    #                                          'cumulate with overtime rates. | Do not '
    #                                          'cumulate with overtime rates. Public holiday '
    #                                          'routing is separate.'},
    #  'two_tier_overtime': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_consequence'],
    #                        'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                            'nonshift-overtime-rate-casual',
    #                                            'shiftwork-overtime-rate-full-time-part-time',
    #                                            'shiftwork-overtime-rate-casual'],
    #                        'clause_references': ['clause 21.4(a)',
    #                                              'clause 28.1',
    #                                              'Table 6—Overtime rates for shiftwork'],
    #                        'reasoning_summary': 'The reviewed overtime tables show a first '
    #                                             'overtime tier and a higher second tier '
    #                                             'after a threshold.',
    #                        'special_case_notes': 'Two-tier overtime applies in different '
    #                                              'ways for day-workers and shiftworkers, '
    #                                              'with separate daily and weekly '
    #                                              'triggers.'},
    #  'two_tier_overtime_threshold': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_consequence'],
    #                                  'source_rule_ids': ['nonshift-overtime-rate-part-time',
    #                                                      'nonshift-overtime-rate-casual',
    #                                                      'shiftwork-overtime-rate-full-time-part-time',
    #                                                      'shiftwork-overtime-rate-casual'],
    #                                  'clause_references': ['clause 21.4(a)',
    #                                                        'clause 28.1',
    #                                                        'Table 6—Overtime rates for '
    #                                                        'shiftwork'],
    #                                  'reasoning_summary': 'The reviewed overtime tables '
    #                                                       'show a first overtime tier and '
    #                                                       'a higher second tier after a '
    #                                                       'threshold. | For day-worker '
    #                                                       'overtime and the ordinary-shift '
    #                                                       'overtime tier, the higher rate '
    #                                                       'starts after the first 2 '
    #                                                       'overtime hours in a day.',
    #                                  'special_case_notes': 'Two-tier overtime applies in '
    #                                                        'different ways for day-workers '
    #                                                        'and shiftworkers, with '
    #                                                        'separate daily and weekly '
    #                                                        'triggers. | Shiftworkers also '
    #                                                        'have a weekly overtime tier '
    #                                                        'that changes after 3 hours; '
    #                                                        'the calculator should keep the '
    #                                                        'standard live trigger at 2 '
    #                                                        'hours for the main daily '
    #                                                        'overtime tier.'},
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

    # GENERATION_METADATA = {'schema_version': 'calculator-rules-python-v1',
    #  'award_code': 'MA000002',
    #  'award_title': 'This is the Clerks—Private Sector Award 2020.'}
