import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Header from './Header';

let payContext;

vi.mock('../../context/PayContext', () => ({
    usePay: () => payContext,
}));

describe('Header', () => {
    afterEach(() => vi.restoreAllMocks());

    it('copies structured calculation details', async () => {
        const writeText = vi.fn().mockResolvedValue();
        Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            value: { writeText },
        });
        payContext = {
            state: {
                shifts: [{
                    week: 1,
                    day: 'Monday',
                    start: '22',
                    end: '3',
                    lunch_start: '00:30',
                    break_duration: '0.5',
                    manual_overtime: true,
                }],
                publicHolidays: [{ week: 1, day: 'Monday' }],
                calculations: {
                    dailyBreakdown: {
                        'Week 1 - Monday': {
                            pay: { total: '180.00' },
                            applied_rules: ['Span Overtime'],
                        },
                    },
                },
            },
            dispatch: vi.fn(),
        };

        render(<Header />);
        fireEvent.click(screen.getByRole('button', { name: 'Copy calculation details' }));

        await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
        expect(JSON.parse(writeText.mock.calls[0][0])).toEqual([{
            dayOfWeek: 'Week 1 - Monday',
            startTime: '22:00',
            endTime: '03:00',
            lunchTime: '00:30',
            lunchLengthHours: 0.5,
            flags: ['Manual overtime', 'Public holiday'],
            amount: '$180.00',
            appliedRules: ['Span Overtime'],
        }]);
        expect(screen.getByRole('button', { name: 'Calculation details copied' })).toBeInTheDocument();
    });

    it('opens the limitations notice from the header', () => {
        const onOpenLimitations = vi.fn();
        payContext = {
            state: {
                shifts: [],
                publicHolidays: [],
                calculations: {},
            },
            dispatch: vi.fn(),
        };

        render(<Header onOpenLimitations={onOpenLimitations} />);
        expect(screen.getByRole('heading', { name: 'payguide.au' })).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Assumptions & limitations' }));

        expect(onOpenLimitations).toHaveBeenCalledTimes(1);
    });
});
