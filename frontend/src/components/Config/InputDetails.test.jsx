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

    it('changes every shift break when the worker type changes', async () => {
        payContext.state = {
            ...baseState(),
            shifts: [
                { id: 'monday', break_duration: '0.5' },
                { id: 'tuesday', break_duration: '0.5' },
            ],
        };
        render(<InputDetails />);

        fireEvent.click(await screen.findByRole('button', { name: 'Shift Worker' }));

        expect(payContext.dispatch).toHaveBeenCalledWith({
            type: 'UPDATE_SHIFTS',
            payload: [
                expect.objectContaining({ break_duration: '0' }),
                expect.objectContaining({ break_duration: '0' }),
            ],
        });
    });

    it('keeps the ruleset-specific edit action and confirms before closing dirty edits', async () => {
        payContext.state = {
            ...baseState(),
            view: 'customize',
            ruleEditorDirty: true,
        };
        const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
        render(<InputDetails />);

        await screen.findByLabelText('Rule Configuration');
        expect(screen.queryByRole('button', { name: 'Edit' })).not.toBeInTheDocument();

        fireEvent.click(
            screen.getByRole('button', { name: 'Edit rule configuration' })
        );
        fireEvent.click(screen.getByRole('button', { name: 'Close editor' }));

        expect(confirm).toHaveBeenCalledWith('Discard unsaved rule changes?');
        expect(
            screen.getByRole('button', { name: 'Close editor' })
        ).toBeInTheDocument();
    });
});
