import React, { useEffect } from 'react';
import { usePay } from '../../context/PayContext';
import { api } from '../../services/apis';

const parseTimeValue = (value) => {
    if (value === '' || value === null || value === undefined) {
        return null;
    }

    // A trailing "n" is the UI's explicit marker for a next-day time.
    if (value.toString().endsWith('n')) {
        const hour = Number.parseInt(value, 10);
        return Number.isNaN(hour) || hour < 0 || hour > 23
            ? null
            : hour + 24;
    }

    const hour = Number.parseInt(value, 10);
    return Number.isNaN(hour) || hour < 0 || hour > 30 ? null : hour;
};

export function ShiftCalculator({ children }) {
    const { state, dispatch } = usePay();

    useEffect(() => {
        const controller = new AbortController();
        let isCurrent = true;

        const calculateShifts = async () => {
            const validShifts = state.shifts.filter(shift => {
                const hasStart = shift.start !== '' && shift.start !== null && shift.start !== undefined;
                const hasEnd = shift.end !== '' && shift.end !== null && shift.end !== undefined;
                return hasStart && hasEnd;
            });

            if (!state.config.hourlyRate || validShifts.length === 0) {
                return;
            }

            try {
                const payload = {
                    hourly_rate: parseFloat(state.config.hourlyRate),
                    worker_type: state.config.workerType,
                    award: state.config.award,
                    rule_configuration: state.config.ruleConfiguration,
                    employment_type: state.config.employmentType,
                    contracted_hours: state.config.contractedHours,
                    public_holidays: state.publicHolidays,
                    shifts: validShifts.map(shift => ({
                        week: shift.week || 1,
                        day: shift.day,
                        start: parseTimeValue(shift.start),
                        end: parseTimeValue(shift.end),
                        break_duration: parseFloat(shift.break_duration) || 0,
                        manual_overtime: Boolean(shift.manual_overtime),
                        manual_ordinary: Boolean(shift.manual_ordinary),
                    }))
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
