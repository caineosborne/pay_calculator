import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DisplayRules } from './DisplayRules';

let payContext;

vi.mock('../../context/PayContext', () => ({
    usePay: () => payContext,
}));

describe('DisplayRules', () => {
    it('groups and filters rules for the selected day-worker type', () => {
        payContext = {
            state: {
                config: { workerType: 'day' },
                calculations: {
                    appliedRules: {
                        contracted_hours: 24,
                        span_hours: { threshold: 'N/A' },
                        daily_overtime: { threshold: 8 },
                        weekly_overtime: {
                            threshold: 38,
                            basis: 'weekly',
                            max_work_days: 5,
                            max_work_days_basis: 'weekly',
                        },
                        gap_penalty: { threshold: 'Less than 12 hours between shifts' },
                        use_contracted_hours_for_overtime: true,
                        pt_employees_entitled_to_contracted_topup: true,
                        ft_employees_entitled_to_contracted_topup: false,
                        configuration: {
                            shift: {
                                default_break_hours: 0.5,
                                minimum_paid_shift_hours: {
                                    variation: 'employment_type',
                                    full_time: 0,
                                    part_time: 3,
                                    casual: 3,
                                },
                            },
                            ordinary_time: {
                                daily: { day: 8, shift: 8 },
                                ordinary_rates: { casual_loading: 0.25 },
                                long_day: { ordinary_limit_hours: 11, uses_per_week: 1 },
                                span_overtime: {
                                    day: {
                                        default: { start: 7, end: 23, enabled: true },
                                        Sunday: { start: 9, end: 23, enabled: true },
                                    },
                                    shift: {
                                        default: { start: 18, end: 6, enabled: true },
                                    },
                                },
                            },
                            pay_rates: {
                                overtime: {
                                    weekday: { multiplier: 1.5, casual: 1.75 },
                                },
                            },
                            gap_between_shifts: {
                                minimum_hours: 12,
                                loading: 1,
                                casual_rate: 1,
                            },
                            day_treatment: {
                                Saturday: {
                                    day: { ordinary_loading: 0.25, casual_rate: 0.5 },
                                    shift: { ordinary_loading: 0.5, casual_rate: 0.75 },
                                },
                                Sunday: {
                                    day: { ordinary_loading: 0.5, casual_rate: 0.75 },
                                    shift: { ordinary_loading: 0.75, casual_rate: 1 },
                                },
                                public_holiday: {
                                    day: { ordinary_loading: 1.25, casual_rate: 1.5 },
                                    shift: { ordinary_loading: 1.25, casual_rate: 1.5 },
                                },
                            },
                            penalties: {
                                night_hours: {
                                    type: 'time_based',
                                    rate: 0.25,
                                    description: 'Night work',
                                    applies_to: ['shift'],
                                },
                                late_hours: {
                                    type: 'time_based',
                                    rate: 0.1,
                                    description: 'Late work',
                                    applies_to: ['day'],
                                },
                            },
                        },
                    },
                },
            },
        };

        render(<DisplayRules showRules />);

        expect(screen.getByText('Late work')).toBeInTheDocument();
        expect(screen.queryByText('Night work')).not.toBeInTheDocument();
        expect(screen.getByText('Contracted hours')).toBeInTheDocument();
        expect(screen.getByText('Default unpaid break')).toBeInTheDocument();
        expect(screen.getByText('Minimum paid shift')).toBeInTheDocument();
        expect(screen.getByText('Full Time: N/A; Part Time: 3 hours; Casual: 3 hours')).toBeInTheDocument();
        expect(screen.getByText('Weekday overtime')).toBeInTheDocument();
        expect(screen.getByText('Overtime entitlements')).toBeInTheDocument();
        expect(screen.getByText('Penalty loadings')).toBeInTheDocument();
        expect(screen.getByText('Rates')).toBeInTheDocument();
        expect(screen.getByText('Other rules')).toBeInTheDocument();

        const mainRuleGrid = screen.getByText('Span of hours').closest('.rule-grid');
        const sundaySpan = screen.getByText('Sunday ordinary span');
        const dailyOvertime = screen.getByText('Daily overtime');
        const longDay = screen.getByText('Long-day ordinary-hours exception');
        const periodOvertime = screen.getByText('Period overtime');
        expect(sundaySpan.closest('.rule-grid')).toBe(mainRuleGrid);
        expect(sundaySpan.compareDocumentPosition(dailyOvertime) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
        expect(dailyOvertime.compareDocumentPosition(longDay) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
        expect(longDay.compareDocumentPosition(periodOvertime) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
        expect(screen.getAllByText('Span of hours')).toHaveLength(1);
        expect(screen.queryByText('Span overtime rate')).not.toBeInTheDocument();
        expect(screen.queryByText('Daily overtime rate')).not.toBeInTheDocument();
        expect(screen.queryByText('Period overtime rate')).not.toBeInTheDocument();

        for (const label of [
            'Saturday ordinary hours',
            'Sunday ordinary hours',
            'Public-holiday ordinary hours',
        ]) {
            const row = screen.getByText(label).closest('.penalty-row');
            expect(row.closest('.penalty-card')).toBeInTheDocument();
            expect(within(row).getByText('Day worker')).toBeInTheDocument();
            expect(within(row).queryByText(/loading/)).not.toBeInTheDocument();
        }
        const saturdayRate = screen.getByText('Saturday ordinary hours rate').closest('.rule-row');
        expect(within(saturdayRate).getByText(/25% loading/)).toBeInTheDocument();
        expect(screen.getByText('Short break between shifts')).toBeInTheDocument();
        expect(screen.getByText('Short-break penalty rate')).toBeInTheDocument();
        expect(screen.queryByText('Standard ordinary span (Shift workers)')).not.toBeInTheDocument();
        expect(screen.getByText('Complete configuration')).toBeInTheDocument();
        expect(screen.getByText(/Authoritative normalized settings/)).toBeInTheDocument();
        expect(screen.getByText(/default_break_hours/)).toBeInTheDocument();
        expect(document.querySelector('.full-rule-config').open).toBe(false);
    });

    it('shows shiftworker weekend treatments instead of day-worker treatments', () => {
        payContext = {
            state: {
                config: { workerType: 'shift' },
                calculations: {
                    appliedRules: {
                        span_hours: { threshold: 'N/A' },
                        daily_overtime: { threshold: 8 },
                        weekly_overtime: { threshold: 38, basis: 'weekly' },
                        configuration: {
                            day_treatment: {
                                Saturday: {
                                    day: { ordinary_loading: 0.25 },
                                    shift: { ordinary_loading: 0.5 },
                                },
                            },
                        },
                    },
                },
            },
        };

        render(<DisplayRules showRules />);

        const row = screen.getByText('Saturday ordinary hours').closest('.penalty-row');
        expect(within(row).getByText('Shift worker')).toBeInTheDocument();
        expect(within(row).queryByText(/loading/)).not.toBeInTheDocument();
        const rateRow = screen.getByText('Saturday ordinary hours rate').closest('.rule-row');
        expect(within(rateRow).getByText('50% loading')).toBeInTheDocument();
        expect(within(rateRow).queryByText('25% loading')).not.toBeInTheDocument();
    });
});
