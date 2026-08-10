import React from 'react';
import { usePay } from '../../context/PayContext';

const titleCase = (value) => value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const formatRate = (rate) => {
    const percentage = Number(rate || 0) * 100;
    const value = Number.isInteger(percentage) ? percentage : percentage.toFixed(1);
    return `${value}% loading`;
};
const formatTime = (time) => {
    const value = Number(time);
    if (!Number.isFinite(value)) return 'Not specified';
    const hours = Math.floor(value);
    const minutes = Math.round((value - hours) * 60);
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
};

const formatOvertime = (rule) => {
    if (!rule?.threshold) return 'Not specified';
    return typeof rule.threshold === 'number'
        ? `After ${rule.threshold} hours`
        : rule.threshold;
};

const formatSpan = (rule) => rule?.threshold || 'Not specified';

const formatWeekendRule = (rule) => {
    if (!rule) return 'Not specified';
    if (rule.is_overtime || rule.base_classification === 'overtime') return 'All hours are paid as overtime';
    const loading = rule.ordinary_loading ?? rule.penalty_rate;
    if (hasValue(loading)) return formatRate(loading);
    return 'Not specified';
};

const hasValue = (value) => value !== null && value !== undefined && value !== '';

const formatMultiplier = (rate) => {
    if (!hasValue(rate)) return 'Not specified';
    return `${Number(rate).toFixed(Number(rate) % 1 ? 2 : 1)}x`;
};

const formatEmploymentRates = (rate = {}) => {
    const standard = formatMultiplier(rate.multiplier);
    return hasValue(rate.casual)
        ? `Full-time / part-time: ${standard}; casual: ${formatMultiplier(rate.casual)}`
        : standard;
};

const formatEmploymentLoadings = (rule = {}) => {
    const standard = formatRate(rule.rate ?? rule.loading);
    return hasValue(rule.casual_rate)
        ? `Full-time / part-time: ${standard}; casual: ${formatRate(rule.casual_rate)}`
        : standard;
};

const formatMinimumEngagement = (rule) => {
    if (!rule || typeof rule !== 'object') return null;
    const values = Object.entries(rule)
        .filter(([key]) => key !== 'variation')
        .map(([employmentType, hours]) =>
            `${titleCase(employmentType)}: ${hours || 0} hours`
        );
    return values.length ? values.join('; ') : null;
};

const formatDayTreatment = (rule) => {
    if (!rule) return 'Not specified';
    if (rule.base_classification === 'overtime') return 'All hours are overtime';
    const ordinary = formatRate(rule.ordinary_loading);
    return hasValue(rule.casual_rate)
        ? `Full-time / part-time: ${ordinary}; casual: ${formatRate(rule.casual_rate)}`
        : ordinary;
};

const formatSpanWindow = (window = {}) => {
    if (window.enabled === false) return 'Not applicable';
    const limits = [
        hasValue(window.start) && `before ${formatTime(window.start)}`,
        hasValue(window.end) && `after ${formatTime(window.end)}`,
    ].filter(Boolean);
    return limits.length ? limits.join(' or ') : 'Not applicable';
};

const formatOrdinaryHoursLimits = (rule = {}) => {
    const excluded = new Set([
        'variation',
        'basis',
        'max_work_days',
        'max_work_days_basis',
        'part_time_uses_contracted_hours',
    ]);
    const limits = Object.entries(rule)
        .filter(([key, value]) => !excluded.has(key) && hasValue(value))
        .map(([group, hours]) => `${titleCase(group)}: ${hours} hours`);
    if (!limits.length) return null;
    const basis = rule.basis;
    if (typeof basis === 'object') {
        limits.push(`Basis: ${Object.entries(basis).map(([group, value]) => `${titleCase(group)} ${value === 'pay_period' ? 'pay period' : 'weekly'}`).join('; ')}`);
    } else if (basis) {
        limits.push(`Basis: ${basis === 'pay_period' ? 'pay period' : 'weekly'}`);
    }
    return limits.join('; ');
};

