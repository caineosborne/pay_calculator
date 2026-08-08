"""Rule engine for award pay calculations."""


class MA000120Rules:
    """Business rules for award MA000120 pay calculations."""

    ORDINARY_HOURS_LIMIT_DAILY = 8
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2
    SUNDAY_OVERTIME_RATE = 1
    SATURDAY_OVERTIME_RATE = 1.5
    SATURDAY_PENALTY_RATE = 0.5
    SUNDAY_PENALTY_RATE = 1
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_HOUR = 18.5
    GAP_PENALTY_HOURS = 10
    GAP_PENALTY_RATE = 1
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 2
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    PENALTIES = {'shiftworker_afternoon_shift_loading': {'type': 'shift_based',
                                             'basis': 'end',
                                             'start': 18.5,
                                             'end': 24.0,
                                             'rate': 0.15,
                                             'description': 'Shiftworkers receive a 15% '
                                                            'loading for afternoon shifts '
                                                            'finishing after 6:30 pm and '
                                                            'at or before midnight.',
                                             'applies_to': ['shift']},
}
    HOURS_PEN_RULES = {}
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': True}, 'Sunday': {'is_overtime': True}},
     'shift': {'Saturday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5},
               'Sunday': {'is_overtime': True}}}
    DEFAULT_BREAK = 0.5

    # FIELD_EVIDENCE = {'ordinary_hours_limit_daily': {'status': 'not_found',
    #                                 'source_ruleset_keys': ['overtime_creation'],
    #                                 'source_rule_ids': ['shiftworkers-average-38-hours-per-week-over-cycle'],
    #                                 'clause_references': ['23.4(a)', '23.4(b)'],
    #                                 'reasoning_summary': 'The reviewed rules provide a '
    #                                                      'weekly average ordinary-hours '
    #                                                      'cap for shiftworkers, but no '
    #                                                      'separate standard daily limit.',
    #                                 'special_case_notes': 'Shiftworkers are governed by an '
    #                                                       'average 38-hour week over a '
    #                                                       'cycle, not a clearly stated '
    #                                                       'daily ordinary-hours limit in '
    #                                                       'the reviewed rules.'},
    #  'ordinary_hours_limit_weekly': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_creation'],
    #                                  'source_rule_ids': ['shiftworkers-average-38-hours-per-week-over-cycle'],
    #                                  'clause_references': ['23.4(a)', '23.4(b)'],
    #                                  'reasoning_summary': "Shiftworkers' ordinary hours, "
    #                                                       'inclusive of meal breaks, must '
    #                                                       'not exceed an average of 38 '
    #                                                       'hours per week over the roster '
    #                                                       'cycle.',
    #                                  'special_case_notes': 'The cap is an average over a '
    #                                                        'one-, two- or four-week cycle, '
    #                                                        'not a fixed single-week '
    #                                                        'maximum.'},
    #  'day_worker_ordinary_hours_daily': {'status': 'derived',
    #                                      'source_ruleset_keys': ['overtime_creation'],
    #                                      'source_rule_ids': ['general-ordinary-hours-daily-boundary-8-hours-with-10-hour-agreement'],
    #                                      'clause_references': ['21.2', '7', '23.4(a)'],
    #                                      'reasoning_summary': 'For non-shiftworkers, '
    #                                                           'ordinary hours are limited '
    #                                                           'to 8 hours per day, with a '
    #                                                           'possible agreement-based '
    #                                                           'extension to 10 hours. The '
    #                                                           'standard live calculator '
    #                                                           'value is 8 hours.',
    #                                      'special_case_notes': 'A valid clause 7 agreement '
    #                                                            'can extend the daily limit '
    #                                                            'to 10 hours for '
    #                                                            'non-shiftworkers; this is '
    #                                                            'a special case and not the '
    #                                                            'standard default.'},
    #  'day_worker_ordinary_hours_weekly': {'status': 'derived',
    #                                       'source_ruleset_keys': ['overtime_creation'],
    #                                       'source_rule_ids': ['full-time-ordinary-hours-average-38-per-week'],
    #                                       'clause_references': ['10.3',
    #                                                             '21.1',
    #                                                             '21.4',
    #                                                             '23.1(a)'],
    #                                       'reasoning_summary': 'For full-time employees, '
    #                                                            'ordinary hours average 38 '
    #                                                            'hours per week over a one, '
    #                                                            'two or four week cycle. '
    #                                                            'This is the standard '
    #                                                            'weekly ordinary-hours '
    #                                                            'limit used by the '
    #                                                            'calculator.',
    #                                       'special_case_notes': 'The source frames this as '
    #                                                             'an average over a one-, '
    #                                                             'two- or four-week cycle '
    #                                                             'rather than a single '
    #                                                             'fixed-week roster cap.'},
    #  'standard_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['ft_pt_overtime_rates_first_two_hours_then_after_two_hours'],
    #                             'clause_references': ['23.2(a)'],
    #                             'reasoning_summary': 'For full-time and part-time '
    #                                                  'employees, overtime is paid at 150% '
    #                                                  'for the first 2 overtime hours, then '
    #                                                  '200% thereafter. The standard '
    #                                                  'first-tier multiplier is 1.5.',
    #                             'special_case_notes': 'Casual overtime has different rates '
    #                                                   'and is not the standard default for '
    #                                                   'this field.'},
    #  'extended_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['ft_pt_overtime_rates_first_two_hours_then_after_two_hours'],
    #                             'clause_references': ['23.2(a)'],
    #                             'reasoning_summary': 'The rule explicitly provides 150% '
    #                                                  'for the first 2 overtime hours and '
    #                                                  '200% thereafter, which is a two-tier '
    #                                                  'overtime structure. | The higher '
    #                                                  'overtime tier for full-time and '
    #                                                  'part-time employees is 200%, i.e. a '
    #                                                  'multiplier of 2.0.',
    #                             'special_case_notes': 'All-purpose allowances may also '
    #                                                   'apply where payable, but that does '
    #                                                   'not change the base multiplier.'},
    #  'sunday_overtime_rate': {'status': 'derived',
    #                           'source_ruleset_keys': ['overtime_consequence'],
    #                           'source_rule_ids': ['sunday_work_double_time_and_minimum_payment'],
    #                           'clause_references': ['23.5(c)'],
    #                           'reasoning_summary': 'Sunday overtime hours are paid at '
    #                                                'double time.',
    #                           'special_case_notes': 'The source also provides a 4-hour '
    #                                                 'minimum payment on Sundays.'},
    #  'saturday_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['saturday_overtime_shiftworker_saturday_ordinary_hours_and_minimum_payment'],
    #                             'clause_references': ['23.5(a)', '23.5(b)'],
    #                             'reasoning_summary': 'Saturday overtime is paid at time '
    #                                                  'and a half for the first 2 hours.',
    #                             'special_case_notes': 'The reviewed rule also states '
    #                                                   'double time thereafter. For '
    #                                                   'shiftworkers, ordinary Saturday '
    #                                                   'hours are handled separately at '
    #                                                   'time and a half in the source, but '
    #                                                   'this field captures overtime '
    #                                                   'treatment.'},
    #  'saturday_penalty_rate': {'status': 'derived',
    #                            'source_ruleset_keys': ['penalties'],
    #                            'source_rule_ids': ['shiftworker-saturday-ordinary-hours'],
    #                            'clause_references': ['Clause 23.5(b)'],
    #                            'reasoning_summary': 'The reviewed rules set Saturday '
    #                                                 'treatment through overtime-specific '
    #                                                 'provisions rather than a day-worker '
    #                                                 'penalty loading with a numeric '
    #                                                 'penalty rate in the penalties rules. '
    #                                                 "| Shiftworkers' ordinary Saturday "
    #                                                 'hours are paid at time and a half, so '
    #                                                 'the loading above base is 0.5.',
    #                            'special_case_notes': 'Saturday loading exists for '
    #                                                  "shiftworkers' ordinary hours, but "
    #                                                  'the day-worker Saturday treatment is '
    #                                                  'captured in overtime rules instead '
    #                                                  'of a standalone penalty loading. | '
    #                                                  'This applies to ordinary Saturday '
    #                                                  'hours for shiftworkers.'},
    #  'sunday_penalty_rate': {'status': 'not_found',
    #                          'source_ruleset_keys': ['penalties'],
    #                          'source_rule_ids': ['sunday-work-double-time'],
    #                          'clause_references': ['Clause 23.5(c)'],
    #                          'reasoning_summary': 'Sunday work is paid at double time, but '
    #                                               'the calculator field asks for penalty '
    #                                               'loading above base time and the '
    #                                               'reviewed rules were supplied through '
    #                                               'the overtime/penalties split with '
    #                                               'Sunday treated as overtime-specific in '
    #                                               'the source set. | Sunday work is double '
    #                                               'time, but this is treated in the '
    #                                               'weekend treatment/overtime fields '
    #                                               'rather than a standalone shiftworker '
    #                                               'Sunday penalty loading in the reviewed '
    #                                               'rules.',
    #                          'special_case_notes': 'The source supports double time for '
    #                                                'Sunday; if interpreted as loading '
    #                                                'above base, that would be 1.0, but the '
    #                                                'reviewed structure here is captured '
    #                                                'under overtime treatment. | If '
    #                                                'required as a loading above base, '
    #                                                'double time would imply 1.0 above '
    #                                                'base, but the reviewed rules do not '
    #                                                'present a separate '
    #                                                'shiftworker-specific Sunday penalty '
    #                                                'loading.'},
    #  'apply_span_overtime': {'status': 'derived',
    #                          'source_ruleset_keys': ['overtime_creation'],
    #                          'source_rule_ids': ['general-ordinary-hours-span-6am-to-6-30pm-and-broken-shifts-12-hours'],
    #                          'clause_references': ['21.3', '23.4(a)'],
    #                          'reasoning_summary': 'For non-shiftworkers, ordinary hours '
    #                                               'must fall within 6:00 am to 6:30 pm; '
    #                                               'time outside that span is overtime. | '
    #                                               'The reviewed rule states the '
    #                                               'ordinary-hours span directly.',
    #                          'special_case_notes': 'This is the standard span rule for day '
    #                                                'workers. Broken-shift spread limits '
    #                                                'also appear in the source but are not '
    #                                                'a separate live span cutoff. | Broken '
    #                                                'shifts may be spread across up to 12 '
    #                                                'hours per day, but that does not '
    #                                                'change the live span summary.'},
    #  'span_overtime_hour': {'status': 'derived',
    #                         'source_ruleset_keys': ['overtime_creation'],
    #                         'source_rule_ids': ['general-ordinary-hours-span-6am-to-6-30pm-and-broken-shifts-12-hours'],
    #                         'clause_references': ['21.3', '23.4(a)'],
    #                         'reasoning_summary': 'For non-shiftworkers, ordinary hours '
    #                                              'must fall within 6:00 am to 6:30 pm; '
    #                                              'time outside that span is overtime. | '
    #                                              'The ordinary-hours span ends at 6:30 pm, '
    #                                              'which is 18.5 in 24-hour numeric form. | '
    #                                              'The reviewed rule states the '
    #                                              'ordinary-hours span directly.',
    #                         'special_case_notes': 'This is the standard span rule for day '
    #                                               'workers. Broken-shift spread limits '
    #                                               'also appear in the source but are not a '
    #                                               'separate live span cutoff. | The source '
    #                                               'gives a 6:00 am to 6:30 pm span; the '
    #                                               'calculator stores the cutoff as 18.5. | '
    #                                               'Broken shifts may be spread across up '
    #                                               'to 12 hours per day, but that does not '
    #                                               'change the live span summary.'},
    #  'gap_penalty_hours': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_creation',
    #                                                'penalties',
    #                                                'overtime_consequence'],
    #                        'source_rule_ids': ['insufficient-break-between-work-periods-creates-overtime-on-resumption',
    #                                            'ten-hour-rest-between-work-periods',
    #                                            'overtime_for_insufficient_rest_between_work_periods'],
    #                        'clause_references': ['22.3(a)',
    #                                              '22.3(b)',
    #                                              '22.3(c)',
    #                                              'Clause 22.3(a)',
    #                                              'Clause 22.3(b)',
    #                                              'Clause 22.3(c)'],
    #                        'reasoning_summary': 'Employees must have 10 hours off between '
    #                                             'work periods, with an agreement-based '
    #                                             'reduction to 8 hours. Resumed work '
    #                                             'without the required break is paid at '
    #                                             'overtime rates until the break is '
    #                                             'satisfied. | The standard minimum break '
    #                                             'between work periods is 10 consecutive '
    #                                             'hours. | The reviewed rules provide a '
    #                                             'standard 10-hour break and an agreed '
    #                                             'reduced threshold of 8 hours.',
    #                        'special_case_notes': 'The rule has an agreement-based '
    #                                              'reduction to 8 hours; the standard '
    #                                              'calculator answer uses the 10-hour '
    #                                              'requirement. | This can be reduced to 8 '
    #                                              'hours by agreement. | Both thresholds '
    #                                              'are recorded because the reviewed source '
    #                                              'expressly provides both. The calculator '
    #                                              'should use 10 hours as the live '
    #                                              'standard.'},
    #  'gap_penalty_rate': {'status': 'derived',
    #                       'source_ruleset_keys': ['overtime_creation',
    #                                               'penalties',
    #                                               'overtime_consequence'],
    #                       'source_rule_ids': ['insufficient-break-between-work-periods-creates-overtime-on-resumption',
    #                                           'ten-hour-rest-between-work-periods',
    #                                           'overtime_for_insufficient_rest_between_work_periods'],
    #                       'clause_references': ['22.3(a)',
    #                                             '22.3(b)',
    #                                             '22.3(c)',
    #                                             'Clause 22.3(a)',
    #                                             'Clause 22.3(b)',
    #                                             'Clause 22.3(c)'],
    #                       'reasoning_summary': 'Employees must have 10 hours off between '
    #                                            'work periods, with an agreement-based '
    #                                            'reduction to 8 hours. Resumed work without '
    #                                            'the required break is paid at overtime '
    #                                            'rates until the break is satisfied. | The '
    #                                            'rule says the resumed work is paid at '
    #                                            'overtime rates; the calculator requests '
    #                                            'the loading above base, so the breach '
    #                                            'loading is 1.0. | The reviewed rules '
    #                                            'provide a standard 10-hour break and an '
    #                                            'agreed reduced threshold of 8 hours.',
    #                       'special_case_notes': 'The rule has an agreement-based reduction '
    #                                             'to 8 hours; the standard calculator '
    #                                             'answer uses the 10-hour requirement. | '
    #                                             'This field captures the overtime loading '
    #                                             'above base, not the total paid rate. | '
    #                                             'Both thresholds are recorded because the '
    #                                             'reviewed source expressly provides both. '
    #                                             'The calculator should use 10 hours as the '
    #                                             'live standard.'},
    #  'penalties': {'status': 'derived',
    #                'source_ruleset_keys': ['penalties', 'overtime_consequence'],
    #                'source_rule_ids': ['shiftwork-allowances-by-shift-commencement-or-finish',
    #                                    'casual-loading-for-ordinary-hours',
    #                                    'interrupted_meal_break_overtime_until_uninterrupted_break',
    #                                    'minimum-four-hours-on-saturday-sunday-or-public-holiday',
    #                                    'public-holiday-rdo-full-time-employee',
    #                                    'part-day-public-holiday-continuous-shift-counts-toward-minimum'],
    #                'clause_references': ['Clause 23.4(c)',
    #                                      'Clause 23.4(d)(i)',
    #                                      'Clause 23.4(d)(ii)',
    #                                      'Clause 23.4(d)(iii)',
    #                                      'Clause 23.4(d)(iv)',
    #                                      'Clause 10.5(a)',
    #                                      'Clause 10.5(c)',
    #                                      'Clause 10.5(d)',
    #                                      '22.1(b)',
    #                                      'Clause 23.5(e)',
    #                                      'Clause 27.4(a)',
    #                                      'Clause 27.4(b)',
    #                                      'Clause 23.5(f)'],
    #                'reasoning_summary': 'The reviewed penalties rules contain standard '
    #                                     'shiftworker loadings that can be expressed with '
    #                                     'numeric time windows or shift-start/end criteria. '
    #                                     '| The reviewed rules provide a 25% casual loading '
    #                                     'for ordinary hours, which is a time-based premium '
    #                                     'applicable to ordinary hours worked. | These '
    #                                     'provisions affect payment outcomes but are not '
    #                                     'standard weekday penalty loadings that fit the '
    #                                     'live weekday penalty structure.',
    #                'special_case_notes': 'The source also describes non-rotating night '
    #                                      'shifts as a classification condition; the '
    #                                      'loading is included because the rule clearly '
    #                                      'states the rate, but the classification aspect '
    #                                      'may require separate logic outside the timing '
    #                                      'window. | The source also mentions minimum '
    #                                      'engagement and payment timing, but those are not '
    #                                      'penalty loadings. | Meal-break interruption '
    #                                      'creates overtime until an uninterrupted break is '
    #                                      'taken; public-holiday minimum-payment and '
    #                                      'rostered-day-off rules are operational '
    #                                      'consequences rather than weekday penalty rates.'},
    #  'hours_pen_rules': {'status': 'defaulted',
    #                      'source_ruleset_keys': [],
    #                      'source_rule_ids': [],
    #                      'clause_references': [],
    #                      'reasoning_summary': 'No separate hours_pen_rules mapping is '
    #                                           'generated in step 6.1 yet.',
    #                      'special_case_notes': ''},
    #  'weekend_rules': {'status': 'derived',
    #                    'source_ruleset_keys': ['overtime_consequence', 'penalties'],
    #                    'source_rule_ids': ['saturday_overtime_shiftworker_saturday_ordinary_hours_and_minimum_payment',
    #                                        'shiftworker-saturday-ordinary-hours',
    #                                        'sunday_work_double_time_and_minimum_payment',
    #                                        'sunday-work-double-time'],
    #                    'clause_references': ['23.5(a)',
    #                                          '23.5(b)',
    #                                          'Clause 23.5(b)',
    #                                          '23.5(c)',
    #                                          'Clause 23.5(c)'],
    #                    'reasoning_summary': 'Saturday work is treated through '
    #                                         'overtime/penalty provisions in the reviewed '
    #                                         'rules. For day workers, Saturday work is '
    #                                         'within the overtime-specific Saturday rules; '
    #                                         'for shiftworkers, ordinary Saturday hours '
    #                                         'have a separate loading. | Sunday work is '
    #                                         'paid at double time in the reviewed rules, '
    #                                         'which is treated as overtime for the '
    #                                         "calculator's weekend treatment field. | "
    #                                         'Shiftworkers required to work ordinary hours '
    #                                         'on a Saturday must be paid time and a half, '
    #                                         'which is a penalty-style loading rather than '
    #                                         'overtime. | Sunday work is paid at double '
    #                                         'time in the reviewed rules. | The reviewed '
    #                                         'rules set Saturday treatment through '
    #                                         'overtime-specific provisions rather than a '
    #                                         'day-worker penalty loading with a numeric '
    #                                         'penalty rate in the penalties rules. | Sunday '
    #                                         'work is paid at double time, but the '
    #                                         'calculator field asks for penalty loading '
    #                                         'above base time and the reviewed rules were '
    #                                         'supplied through the overtime/penalties split '
    #                                         'with Sunday treated as overtime-specific in '
    #                                         "the source set. | Shiftworkers' ordinary "
    #                                         'Saturday hours are paid at time and a half, '
    #                                         'so the loading above base is 0.5. | Sunday '
    #                                         'work is double time, but this is treated in '
    #                                         'the weekend treatment/overtime fields rather '
    #                                         'than a standalone shiftworker Sunday penalty '
    #                                         'loading in the reviewed rules.',
    #                    'special_case_notes': 'Shiftworkers have a distinct Saturday '
    #                                          'ordinary-hours loading of time and a half, '
    #                                          'but the standard weekend-treatment '
    #                                          'classification for Saturday in the '
    #                                          'overtime-consequence rules is '
    #                                          'overtime-oriented. | Saturday overtime for '
    #                                          'shiftworkers is handled separately in the '
    #                                          'overtime rules, but ordinary Saturday hours '
    #                                          'are the live penalty case. | The Sunday rule '
    #                                          'applies to all employees. | Saturday loading '
    #                                          "exists for shiftworkers' ordinary hours, but "
    #                                          'the day-worker Saturday treatment is '
    #                                          'captured in overtime rules instead of a '
    #                                          'standalone penalty loading. | The source '
    #                                          'supports double time for Sunday; if '
    #                                          'interpreted as loading above base, that '
    #                                          'would be 1.0, but the reviewed structure '
    #                                          'here is captured under overtime treatment. | '
    #                                          'This applies to ordinary Saturday hours for '
    #                                          'shiftworkers. | If required as a loading '
    #                                          'above base, double time would imply 1.0 '
    #                                          'above base, but the reviewed rules do not '
    #                                          'present a separate shiftworker-specific '
    #                                          'Sunday penalty loading.'},
    #  'two_tier_overtime': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_consequence'],
    #                        'source_rule_ids': ['ft_pt_overtime_rates_first_two_hours_then_after_two_hours'],
    #                        'clause_references': ['23.2(a)'],
    #                        'reasoning_summary': 'The rule explicitly provides 150% for the '
    #                                             'first 2 overtime hours and 200% '
    #                                             'thereafter, which is a two-tier overtime '
    #                                             'structure.',
    #                        'special_case_notes': ''},
    #  'two_tier_overtime_threshold': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_consequence'],
    #                                  'source_rule_ids': ['ft_pt_overtime_rates_first_two_hours_then_after_two_hours'],
    #                                  'clause_references': ['23.2(a)'],
    #                                  'reasoning_summary': 'The rule explicitly provides '
    #                                                       '150% for the first 2 overtime '
    #                                                       'hours and 200% thereafter, '
    #                                                       'which is a two-tier overtime '
    #                                                       'structure. | The higher '
    #                                                       'overtime rate starts after the '
    #                                                       'first 2 overtime hours.',
    #                                  'special_case_notes': 'Each day is calculated '
    #                                                        'separately for overtime.'},
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
