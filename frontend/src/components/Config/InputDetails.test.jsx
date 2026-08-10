import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InputDetails } from './InputDetails';

let payContext;

vi.mock('../../context/PayContext', () => ({
    usePay: () => payContext,
}));

vi.mock('../../services/apis', () => ({
    api: {
        getAwards: vi.fn(),
        getRuleConfigurations: vi.fn(),
    },
}));

vi.mock('./DisplayRules', () => ({
    DisplayRules: () => null,
}));

vi.mock('./RuleConfigurationEditor', () => ({
    RuleConfigurationEditor: () => null,
}));

const baseState = (hourlyRate = 27.81) => ({
    config: {
        hourlyRate,
        workerType: 'shift',
        award: 'fast_food',
        ruleConfiguration: 'builtin:fast_food',
        employmentType: 'casual',
        contractedHours: null,
    },
    calculations: {},
});

describe('InputDetails Fast Food classifications', () => {
    beforeEach(async () => {
        const { api } = await import('../../services/apis');
        api.getAwards.mockResolvedValue([
            {
                key: 'fast_food',
                label: 'Fast Food Award',
                default: true,
                hourly_rate_options: [
                    { key: 'level_1', label: 'Level 1', hourly_rate: 27.81 },
                    { key: 'level_3_two_or_more', label: 'Level 3 — in charge of 2 or more persons', hourly_rate: 30.27 },
                ],
            },
        ]);
        api.getRuleConfigurations.mockResolvedValue([
            {
                id: 'builtin:fast_food',
                base_award: 'fast_food',
                kind: 'builtin',
                name: 'Fast Food Award',
            },
        ]);
        payContext = { state: baseState(), dispatch: vi.fn() };
    });

    it('sets the published hourly rate when a classification is selected', async () => {
        render(<InputDetails />);

        const classification = await screen.findByLabelText(
            'Classification and hourly rate'
        );
        payContext.dispatch.mockClear();
        fireEvent.change(classification, { target: { value: 'level_3_two_or_more' } });

        expect(payContext.dispatch).toHaveBeenCalledWith({
            type: 'UPDATE_HOURLY_RATE',
            payload: 30.27,
        });
    });

    it('shows an editable rate field when custom rate is selected', async () => {
        render(<InputDetails />);

        const classification = await screen.findByLabelText(
            'Classification and hourly rate'
        );
        fireEvent.change(classification, { target: { value: 'custom' } });

        const rate = screen.getByLabelText('Your hourly rate ($)');
        fireEvent.change(rate, { target: { value: '31.25' } });

        await waitFor(() => {
            expect(payContext.dispatch).toHaveBeenCalledWith({
                type: 'UPDATE_HOURLY_RATE',
                payload: 31.25,
            });
        });
    });
});
