import React from 'react';
import { usePay } from '../../context/PayContext';

const titleCase = (value) => value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const formatRate = (rate) => `${Math.round(Number(rate || 0) * 100)}% loading`;
const formatTime = (time) => `${String(time).padStart(2, '0')}:00`;

const formatOvertime = (rule) => {
    if (!rule?.threshold || !rule?.rate) return 'Not specified';
    return `After ${rule.threshold} hours · ${rule.rate}`;
};

const formatWeekendRule = (rule) => {
    if (!rule) return 'Not specified';
    if (rule.is_overtime) return 'All hours are paid as overtime';
    if (rule.penalty_rate) return `${formatRate(rule.penalty_rate)}`;
    return 'Not specified';
};

const hasValue = (value) => value !== null && value !== undefined && value !== '';

export function DisplayRules({ showRules }) {
    const { state } = usePay();
    const rules = state.calculations?.appliedRules;

    if (!showRules || !rules) return null;

    // The response may contain unified, legacy hourly, and legacy shift-start
    // penalties. Normalize all three sources before rendering one list.
    const penalties = Object.entries(rules.penalties || {})
        .map(([name, penalty]) => {
            if (!penalty || typeof penalty !== 'object') return null;
            const kind = penalty.type === 'time_based'
                ? 'For hours worked'
                : 'When the shift starts';
            const timeWindow =
                penalty.start !== undefined && penalty.end !== undefined
                    ? `${formatTime(penalty.start)}–${formatTime(penalty.end)}`
                    : null;
            return {
                name: titleCase(name.replace(/_loading$/, '')),
                rate: formatRate(
                    penalty.rate ?? penalty.penalty_rate
                ),
                detail: [kind, timeWindow].filter(Boolean).join(' · '),
            };
        })
        .filter(Boolean);

    const hourlyPenalties = Object.entries(rules.hourly_penalties || {})
        .filter(([key]) => key !== 'note')
        .map(([name, detail]) => ({
            name: titleCase(name),
            rate: typeof detail === 'string' ? detail : 'Applies at the specified time',
            detail: rules.hourly_penalties.note || 'Weekdays only',
        }));

    const shiftStartPenalties = Object.entries(rules.shift_start_penalties || {})
        .filter(([, detail]) => hasValue(detail))
        .map(([name, detail]) => ({
            name: titleCase(name.replace(/_/g, ' ')),
            rate: detail,
            detail: 'When the shift starts',
        }));

    const allPenalties = [...penalties, ...shiftStartPenalties, ...hourlyPenalties];
    const worker = state.config.workerType === 'shift' ? 'Shift worker' : 'Day worker';
    const employment = state.config.employmentType?.replace('_', ' ');
    const gapPenalty =
        rules.gap_penalty?.threshold && rules.gap_penalty?.rate
            ? `${rules.gap_penalty.threshold} · ${rules.gap_penalty.rate}`
            : rules.gap_penalty?.penalty_rate
              ? formatRate(rules.gap_penalty.penalty_rate)
              : null;
    const detailRows = [
        hasValue(rules.employment_type) && ['Employment type', titleCase(rules.employment_type)],
        hasValue(rules.contracted_hours) && ['Contracted hours', `${rules.contracted_hours} hours per week`],
        hasValue(rules.use_contracted_hours_for_overtime) && ['Overtime based on contracted hours', rules.use_contracted_hours_for_overtime ? 'Yes' : 'No'],
        hasValue(rules.pt_employees_entitled_to_contracted_topup) && ['Part-time contracted-hours top-up', rules.pt_employees_entitled_to_contracted_topup ? 'Included' : 'Not included'],
        hasValue(rules.ft_employees_entitled_to_contracted_topup) && ['Full-time contracted-hours top-up', rules.ft_employees_entitled_to_contracted_topup ? 'Included' : 'Not included'],
    ].filter(Boolean);

    return (
        <section className="rules-panel" aria-label="Pay rules that apply">
            <div className="rules-heading">
                <div>
                    <p className="section-kicker">How your pay is worked out</p>
                    <h3>{worker} rules <span>{employment}</span></h3>
                </div>
                <span className="rules-badge">Current award settings</span>
            </div>

            <div className="rule-grid">
                <div className="rule-row"><span>Span of hours</span><strong>{rules.span_hours?.threshold === 'N/A' ? 'Not applicable' : formatOvertime(rules.span_hours)}</strong></div>
                <div className="rule-row"><span>Daily overtime</span><strong>{formatOvertime(rules.daily_overtime)}</strong></div>
                <div className="rule-row"><span>Fortnightly overtime</span><strong>{formatOvertime(rules.weekly_overtime)}</strong></div>
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
                                <b>{penalty.rate}</b>
                            </div>
                        ))}
                    </div>
                ) : <p className="no-penalties">No weekday penalty loadings are configured for this worker type.</p>}
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
        </section>
    );
}
