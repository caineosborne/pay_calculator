import React from 'react';
import { act, render } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ShiftCalculator } from './ShiftCalculator';

let payContext;

vi.mock('../../context/PayContext', () => ({
    usePay: () => payContext,
}));

const stateForRate = (hourlyRate) => ({
    config: {
        hourlyRate,
        workerType: 'shift',
        award: 'fast_food',
        ruleConfiguration: 'builtin:fast_food',
        employmentType: 'casual',
        contractedHours: null,
    },
    shifts: [
        {
            week: 1,
            day: 'Monday',
            start: 9,
            end: 17,
            break_duration: 0,
        },
    ],
    calculationRevision: 0,
});

const responseForPay = (totalPay) => ({
    ok: true,
    json: async () => ({
        ordinary_hours: 8,
        overtime_hours: 0,
        topup_hours: 0,
        total_hours: 8,
        ordinary_pay: totalPay,
        overtime_pay: 0,
        topup_pay: 0,
        penalty_pay: 0,
        total_pay: totalPay,
        daily_breakdown: {},
        applied_rules: {},
    }),
});

describe('ShiftCalculator', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        vi.stubGlobal('fetch', vi.fn());
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.unstubAllGlobals();
    });

    it('only applies the newest calculation response', async () => {
        const dispatch = vi.fn();
        const pendingResponses = [];
        fetch.mockImplementation(
            () =>
                new Promise((resolve) => {
                    pendingResponses.push(resolve);
                })
        );
        payContext = { state: stateForRate(20), dispatch };

        const { rerender } = render(
            <ShiftCalculator>
                <div>Calculator</div>
            </ShiftCalculator>
        );
        await act(async () => {
            await vi.advanceTimersByTimeAsync(150);
        });
        expect(fetch).toHaveBeenCalledTimes(1);

        payContext = { state: stateForRate(30), dispatch };
        rerender(
            <ShiftCalculator>
                <div>Calculator</div>
            </ShiftCalculator>
        );
        await act(async () => {
            await vi.advanceTimersByTimeAsync(150);
        });
        expect(fetch).toHaveBeenCalledTimes(2);

        await act(async () => {
            pendingResponses[1](responseForPay(240));
            await Promise.resolve();
        });
        expect(dispatch).toHaveBeenCalledTimes(1);
        expect(
            dispatch.mock.calls[0][0].payload.payments.totalPay
        ).toBe('240.00');

        await act(async () => {
            pendingResponses[0](responseForPay(160));
            await Promise.resolve();
        });
        expect(dispatch).toHaveBeenCalledTimes(1);
    });

    it('recalculates when a saved configuration refreshes the revision', async () => {
        const dispatch = vi.fn();
        fetch.mockResolvedValue(responseForPay(160));
        payContext = { state: stateForRate(20), dispatch };

        const { rerender } = render(
            <ShiftCalculator>
                <div>Calculator</div>
            </ShiftCalculator>
        );
        await act(async () => {
            await vi.advanceTimersByTimeAsync(150);
        });
        expect(fetch).toHaveBeenCalledTimes(1);

        payContext = {
            state: { ...stateForRate(20), calculationRevision: 1 },
            dispatch,
        };
        rerender(
            <ShiftCalculator>
                <div>Calculator</div>
            </ShiftCalculator>
        );
        await act(async () => {
            await vi.advanceTimersByTimeAsync(150);
        });

        expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('sends the worked periods around a manually specified lunch', async () => {
        const dispatch = vi.fn();
        fetch.mockResolvedValue(responseForPay(160));
        payContext = {
            state: {
                ...stateForRate(20),
                shifts: [{
                    week: 1,
                    day: 'Monday',
                    start: 9,
                    end: 17,
                    break_duration: 0.5,
                    lunch_start: '12:00',
                }],
            },
            dispatch,
        };

        render(<ShiftCalculator><div>Calculator</div></ShiftCalculator>);
        await act(async () => {
            await vi.advanceTimersByTimeAsync(150);
        });

        const payload = JSON.parse(fetch.mock.calls[0][1].body);
        expect(payload.shifts).toEqual([
            expect.objectContaining({ start: 9, end: 12, break_duration: 0, minimum_engagement_exempt: true }),
            expect.objectContaining({ start: 12.5, end: 17, break_duration: 0, minimum_engagement_exempt: true }),
        ]);
    });

    it('sends public holiday status with each attendance segment', async () => {
        const dispatch = vi.fn();
        fetch.mockResolvedValue(responseForPay(160));
        payContext = {
            state: {
                ...stateForRate(20),
                shifts: [{
                    week: 1,
                    day: 'Monday',
                    start: 9,
                    end: 17,
                    break_duration: 0,
                    public_holiday: true,
                }],
            },
            dispatch,
        };

        render(<ShiftCalculator><div>Calculator</div></ShiftCalculator>);
        await act(async () => {
            await vi.advanceTimersByTimeAsync(150);
        });

        const payload = JSON.parse(fetch.mock.calls[0][1].body);
        expect(payload.shifts).toEqual([
            expect.objectContaining({ public_holiday: true }),
        ]);
    });
});
