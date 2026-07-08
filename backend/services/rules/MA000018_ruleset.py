"""Rule engine for award pay calculations."""


class MA000018Rules:
    """Business rules for award MA000018 pay calculations."""

    ORDINARY_HOURS_LIMIT_DAILY = 10
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
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    PENALTIES = {'shift_allowance_1000_1300': {'type': 'shift_based',
                                   'basis': 'start',
                                   'start': 10,
                                   'end': 13,
                                   'rate': 0.1,
                                   'description': 'Shift allowance for shifts commencing '
                                                  'between 10:00 and before 13:00.',
                                   'applies_to': ['shift']},
     'shift_allowance_1300_1600': {'type': 'shift_based',
                                   'basis': 'start',
                                   'start': 13,
                                   'end': 16,
                                   'rate': 0.125,
                                   'description': 'Shift allowance for shifts commencing '
                                                  'between 13:00 and before 16:00.',
                                   'applies_to': ['shift']},
     'shift_allowance_1600_0400': {'type': 'shift_based',
                                   'basis': 'start',
                                   'start': 16,
                                   'end': 4,
                                   'rate': 0.15,
                                   'description': 'Shift allowance for shifts commencing '
                                                  'between 16:00 and before 04:00.',
                                   'applies_to': ['shift']},
     'shift_allowance_0400_0600': {'type': 'shift_based',
                                   'basis': 'start',
                                   'start': 4,
                                   'end': 6,
                                   'rate': 0.1,
                                   'description': 'Shift allowance for shifts commencing '
                                                  'between 04:00 and before 06:00.',
                                   'applies_to': ['shift']}}
    HOURS_PEN_RULES = {}
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': True}, 'Sunday': {'is_overtime': True}},
     'shift': {'Saturday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.5},
               'Sunday': {'is_overtime': False, 'rate': None, 'penalty_rate': 0.75}}}
    DEFAULT_BREAK = 0.5

    # FIELD_EVIDENCE = {'ordinary_hours_limit_daily': {'status': 'derived',
    #                                 'source_ruleset_keys': ['overtime_creation'],
    #                                 'source_rule_ids': ['ordinary-hours-daily-limit-8-hours-day-shift-or-10-hours-night-shift'],
    #                                 'clause_references': ['22.1(c)'],
    #                                 'reasoning_summary': 'The reviewed rules expressly '
    #                                                      'allow ordinary hours to be '
    #                                                      'worked as 10 hours on a night '
    #                                                      'shift. This is the clearest '
    #                                                      'daily limit for shiftworkers in '
    #                                                      'the reviewed material.',
    #                                 'special_case_notes': 'The source frames this as a '
    #                                                       'day-shift versus night-shift '
    #                                                       'ordinary-hours choice rather '
    #                                                       'than a separate universal '
    #                                                       'shiftworker rule. Used as the '
    #                                                       'best live shiftworker daily '
    #                                                       'limit.'},
    #  'ordinary_hours_limit_weekly': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_creation'],
    #                                  'source_rule_ids': ['full-time-overtime-beyond-rostered-ordinary-hours',
    #                                                      'part-time-overtime-over-38-per-week-or-76-per-fortnight',
    #                                                      'casual-overtime-over-38-per-week-or-76-per-fortnight',
    #                                                      'ordinary-hours-week-fortnight-and-rostered-cycle-framework'],
    #                                  'clause_references': ['10.2',
    #                                                        '10.3(a)',
    #                                                        '10.4(a)',
    #                                                        '22.1',
    #                                                        '22.3'],
    #                                  'reasoning_summary': 'The reviewed rules state a '
    #                                                       '38-hour weekly ordinary-hours '
    #                                                       'benchmark across cohorts, '
    #                                                       'including shiftwork '
    #                                                       'arrangements, subject to '
    #                                                       'roster-cycle and averaging '
    #                                                       'rules.',
    #                                  'special_case_notes': 'This is the standard weekly '
    #                                                        'limit used for the calculator '
    #                                                        'even though some rules also '
    #                                                        'refer to fortnightly and '
    #                                                        'roster-cycle boundaries.'},
    #  'day_worker_ordinary_hours_daily': {'status': 'derived',
    #                                      'source_ruleset_keys': ['overtime_creation'],
    #                                      'source_rule_ids': ['ordinary-hours-daily-limit-8-hours-day-shift-or-10-hours-night-shift'],
    #                                      'clause_references': ['22.1(c)'],
    #                                      'reasoning_summary': 'The reviewed rules state '
    #                                                           'ordinary hours may be '
    #                                                           'worked as eight hours on a '
    #                                                           'day shift, with a separate '
    #                                                           '10-hour night-shift option. '
    #                                                           'For the standard day-worker '
    #                                                           'daily live limit, 8 hours '
    #                                                           'is the clearest default.',
    #                                      'special_case_notes': 'The source also mentions a '
    #                                                            '10-hour night-shift '
    #                                                            'ordinary-hours option, but '
    #                                                            'the calculator needs one '
    #                                                            'standard live limit. This '
    #                                                            'answer uses the day-shift '
    #                                                            'standard.'},
    #  'day_worker_ordinary_hours_weekly': {'status': 'derived',
    #                                       'source_ruleset_keys': ['overtime_creation'],
    #                                       'source_rule_ids': ['full-time-overtime-beyond-rostered-ordinary-hours',
    #                                                           'part-time-overtime-over-38-per-week-or-76-per-fortnight',
    #                                                           'casual-overtime-over-38-per-week-or-76-per-fortnight',
    #                                                           'ordinary-hours-week-fortnight-and-rostered-cycle-framework'],
    #                                       'clause_references': ['10.2',
    #                                                             '10.3(a)',
    #                                                             '10.4(a)',
    #                                                             '22.1',
    #                                                             '22.3'],
    #                                       'reasoning_summary': 'The reviewed rules '
    #                                                            'repeatedly identify 38 '
    #                                                            'hours per week as the '
    #                                                            'ordinary-hours weekly '
    #                                                            'benchmark across cohorts, '
    #                                                            'with overtime triggered '
    #                                                            'beyond that boundary.',
    #                                       'special_case_notes': 'The award also refers to '
    #                                                             'averaging and '
    #                                                             'roster-cycle limits in '
    #                                                             'clause 22.1, but 38 hours '
    #                                                             'per week is the standard '
    #                                                             'live weekly benchmark.'},
    #  'standard_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['merged-25-1-a-full-time-overtime-rates',
    #                                                 'merged-25-1-b-part-time-overtime-rates'],
    #                             'clause_references': ['25.1(a)(i)',
    #                                                   '25.1(b)(i)',
    #                                                   '25.1(b)(ii)',
    #                                                   '25.1(b)(iii)'],
    #                             'reasoning_summary': 'The standard overtime rate for '
    #                                                  'full-time and part-time employees is '
    #                                                  '150% for the first two hours, which '
    #                                                  'is a 0.5 loading above base.',
    #                             'special_case_notes': 'The source contains higher overtime '
    #                                                   'tiers after the first two hours. '
    #                                                   'This field records the standard '
    #                                                   'initial overtime loading only.'},
    #  'extended_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['merged-25-1-a-full-time-overtime-rates',
    #                                                 'merged-25-1-b-part-time-overtime-rates',
    #                                                 'merged-10-4-c-casual-overtime-rates'],
    #                             'clause_references': ['25.1(a)(i)',
    #                                                   '25.1(b)(i)',
    #                                                   '25.1(c)(i)',
    #                                                   '25.1(c)(ii)'],
    #                             'reasoning_summary': 'The reviewed rules provide a '
    #                                                  'first-tier overtime rate and a '
    #                                                  'higher rate thereafter for '
    #                                                  'full-time, part-time, and casual '
    #                                                  'overtime in the standard contexts. | '
    #                                                  'The higher overtime tier is 200% for '
    #                                                  'full-time and part-time overtime '
    #                                                  'after the first two hours, which is '
    #                                                  'a 1.0 loading above base.',
    #                             'special_case_notes': 'Casual overtime also has a two-tier '
    #                                                   'structure, but the exact rates '
    #                                                   'differ by overtime trigger and day '
    #                                                   'of week. | Casual overtime also has '
    #                                                   'a 250% tier in some contexts, but '
    #                                                   'the calculator’s standard higher '
    #                                                   'tier is 200%.'},
    #  'sunday_overtime_rate': {'status': 'derived',
    #                           'source_ruleset_keys': ['overtime_consequence'],
    #                           'source_rule_ids': ['merged-25-1-a-full-time-overtime-rates',
    #                                               'merged-25-1-b-part-time-overtime-rates',
    #                                               'merged-10-4-c-casual-overtime-rates'],
    #                           'clause_references': ['25.1(a)(i)',
    #                                                 '25.1(b)(i)',
    #                                                 '25.1(c)(i)',
    #                                                 '25.1(c)(ii)'],
    #                           'reasoning_summary': 'The reviewed overtime rules specify '
    #                                                '200% on Sunday for full-time and '
    #                                                'part-time overtime, which is a 1.0 '
    #                                                'loading above base.',
    #                           'special_case_notes': 'For casuals, Sunday overtime/penalty '
    #                                                 'outcomes are handled in the casual '
    #                                                 'weekend and overtime rules and may '
    #                                                 'differ by trigger.'},
    #  'saturday_overtime_rate': {'status': 'derived',
    #                             'source_ruleset_keys': ['overtime_consequence'],
    #                             'source_rule_ids': ['merged-25-1-a-full-time-overtime-rates',
    #                                                 'merged-25-1-b-part-time-overtime-rates',
    #                                                 'merged-10-4-c-casual-overtime-rates'],
    #                             'clause_references': ['25.1(a)(i)',
    #                                                   '25.1(b)(i)',
    #                                                   '25.1(c)(i)',
    #                                                   '25.1(c)(ii)'],
    #                             'reasoning_summary': 'The reviewed overtime rules specify '
    #                                                  '200% on Saturday for full-time and '
    #                                                  'part-time overtime, which is a 1.0 '
    #                                                  'loading above base.',
    #                             'special_case_notes': 'Weekend overtime treatment may '
    #                                                   'differ for casual employees and for '
    #                                                   'shiftworkers under weekend '
    #                                                   'ordinary-hours rules.'},
    #  'apply_span_overtime': {'status': 'derived',
    #                          'source_ruleset_keys': ['overtime_creation'],
    #                          'source_rule_ids': ['day-worker-span-outside-6am-to-6pm-monday-to-friday'],
    #                          'clause_references': ['22.2(a)', '22.1(c)'],
    #                          'reasoning_summary': 'The reviewed rules state that '
    #                                               'day-worker ordinary hours fall between '
    #                                               '6am and 6pm Monday to Friday and that '
    #                                               'work outside that span is outside '
    #                                               'ordinary hours and may be treated as '
    #                                               'overtime. | The reviewed rules '
    #                                               'expressly confine day-worker ordinary '
    #                                               'hours to the weekday 6am to 6pm span.',
    #                          'special_case_notes': 'The source describes a span boundary '
    #                                                'rather than a complete overtime '
    #                                                'algorithm, but it clearly supports '
    #                                                'span overtime for day workers. | Work '
    #                                                'outside this span is outside ordinary '
    #                                                'hours for day workers and may be '
    #                                                'treated as overtime or shiftwork under '
    #                                                'the award.'},
    #  'span_overtime_hour': {'status': 'derived',
    #                         'source_ruleset_keys': ['overtime_creation'],
    #                         'source_rule_ids': ['day-worker-span-outside-6am-to-6pm-monday-to-friday'],
    #                         'clause_references': ['22.2(a)', '22.1(c)'],
    #                         'reasoning_summary': 'The reviewed rules state that day-worker '
    #                                              'ordinary hours fall between 6am and 6pm '
    #                                              'Monday to Friday and that work outside '
    #                                              'that span is outside ordinary hours and '
    #                                              'may be treated as overtime. | The live '
    #                                              'span boundary for day workers is 6am to '
    #                                              '6pm; the earliest cutoff is 6am. | The '
    #                                              'reviewed rules expressly confine '
    #                                              'day-worker ordinary hours to the weekday '
    #                                              '6am to 6pm span.',
    #                         'special_case_notes': 'The source describes a span boundary '
    #                                               'rather than a complete overtime '
    #                                               'algorithm, but it clearly supports span '
    #                                               'overtime for day workers. | The award '
    #                                               'has both a start and end boundary. The '
    #                                               'calculator needs one live cutoff, so '
    #                                               '6am is used as the main live cutoff. | '
    #                                               'Work outside this span is outside '
    #                                               'ordinary hours for day workers and may '
    #                                               'be treated as overtime or shiftwork '
    #                                               'under the award.'},
    #  'gap_penalty_hours': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_creation', 'penalties'],
    #                        'source_rule_ids': ['rest-period-after-overtime-less-than-10-consecutive-hours-off-duty',
    #                                            'rest-break-between-rostered-work-22-4',
    #                                            'sleepover-eight-hour-rest-gap-and-release',
    #                                            'sleepover-resume-without-eight-hour-rest-double-time'],
    #                        'clause_references': ['25.1(d)(i)',
    #                                              '25.1(d)(ii)',
    #                                              'clause 22.4(a)',
    #                                              'clause 22.4(b)',
    #                                              'clause 22.9(g)(iv)',
    #                                              'clause 22.9(j)'],
    #                        'reasoning_summary': 'The reviewed rules require a minimum rest '
    #                                             'break between shifts and also provide a '
    #                                             'post-overtime rest consequence when the '
    #                                             'break is not met. | The standard minimum '
    #                                             'break is 10 consecutive hours off duty '
    #                                             'between shifts. | The reviewed rules '
    #                                             'contain multiple rest-gap thresholds for '
    #                                             'different contexts, so the calculator '
    #                                             'records the standard live threshold plus '
    #                                             'special cases.',
    #                        'special_case_notes': 'The source contains both a general '
    #                                              '10-hour rule and a mutually agreed '
    #                                              'reduction to 8 hours, plus a separate '
    #                                              'post-overtime 10-hour release rule. | '
    #                                              'The source also allows an agreed '
    #                                              'reduction to 8 hours, but 10 hours is '
    #                                              'the standard live threshold. | Keep 10 '
    #                                              'hours as the standard live threshold; 8 '
    #                                              'hours applies only by mutual agreement '
    #                                              'in the general rule and in '
    #                                              'sleepover-specific consequence rules.'},
    #  'gap_penalty_rate': {'status': 'derived',
    #                       'source_ruleset_keys': ['overtime_creation', 'penalties'],
    #                       'source_rule_ids': ['rest-period-after-overtime-less-than-10-consecutive-hours-off-duty',
    #                                           'rest-break-between-rostered-work-22-4',
    #                                           'sleepover-eight-hour-rest-gap-and-release',
    #                                           'sleepover-resume-without-eight-hour-rest-double-time'],
    #                       'clause_references': ['25.1(d)(i)',
    #                                             '25.1(d)(ii)',
    #                                             'clause 22.4(a)',
    #                                             'clause 22.4(b)',
    #                                             'clause 22.9(g)(iv)',
    #                                             'clause 22.9(j)'],
    #                       'reasoning_summary': 'The reviewed rules require a minimum rest '
    #                                            'break between shifts and also provide a '
    #                                            'post-overtime rest consequence when the '
    #                                            'break is not met. | Where the employer '
    #                                            'directs continued work without the '
    #                                            'required rest, the reviewed rule pays 200% '
    #                                            'of the hourly rate, which is a 1.0 loading '
    #                                            'above base. | The reviewed rules contain '
    #                                            'multiple rest-gap thresholds for different '
    #                                            'contexts, so the calculator records the '
    #                                            'standard live threshold plus special '
    #                                            'cases.',
    #                       'special_case_notes': 'The source contains both a general '
    #                                             '10-hour rule and a mutually agreed '
    #                                             'reduction to 8 hours, plus a separate '
    #                                             'post-overtime 10-hour release rule. | '
    #                                             'This is the calculator loading above '
    #                                             'base, not the total paid rate. | Keep 10 '
    #                                             'hours as the standard live threshold; 8 '
    #                                             'hours applies only by mutual agreement in '
    #                                             'the general rule and in '
    #                                             'sleepover-specific consequence rules.'},
    #  'penalties': {'status': 'derived',
    #                'source_ruleset_keys': ['penalties', 'overtime_consequence'],
    #                'source_rule_ids': ['shiftwork-afternoon-and-night-shift-allowances',
    #                                    'casual-loading-and-basic-casual-hourly-rate',
    #                                    'public-holiday-day-workers-election',
    #                                    'public-holiday-part-time-eligibility-and-election',
    #                                    'public-holiday-casual-hours-paid-at-275',
    #                                    'sleepover-allowance-and-supporting-conditions',
    #                                    'sleepover-non-emergency-work-extra-pay',
    #                                    'sleepover-full-time-worked-time-overtime',
    #                                    'sleepover-part-time-worked-time-with-penalties',
    #                                    'sleepover-casual-worked-time-with-penalties',
    #                                    'sleepover-eight-hour-rest-gap-and-release',
    #                                    'sleepover-resume-without-eight-hour-rest-double-time',
    #                                    'rest-period-after-overtime-25-1-d'],
    #                'clause_references': ['clause 26.1',
    #                                      'clause 26.2',
    #                                      'clause 10.4(b)',
    #                                      'clause 29.2(a)(i)',
    #                                      'clause 29.2(b)(i)',
    #                                      'clause 29.2(c)(i)',
    #                                      'clause 22.9(a)',
    #                                      'clause 22.9(e)',
    #                                      'clause 22.9(g)(i)',
    #                                      'clause 22.9(g)(ii)',
    #                                      'clause 22.9(g)(iii)',
    #                                      'clause 22.9(j)',
    #                                      'clause 25.1(d)(i)',
    #                                      'clause 25.1(d)(ii)'],
    #                'reasoning_summary': 'The reviewed rules provide standard shift '
    #                                     'allowances based on the shift commencement time '
    #                                     'bands, which can be represented as shift-based '
    #                                     'weekday penalties. | No additional standard '
    #                                     'weekday time-based penalty windows beyond the '
    #                                     'shift-based commencement allowances were '
    #                                     'supported cleanly by the reviewed rules. | The '
    #                                     'reviewed rules include several non-weekday and '
    #                                     'consequence-based payments that should not be '
    #                                     'represented as live weekday penalty windows.',
    #                'special_case_notes': 'These are allowances applied to the whole shift, '
    #                                      'and for employees under 38 hours per week they '
    #                                      'apply only if the shift starts before 06:00 or '
    #                                      'finishes after 18:00. Permanent night-shift '
    #                                      'variants are not separately encoded. | Weekend, '
    #                                      'public holiday, casual-loading, meal-break, and '
    #                                      'sleepover rules were excluded from the live '
    #                                      'weekday penalty list as instructed. | Shift '
    #                                      'allowances are the only standard weekday '
    #                                      'penalty-like items encoded. All other '
    #                                      'exceptional or calendar-dependent items were '
    #                                      'excluded per instructions.'},
    #  'hours_pen_rules': {'status': 'defaulted',
    #                      'source_ruleset_keys': [],
    #                      'source_rule_ids': [],
    #                      'clause_references': [],
    #                      'reasoning_summary': 'No separate hours_pen_rules mapping is '
    #                                           'generated in step 6.1 yet.',
    #                      'special_case_notes': ''},
    #  'weekend_rules': {'status': 'derived',
    #                    'source_ruleset_keys': ['overtime_consequence',
    #                                            'overtime_creation',
    #                                            'penalties'],
    #                    'source_rule_ids': ['merged-25-1-a-full-time-overtime-rates',
    #                                        'merged-25-1-b-part-time-overtime-rates',
    #                                        'day-worker-span-outside-6am-to-6pm-monday-to-friday',
    #                                        'weekend-ordinary-hours-for-shiftworkers'],
    #                    'clause_references': ['25.1(a)(i)', '25.1(b)(i)', '22.2(a)', '23.1'],
    #                    'reasoning_summary': 'The reviewed rules do not provide a '
    #                                         'day-worker ordinary-hours penalty regime for '
    #                                         'Saturday; day-worker ordinary hours are '
    #                                         'confined to Monday to Friday, so Saturday '
    #                                         'work is treated as overtime. | The reviewed '
    #                                         'rules do not provide a day-worker '
    #                                         'ordinary-hours penalty regime for Sunday; '
    #                                         'day-worker ordinary hours are confined to '
    #                                         'Monday to Friday, so Sunday work is treated '
    #                                         'as overtime. | For shiftworkers, ordinary '
    #                                         'weekend hours attract weekend penalty-style '
    #                                         'rates rather than overtime in the reviewed '
    #                                         'rules. | For shiftworkers, ordinary Sunday '
    #                                         'hours attract weekend penalty-style rates '
    #                                         'rather than overtime in the reviewed rules. | '
    #                                         'The reviewed rules do not provide a standard '
    #                                         'day-worker Saturday penalty loading. '
    #                                         'Day-worker weekend work is treated as '
    #                                         'overtime instead. | The reviewed rules do not '
    #                                         'provide a standard day-worker Sunday penalty '
    #                                         'loading. Day-worker weekend work is treated '
    #                                         'as overtime instead. | Shiftworkers receive '
    #                                         '1.5x for Friday midnight to Saturday '
    #                                         'midnight, which is a 0.5 loading above base. '
    #                                         '| Shiftworkers receive 1.75x for Saturday '
    #                                         'midnight to Sunday midnight, which is a 0.75 '
    #                                         'loading above base.',
    #                    'special_case_notes': 'For day workers, weekend work is outside '
    #                                          'ordinary-hours span. The calculator should '
    #                                          'not treat it as a day-worker penalty rate. | '
    #                                          'This applies to ordinary hours that include '
    #                                          'weekend work for shiftworkers. | Do not '
    #                                          'infer a day-worker Saturday penalty from '
    #                                          'shiftworker or casual weekend rules. | Do '
    #                                          'not infer a day-worker Sunday penalty from '
    #                                          'shiftworker or casual weekend rules. | The '
    #                                          'source describes this as weekend '
    #                                          'ordinary-hours pay for shiftworkers, not '
    #                                          'overtime.'},
    #  'two_tier_overtime': {'status': 'derived',
    #                        'source_ruleset_keys': ['overtime_consequence'],
    #                        'source_rule_ids': ['merged-25-1-a-full-time-overtime-rates',
    #                                            'merged-25-1-b-part-time-overtime-rates',
    #                                            'merged-10-4-c-casual-overtime-rates'],
    #                        'clause_references': ['25.1(a)(i)',
    #                                              '25.1(b)(i)',
    #                                              '25.1(c)(i)',
    #                                              '25.1(c)(ii)'],
    #                        'reasoning_summary': 'The reviewed rules provide a first-tier '
    #                                             'overtime rate and a higher rate '
    #                                             'thereafter for full-time, part-time, and '
    #                                             'casual overtime in the standard contexts.',
    #                        'special_case_notes': 'Casual overtime also has a two-tier '
    #                                              'structure, but the exact rates differ by '
    #                                              'overtime trigger and day of week.'},
    #  'two_tier_overtime_threshold': {'status': 'derived',
    #                                  'source_ruleset_keys': ['overtime_consequence'],
    #                                  'source_rule_ids': ['merged-25-1-a-full-time-overtime-rates',
    #                                                      'merged-25-1-b-part-time-overtime-rates',
    #                                                      'merged-10-4-c-casual-overtime-rates'],
    #                                  'clause_references': ['25.1(a)(i)',
    #                                                        '25.1(b)(i)',
    #                                                        '25.1(c)(i)',
    #                                                        '25.1(c)(ii)'],
    #                                  'reasoning_summary': 'The reviewed rules provide a '
    #                                                       'first-tier overtime rate and a '
    #                                                       'higher rate thereafter for '
    #                                                       'full-time, part-time, and '
    #                                                       'casual overtime in the standard '
    #                                                       'contexts. | The reviewed rules '
    #                                                       'state that the higher overtime '
    #                                                       'rate applies after the first '
    #                                                       'two overtime hours in the '
    #                                                       'standard Monday-to-Friday '
    #                                                       'overtime context.',
    #                                  'special_case_notes': 'Casual overtime also has a '
    #                                                        'two-tier structure, but the '
    #                                                        'exact rates differ by overtime '
    #                                                        'trigger and day of week. | '
    #                                                        'Some casual overtime contexts '
    #                                                        'also apply the first-two-hours '
    #                                                        'rule, but '
    #                                                        'weekend/public-holiday rates '
    #                                                        'can differ.'},
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
