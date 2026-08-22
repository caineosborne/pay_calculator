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

const formatPeriodOvertime = (rule) => {
    if (!rule?.threshold) return 'Not specified';
    const period = rule.basis === 'weekly' ? 'week' : 'pay period';
    return `After ${rule.threshold} hours per ${period}`;
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
        .map(([employmentType, hours]) => {
            const formattedHours = employmentType === 'full_time' && Number(hours) === 0
                ? 'N/A'
                : `${hours || 0} hours`;
            return `${titleCase(employmentType)}: ${formattedHours}`;
        });
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

export function DisplayRules({ showRules }) {
    const { state } = usePay();
    const rules = state.calculations?.appliedRules;

    if (!showRules || !rules) return null;

    const config = rules.configuration || {};
    const selectedWorkerType = state.config.workerType === 'shift' ? 'shift' : 'day';
    const ordinaryTime = config.ordinary_time || {};
    const overtimeRates = config.pay_rates?.overtime || {};
    const shiftRules = config.shift || {};
    const dayTreatment = config.day_treatment || {};
    // Normalize the canonical penalty dictionary into one readable list.
    const configuredPenalties = Object.entries(config.penalties || rules.penalties || {})
        .filter(([, penalty]) => {
            const appliesTo = penalty?.applies_to;
            return !Array.isArray(appliesTo)
                || appliesTo.length === 0
                || appliesTo.includes(selectedWorkerType);
        })
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

    const weekendAndPublicHolidayRules = [
        ['Saturday', 'Saturday ordinary hours'],
        ['Sunday', 'Sunday ordinary hours'],
        ['public_holiday', 'Public-holiday ordinary hours'],
    ].map(([day, name]) => {
        const treatment = dayTreatment[day]?.[selectedWorkerType];
        if (!treatment) return null;
        return {
            name,
            employmentRate: formatDayTreatment(treatment),
            detail: `${titleCase(selectedWorkerType)} worker`,
        };
    }).filter(Boolean);

    const worker = state.config.workerType === 'shift' ? 'Shift worker' : 'Day worker';
    const contractedHours = hasValue(rules.contracted_hours)
        ? `${rules.contracted_hours} hours per week`
        : null;
    const fullConfiguration = rules.configuration
        ? JSON.stringify(rules.configuration, null, 2)
        : null;
    const selectedSpanWindows = ordinaryTime.span_overtime?.[selectedWorkerType] || {};
    const defaultSpan = selectedSpanWindows.default
        ? formatSpanWindow(selectedSpanWindows.default)
        : rules.span_hours?.threshold === 'N/A'
            ? 'Not applicable'
            : rules.span_hours?.threshold || 'Not applicable';
    const overtimeEntitlementRows = [
        ['Span of hours', defaultSpan],
        ...Object.entries(selectedSpanWindows)
            .filter(([day]) => day !== 'default')
            .map(([day, window]) => [`${day} ordinary span`, formatSpanWindow(window)]),
        ['Daily overtime', formatOvertime(rules.daily_overtime)],
        ordinaryTime.long_day?.ordinary_limit_hours && [
            'Long-day ordinary-hours exception',
            `Up to ${ordinaryTime.long_day.ordinary_limit_hours} hours, ${ordinaryTime.long_day.uses_per_week || 0} time${ordinaryTime.long_day.uses_per_week === 1 ? '' : 's'} per week`,
        ],
        ['Period overtime', formatPeriodOvertime(rules.weekly_overtime)],
        rules.weekly_overtime?.max_work_days && [
            'Maximum worked days',
            `${rules.weekly_overtime.max_work_days} per ${rules.weekly_overtime.max_work_days_basis === 'weekly' ? 'week' : 'pay period'}`,
        ],
        hasValue(rules.use_contracted_hours_for_overtime) && [
            'Overtime based on contracted hours',
            rules.use_contracted_hours_for_overtime ? 'Yes' : 'No',
        ],
    ].filter(Boolean);
    const shortBreakThreshold = rules.gap_penalty?.threshold
        || (config.gap_between_shifts?.minimum_hours
            ? `Less than ${config.gap_between_shifts.minimum_hours} hours between shifts`
            : null);
    const shortBreakRate = config.gap_between_shifts?.minimum_hours
        ? formatEmploymentLoadings(config.gap_between_shifts)
        : rules.gap_penalty?.rate
            || (rules.gap_penalty?.penalty_rate
                ? formatRate(rules.gap_penalty.penalty_rate)
                : null);
    const penaltyRows = [
        ...configuredPenalties,
        ...weekendAndPublicHolidayRules,
        shortBreakThreshold && {
            name: 'Short break between shifts',
            detail: shortBreakThreshold,
            employmentRate: shortBreakRate || 'Not specified',
        },
        hasValue(ordinaryTime.ordinary_rates?.casual_loading) && {
            name: 'Casual ordinary-hours loading',
            detail: 'Casual employees',
            employmentRate: formatRate(ordinaryTime.ordinary_rates.casual_loading),
        },
    ].filter(Boolean);
    const rateRows = [
        overtimeRates.weekday && ['Weekday overtime', formatEmploymentRates(overtimeRates.weekday)],
        overtimeRates.extended && overtimeRates.two_tier?.enabled && [
            'Higher-rate overtime',
            `${formatEmploymentRates(overtimeRates.extended)} after ${overtimeRates.two_tier.threshold} overtime hours on ${(overtimeRates.two_tier.days || []).join(', ')}`,
        ],
        overtimeRates.manual && ['Manual overtime', formatEmploymentRates(overtimeRates.manual)],
        overtimeRates.saturday && ['Saturday overtime', formatEmploymentRates(overtimeRates.saturday)],
        overtimeRates.sunday && ['Sunday overtime', formatEmploymentRates(overtimeRates.sunday)],
        overtimeRates.public_holiday && ['Public-holiday overtime', formatEmploymentRates(overtimeRates.public_holiday)],
    ].filter(Boolean);
    const otherRuleRows = [
        contractedHours && ['Contracted hours', contractedHours],
        hasValue(rules.pt_employees_entitled_to_contracted_topup) && ['Contracted-hours top-up for part-time employees', rules.pt_employees_entitled_to_contracted_topup ? 'Included' : 'Not included'],
        hasValue(rules.ft_employees_entitled_to_contracted_topup) && ['Contracted-hours top-up for full-time employees', rules.ft_employees_entitled_to_contracted_topup ? 'Included' : 'Not included'],
        hasValue(shiftRules.default_break_hours) && [
            'Default unpaid break',
            `${shiftRules.default_break_hours} hours`,
        ],
        formatMinimumEngagement(shiftRules.minimum_paid_shift_hours) && [
            'Minimum paid shift',
            formatMinimumEngagement(shiftRules.minimum_paid_shift_hours),
        ],
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

            <div className="rule-details rules-section-first">
                <p className="section-kicker">Overtime entitlements</p>
                <div className="rule-grid">
                    {overtimeEntitlementRows.map(([label, value]) => (
                        <div className="rule-row" key={label}><span>{label}</span><strong>{value}</strong></div>
                    ))}
                </div>
            </div>

            <div className="penalty-card">
                <div className="penalty-card-heading">
                    <div><span className="penalty-icon" aria-hidden="true">+</span><h4>Penalty loadings</h4></div>
                    <span>{penaltyRows.length} configured</span>
                </div>
                {penaltyRows.length ? (
                    <div className="penalty-list">
                        {penaltyRows.map((penalty) => (
                            <div className="penalty-row" key={penalty.name}>
                                <div><strong>{penalty.name}</strong><span>{penalty.detail}</span></div>
                                <b>{penalty.employmentRate}</b>
                            </div>
                        ))}
                    </div>
                ) : <p className="no-penalties">No penalty loadings are configured for this worker type.</p>}
            </div>

            {rateRows.length > 0 && (
                <div className="rule-details">
                    <p className="section-kicker">Rates</p>
                    <div className="rule-grid">
                        {rateRows.map(([label, value]) => (
                            <div className="rule-row" key={label}><span>{label}</span><strong>{value}</strong></div>
                        ))}
                    </div>
                </div>
            )}

            {otherRuleRows.length > 0 && (
                <div className="rule-details">
                    <p className="section-kicker">Other rules</p>
                    <div className="rule-grid">
                        {otherRuleRows.map(([label, value]) => (
                            <div className="rule-row" key={label}><span>{label}</span><strong>{value}</strong></div>
                        ))}
                    </div>
                </div>
            )}

            {fullConfiguration && (
                <details className="full-rule-config">
                    <summary>Complete configuration</summary>
                    <p>Authoritative normalized settings from the award’s Python rules configuration.</p>
                    <pre>{fullConfiguration}</pre>
                </details>
            )}
        </section>
    );
}
