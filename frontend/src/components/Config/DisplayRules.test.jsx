import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DisplayRules } from './DisplayRules';

let payContext;

vi.mock('../../context/PayContext', () => ({
    usePay: () => payContext,
}));

describe('DisplayRules', () => {
    it('shows configured penalties, readable additional rules, and keeps the complete configuration collapsed', () => {
        payContext = {
            state: {
                config: { workerType: 'shift' },
                calculations: {
                    appliedRules: {
                        span_hours: { threshold: 'N/A' },
                        daily_overtime: { threshold: 8 },
                        weekly_overtime: { threshold: 38, basis: 'weekly' },
                        saturday_rules: { ordinary_loading: 0.25 },
                        sunday_rules: { ordinary_loading: 0.5 },
                        penalties: {
                            night_hours: {
                                type: 'time_based',
                                start: 23,
                                end: 6,
                                rate: 0.25,
                                description: 'Night work',
                                applies_to: ['shift'],
                            },
                        },
                        configuration: {
                            shift: {
                                default_break_hours: 0.5,
                                minimum_paid_shift_hours: {
                                    variation: 'employment_type',
                                    part_time: 3,
                                    casual: 3,
                                },
                            },
                            ordinary_time: { daily: { shift: 8 } },
                            pay_rates: {
                                overtime: {
                                    weekday: { multiplier: 1.5, casual: 1.75 },
                                },
                            },
                            penalties: {
                                night_hours: {
                                    type: 'time_based',
                                    rate: 0.25,
                                    description: 'Night work',
                                    applies_to: ['shift'],
                                },
                            },
                        },
                    },
                },
            },
        };

        render(<DisplayRules showRules />);

        expect(screen.getByText('Night work')).toBeInTheDocument();
        expect(screen.getAllByText('25% loading')).toHaveLength(2);
        expect(screen.getByText('50% loading')).toBeInTheDocument();
        expect(screen.getByText('Default unpaid break')).toBeInTheDocument();
        expect(screen.getByText('Minimum paid shift')).toBeInTheDocument();
        expect(screen.getByText('Weekday overtime')).toBeInTheDocument();
        expect(screen.getByText('Complete configuration')).toBeInTheDocument();
        expect(screen.getByText(/default_break_hours/)).toBeInTheDocument();
        expect(document.querySelector('.full-rule-config').open).toBe(false);
    });
});