export function DisplayRules({ showRules }) {
    const { state } = usePay();
    const rules = state.calculations?.appliedRules;

    if (!showRules || !rules) return null;

    const config = rules.configuration || {};
    // Normalize the canonical penalty dictionary into one readable list.
    const penalties = Object.entries(config.penalties || rules.penalties || {})
        .map(([name, penalty]) => {
            if (!penalty || typeof penalty !== 'object') return null;
            const kind = penalty.type === 'time_based'
                ? 'For hours worked'
                : penalty.basis === 'end'
                    ? 'When the shift ends'
                    : penalty.basis === 'duration'
                        ? 'By shift duration'
                        : 'When the shift starts';
            const timeWindow =
                penalty.start !== undefined && penalty.end !== undefined
                    ? `${formatTime(penalty.start)}–${formatTime(penalty.end)}`
                    : null;
            return {
                name: penalty.description || titleCase(name.replace(/_loading$/, '')),
                employmentRate: formatEmploymentLoadings(penalty),
                detail: [
                    kind,
                    timeWindow,
                    penalty.days?.length && penalty.days.join(', '),
                    penalty.applies_to?.length && `For ${penalty.applies_to.map(titleCase).join(' and ')} workers`,
                ].filter(Boolean).join(' · '),
            };
        })
        .filter(Boolean);

    const allPenalties = penalties;
    const worker = state.config.workerType === 'shift' ? 'Shift worker' : 'Day worker';
    const gapPenalty =
        rules.gap_penalty?.threshold && rules.gap_penalty?.rate
            ? `${rules.gap_penalty.threshold} · ${rules.gap_penalty.rate}`
            : rules.gap_penalty?.penalty_rate
              ? formatRate(rules.gap_penalty.penalty_rate)
              : null;
    const contractedHours = hasValue(rules.contracted_hours)
        ? `${rules.contracted_hours} hours per week`
        : null;
    const detailRows = [
        contractedHours && ['Effective contracted hours', contractedHours],
        hasValue(rules.use_contracted_hours_for_overtime) && [
            'Overtime based on contracted hours',
            rules.use_contracted_hours_for_overtime
                ? `Yes — after ${contractedHours || 'contracted hours'}`
                : `No${contractedHours ? ` — after ${contractedHours}` : ''}`,
        ],
        hasValue(rules.pt_employees_entitled_to_contracted_topup) && ['Contracted-hours top-up for part-time employees', rules.pt_employees_entitled_to_contracted_topup ? 'Included' : 'Not included'],
        hasValue(rules.ft_employees_entitled_to_contracted_topup) && ['Contracted-hours top-up for full-time employees', rules.ft_employees_entitled_to_contracted_topup ? 'Included' : 'Not included'],
    ].filter(Boolean);
    const fullConfiguration = rules.configuration
        ? JSON.stringify(rules.configuration, null, 2)
        : null;
    const ordinaryTime = config.ordinary_time || {};
    const overtimeRates = config.pay_rates?.overtime || {};
    const shiftRules = config.shift || {};
    const dayTreatment = config.day_treatment || {};
    const spanRuleRows = Object.entries(ordinaryTime.span_overtime || {})
        .flatMap(([workerType, windows]) =>
            Object.entries(windows || {}).map(([day, window]) => [
                `${day === 'default' ? 'Standard' : day} ordinary span (${titleCase(workerType)} workers)`,
                formatSpanWindow(window),
            ])
        );
    const additionalRules = [
        hasValue(shiftRules.default_break_hours) && [
            'Default unpaid break',
            `${shiftRules.default_break_hours} hours`,
        ],
        formatMinimumEngagement(shiftRules.minimum_paid_shift_hours) && [
            'Minimum paid shift',
            formatMinimumEngagement(shiftRules.minimum_paid_shift_hours),
        ],
        formatOrdinaryHoursLimits(ordinaryTime.daily) && [
            'Daily ordinary-hours limits',
            formatOrdinaryHoursLimits(ordinaryTime.daily),
        ],
        formatOrdinaryHoursLimits(ordinaryTime.period) && [
            'Period ordinary-hours limits',
            formatOrdinaryHoursLimits(ordinaryTime.period),
        ],
        hasValue(ordinaryTime.ordinary_rates?.casual_loading) && [
            'Casual ordinary-hours loading',
            formatRate(ordinaryTime.ordinary_rates.casual_loading),
        ],
        ordinaryTime.long_day?.ordinary_limit_hours && [
            'Long-day ordinary-hours exception',
            `Up to ${ordinaryTime.long_day.ordinary_limit_hours} hours, ${ordinaryTime.long_day.uses_per_week || 0} time${ordinaryTime.long_day.uses_per_week === 1 ? '' : 's'} per week`,
        ],
        config.gap_between_shifts?.minimum_hours && [
            'Insufficient-break loading',
            `After a break of less than ${config.gap_between_shifts.minimum_hours} hours: ${formatEmploymentLoadings(config.gap_between_shifts)}`,
        ],
        ...spanRuleRows,
        overtimeRates.weekday && ['Weekday overtime', formatEmploymentRates(overtimeRates.weekday)],
        overtimeRates.extended && overtimeRates.two_tier?.enabled && [
            'Higher-rate overtime',
            `${formatEmploymentRates(overtimeRates.extended)} after ${overtimeRates.two_tier.threshold} overtime hours on ${(overtimeRates.two_tier.days || []).join(', ')}`,
        ],
        overtimeRates.manual && ['Manual overtime', formatEmploymentRates(overtimeRates.manual)],
        overtimeRates.saturday && ['Saturday overtime', formatEmploymentRates(overtimeRates.saturday)],
        overtimeRates.sunday && ['Sunday overtime', formatEmploymentRates(overtimeRates.sunday)],
        overtimeRates.public_holiday && ['Public-holiday overtime', formatEmploymentRates(overtimeRates.public_holiday)],
        dayTreatment.public_holiday?.day && [
            'Public-holiday ordinary hours (day workers)',
            formatDayTreatment(dayTreatment.public_holiday.day),
        ],
        dayTreatment.public_holiday?.shift && [
            'Public-holiday ordinary hours (shift workers)',
            formatDayTreatment(dayTreatment.public_holiday.shift),
        ],
        ...['Saturday', 'Sunday'].flatMap((day) => [
            dayTreatment[day]?.day && [
                `${day} ordinary hours (day workers)`,
                formatDayTreatment(dayTreatment[day].day),
            ],
            dayTreatment[day]?.shift && [
                `${day} ordinary hours (shift workers)`,
                formatDayTreatment(dayTreatment[day].shift),
            ],
        ]),
    ].filter(Boolean);

    return (
        <section className="rules-panel" aria-label="Pay rules that apply">
            <div className="rules-heading">
                <div>
                    <p className="section-kicker">How your pay is worked out</p>
                    <h3>{worker} rules</h3>
                </div>
                <span className="rules-badge">Current award settings</span>
            </div>

                <div className="rule-grid">
                <div className="rule-row"><span>Span of hours</span><strong>{rules.span_hours?.threshold === 'N/A' ? 'Not applicable' : formatSpan(rules.span_hours)}</strong></div>
                {hasValue(rules.span_hours?.rate) && rules.span_hours.rate !== 'N/A' && <div className="rule-row"><span>Span overtime rate</span><strong>{rules.span_hours.rate}</strong></div>}
                <div className="rule-row"><span>Daily overtime</span><strong>{formatOvertime(rules.daily_overtime)}</strong></div>
                <div className="rule-row"><span>Daily overtime rate</span><strong>{rules.daily_overtime?.rate || 'Not specified'}</strong></div>
                <div className="rule-row"><span>{rules.weekly_overtime?.basis === 'weekly' ? 'Weekly overtime' : 'Pay-period overtime'}</span><strong>{formatOvertime(rules.weekly_overtime)}</strong></div>
                <div className="rule-row"><span>Period overtime rate</span><strong>{rules.weekly_overtime?.rate || 'Not specified'}</strong></div>
                {rules.weekly_overtime?.max_work_days && <div className="rule-row"><span>Maximum worked days</span><strong>{rules.weekly_overtime.max_work_days} per {rules.weekly_overtime.max_work_days_basis === 'weekly' ? 'week' : 'pay period'}</strong></div>}
                <div className="rule-row"><span>Saturday</span><strong>{formatWeekendRule(rules.saturday_rules)}</strong></div>
                <div className="rule-row"><span>Sunday</span><strong>{formatWeekendRule(rules.sunday_rules)}</strong></div>
                {gapPenalty && <div className="rule-row"><span>Short break between shifts</span><strong>{gapPenalty}</strong></div>}
            </div>

            <div className="penalty-card">
                <div className="penalty-card-heading">
                    <div><span className="penalty-icon" aria-hidden="true">+</span><h4>Penalty loadings</h4></div>
                    <span>{allPenalties.length} configured</span>
                </div>
                {allPenalties.length ? (
                    <div className="penalty-list">
                        {allPenalties.map((penalty) => (
                            <div className="penalty-row" key={`${penalty.name}-${penalty.detail}`}>
                                <div><strong>{penalty.name}</strong><span>{penalty.detail}</span></div>
                                <b>{penalty.employmentRate}</b>
                            </div>
                        ))}
                    </div>
                ) : <p className="no-penalties">No weekday penalty loadings are configured for this award.</p>}
            </div>

            {detailRows.length > 0 && (
                <div className="rule-details">
                    <p className="section-kicker">Other rule details</p>
                    <div className="rule-grid">
                        {detailRows.map(([label, value]) => (
                            <div className="rule-row" key={label}><span>{label}</span><strong>{value}</strong></div>
                        ))}
                    </div>
                </div>
            )}

            {additionalRules.length > 0 && (
                <div className="rule-details">
                    <p className="section-kicker">Additional configured rules</p>
                    <div className="rule-grid">
                        {additionalRules.map(([label, value]) => (
                            <div className="rule-row" key={label}><span>{label}</span><strong>{value}</strong></div>
                        ))}
                    </div>
                </div>
            )}

            {fullConfiguration && (
                <details className="full-rule-config">
                    <summary>Complete configuration</summary>
                    <p>All normalized award settings used for this calculation.</p>
                    <pre>{fullConfiguration}</pre>
                </details>
            )}
        </section>
    );
}
