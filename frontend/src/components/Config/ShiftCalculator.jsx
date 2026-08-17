import React, { useEffect } from 'react';
import { usePay } from '../../context/PayContext';
import { api } from '../../services/apis';

const parseTimeValue = (value) => {
    if (value === '' || value === null || value === undefined) {
        return null;
    }

    const match = /^(\d{1,2}):(\d{2})$/.exec(value.toString().trim());
    const numericValue = value.toString().trim();
    const inputHours = match ? Number.parseInt(match[1], 10) : null;
    const inputMinutes = match ? Number.parseInt(match[2], 10) : null;
    const time = match && inputHours <= 23 && inputMinutes <= 59
        ? inputHours + (inputMinutes / 60)
        : /^\d+(?:\.\d+)?$/.test(numericValue)
            ? Number.parseFloat(numericValue)
            : Number.NaN;
    return Number.isNaN(time) || time < 0 || time > 47 ? null : time;
};

const asCalculationPeriods = (shift) => {
    const start = parseTimeValue(shift.start);
    const enteredEnd = parseTimeValue(shift.end);
    const lunch = parseTimeValue(shift.lunch_start);
    const breakDuration = parseFloat(shift.break_duration) || 0;
    const end = enteredEnd > start ? enteredEnd : enteredEnd + 24;
    const baseShift = {
        week: shift.week || 1,
        day: shift.day,
        start,
        end,
        manual_overtime: Boolean(shift.manual_overtime),
        manual_ordinary: Boolean(shift.manual_ordinary),
        public_holiday: Boolean(shift.public_holiday),
    };

    // An entered lunch time is optional. When it falls inside the shift, send
    // the actual worked periods around it. This lets the existing calculator
    // apply time-sensitive rules without changing allocation behaviour for
    // shifts where lunch timing does not matter.
    const lunchStart = lunch !== null && lunch < start ? lunch + 24 : lunch;
    const lunchEnd = lunchStart === null ? null : lunchStart + breakDuration;
    if (
        breakDuration > 0 &&
        lunchStart !== null &&
        lunchStart >= start &&
        lunchEnd <= end
    ) {
        return [
            {
                ...baseShift,
                end: lunchStart,
                break_duration: 0,
                minimum_engagement_exempt: true,
            },
            {
                ...baseShift,
                start: lunchEnd,
                break_duration: 0,
                minimum_engagement_exempt: true,
            },
        ];
    }

    return [{ ...baseShift, break_duration: breakDuration }];
};

export function ShiftCalculator({ children }) {
    const { state, dispatch } = usePay();

    useEffect(() => {
        const controller = new AbortController();
        let isCurrent = true;

        const calculateShifts = async () => {
            const validShifts = state.shifts.filter(shift => {
                return parseTimeValue(shift.start) !== null && parseTimeValue(shift.end) !== null;
            });

            if (!state.config.hourlyRate || validShifts.length === 0) {
                return;
            }

            try {
                const payload = {
                    hourly_rate: parseFloat(state.config.hourlyRate),
                    worker_type: state.config.workerType,
                    award: state.config.award,
                    // Public award tabs always calculate against the matching
                    // built-in rules. A stale custom identifier must not leak
                    // into a public calculator request.
                    rule_configuration: `builtin:${state.config.award}`,
                    employment_type: state.config.employmentType,
                    contracted_hours: state.config.contractedHours,
                    public_holidays: state.publicHolidays,
                    shifts: validShifts.flatMap(asCalculationPeriods)
                };

                const data = await api.calculatePay(payload, {
                    signal: controller.signal,
                });
                // Some test or browser fetch implementations do not honour
                // AbortController, so also guard the state update explicitly.
                if (!isCurrent) {
                    return;
                }

                const formattedDailyBreakdown = {};
                Object.entries(data.daily_breakdown || {}).forEach(([day, values]) => {
                    formattedDailyBreakdown[day] = {
                        hours: {
                            ordinary: Number(values.ordinary || 0).toFixed(2),
                            overtime: Number(values.overtime || 0).toFixed(2),
                            topup: Number(values.topup || 0).toFixed(2),  // Add topup hours
                            total: Number(values.total || 0).toFixed(2)
                        },
                        pay: {
                            ordinary: Number(values.ordinary_pay || 0).toFixed(2),
                            overtime: Number(values.overtime_pay || 0).toFixed(2),
                            penalty: Number(values.penalty_pay || 0).toFixed(2),
                            topup: Number(values.topup_pay || 0).toFixed(2),
                            total: Number(values.pay || 0).toFixed(2)
                        },
                        applied_rules: values.applied_rules || []
                    };
                });

                dispatch({
                    type: 'UPDATE_CALCULATIONS',
                    payload: {
                        calculations: {
                            ordinaryHours: Number(data.ordinary_hours || 0).toFixed(2),
                            overtimeHours: Number(data.overtime_hours || 0).toFixed(2),
                            topupHours: Number(data.topup_hours || 0).toFixed(2),
                            totalHours: Number(data.total_hours || 0).toFixed(2),
                            timeBasedPenaltyHours: Number(data.time_based_penalty_hours || 0).toFixed(2),
                            dailyBreakdown: formattedDailyBreakdown,
                            appliedRules: data.applied_rules
                        },
                        payments: {
                            ordinaryPay: Number(data.ordinary_pay || 0).toFixed(2),
                            overtimePay: Number(data.overtime_pay || 0).toFixed(2),
                            topupPay: Number(data.topup_pay || 0).toFixed(2),
                            penaltyPay: Number(data.penalty_pay || 0).toFixed(2),
                            totalPay: Number(data.total_pay || 0).toFixed(2)
                        }
                    }
                });
            } catch (error) {
                if (error.name === 'AbortError') {
                    return;
                }
                console.error('Calculation error:', error);
                if (isCurrent) {
                    dispatch({
                        type: 'SET_CALCULATION_ERROR',
                        payload: error.message || 'Unable to calculate these shifts.',
                    });
                }
            }
        };

        // Coalesce rapid input changes, then cancel this request if any input
        // changes again before the response is applied.
        const calculationTimer = window.setTimeout(calculateShifts, 150);
        return () => {
            isCurrent = false;
            window.clearTimeout(calculationTimer);
            controller.abort();
        };
    }, [
        state.shifts,
        state.publicHolidays,
        state.config.hourlyRate,
        state.config.workerType,
        state.config.award,
        state.config.ruleConfiguration,
        state.config.employmentType,
        state.config.contractedHours,
        state.calculationRevision,
        dispatch
    ]);

    return <>{children}</>;
}
