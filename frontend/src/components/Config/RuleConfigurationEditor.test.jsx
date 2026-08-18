import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../services/apis';
import { RuleConfigurationEditor } from './RuleConfigurationEditor';
import { QUESTIONNAIRE_SECTIONS } from './ruleQuestionnaire';

const record = (answer) => ({
    answer,
    status: 'derived',
    source_ruleset_keys: [],
    source_rule_ids: [],
    clause_references: [],
    reasoning_summary: 'Loaded from Python.',
    special_case_notes: [],
});

const buildQuestionnaire = () => {
    const questionnaire = {};
    for (const section of QUESTIONNAIRE_SECTIONS) {
        questionnaire[section.key] = {};
        for (const [field, _label, type] of section.fields) {
            let answer = type === 'boolean' ? false : type === 'days' ? [] : 1;
            if (type === 'weekend') {
                answer = 'not_applicable';
            }
            if (type === 'penalties') {
                answer = [];
            }
            if (type === 'overtime_limits') {
                answer = { variation: 'default', default: 8 };
            }
            questionnaire[section.key][field] = record(answer);
        }
    }
    return questionnaire;
};

const configuration = () => ({
    id: 'builtin:fast_food',
    name: 'Fast Food Industry Award',
    base_award: 'fast_food',
    class_name: 'FastFoodAward2026Rules',
    kind: 'builtin',
    source: 'class FastFoodAward2026Rules:\n    VALUE = 1\n',
    questionnaire: buildQuestionnaire(),
    structural_issues: [],
    advanced_attributes: ['VALUE'],
});

const configurationWithSpanOvertime = () => {
    const configured = configuration();
    configured.questionnaire.span_overtime.applies.answer = true;
    configured.questionnaire.span_overtime.before_cutoff_hour.answer = 8.5;
    configured.questionnaire.span_overtime.cutoff_hour.answer = 18.5;
    return configured;
};

const configurationWithWeekdayPenaltyWindow = () => {
    const configured = configuration();
    configured.questionnaire.weekday_penalties.time_based_penalties.answer = [
        {
            code_name: 'late_night',
            type: 'time_based',
            basis: 'time',
            start_hour: 22,
            end_hour: 24,
            finish_start_hour: null,
            finish_end_hour: null,
            rate: 0.15,
            description: 'Late-night loading',
            applies_to: ['day'],
            extra: {},
        },
    ];
    return configured;
};

describe('RuleConfigurationEditor', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        vi.spyOn(api, 'getRuleConfiguration').mockResolvedValue(configuration());
        vi.spyOn(api, 'validateRuleConfiguration').mockImplementation(
            async (_award, source, questionnaire) => ({
                valid: true,
                source,
                questionnaire: questionnaire || buildQuestionnaire(),
                structural_issues: [],
            })
        );
        vi.spyOn(api, 'createRuleConfiguration').mockImplementation(
            async (_award, _name, source, questionnaire) => ({
                ...configuration(),
                id: 'custom:fast_food:reviewed',
                kind: 'custom',
                source,
                questionnaire: questionnaire || buildQuestionnaire(),
            })
        );
    });

    it('keeps guided edits in the temporary editor', async () => {
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                onConfigurationSaved={vi.fn()}
            />
        );
        const field = await screen.findByLabelText('Standard overtime rate');
        fireEvent.change(field, { target: { value: '9' } });
        expect(screen.getByText('Unsaved changes')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Discard changes' }));
        expect(field).toHaveValue(1);
    });

    it('does not expose raw Python editing', async () => {
        const refreshed = buildQuestionnaire();
        refreshed.overtime.standard_overtime_rate.answer = 1.7;
        api.validateRuleConfiguration.mockResolvedValueOnce({
            valid: true,
            source: 'class FastFoodAward2026Rules:\n    VALUE = 7\n',
            questionnaire: refreshed,
            structural_issues: [],
        });
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                onConfigurationSaved={vi.fn()}
            />
        );
        expect(screen.queryByLabelText('Rule class source')).not.toBeInTheDocument();
        expect(screen.queryByText('Advanced Python')).not.toBeInTheDocument();
    });

    it('shows the guided editor without an advanced mode toggle', async () => {
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                onConfigurationSaved={vi.fn()}
            />
        );
        expect(await screen.findByText('Employment settings')).toBeInTheDocument();
        expect(screen.queryByRole('checkbox', { name: 'Review Helper' })).not.toBeInTheDocument();
    });

    it('shows long-day controls in the guided editor', async () => {
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                onConfigurationSaved={vi.fn()}
            />
        );
        expect(await screen.findByText('Long-day exception')).toBeInTheDocument();
        expect(screen.getByLabelText('Allow a long-day exception?')).toBeInTheDocument();
        expect(screen.getByLabelText('Long-day exceptions per week')).toBeDisabled();
    });

    it('supports repeatable penalty rows', async () => {
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                onConfigurationSaved={vi.fn()}
            />
        );
        const section = (await screen.findByText('Weekday Penalties')).closest(
            'section'
        );
        const addButtons = within(section).getAllByRole('button', {
            name: 'Add row',
        });
        fireEvent.click(addButtons[0]);
        expect(
            within(section).getByLabelText('Whole-shift penalty loadings (based on start or end time) code 1')
        ).toHaveValue('shift_based_loading_1');
        fireEvent.change(
            within(section).getByLabelText(
                'Whole-shift penalty loadings (based on start or end time) code 1'
            ),
            { target: { value: 'custom_loading' } }
        );
        expect(
            within(section).getByLabelText(
                'Whole-shift penalty loadings (based on start or end time) code 1'
            )
        ).toHaveValue('custom_loading');
        const condition = within(section).getByLabelText(
            'Whole-shift penalty loadings (based on start or end time) condition 1'
        );
        expect(condition).toHaveTextContent('Shift start and end both match');
        fireEvent.change(condition, { target: { value: 'start_and_end' } });
        expect(
            within(section).getByLabelText(
                'Whole-shift penalty loadings (based on start or end time) finish start 1'
            )
        ).toBeInTheDocument();
        expect(
            within(section).getByLabelText(
                'Whole-shift penalty loadings (based on start or end time) finish end 1'
            )
        ).toBeInTheDocument();
        fireEvent.click(within(section).getByRole('button', { name: 'Remove' }));
        expect(
            within(section).queryByLabelText('Whole-shift penalty loadings (based on start or end time) code 1')
        ).not.toBeInTheDocument();
    });

    it('shows field-level structural validation errors', async () => {
        api.validateRuleConfiguration.mockResolvedValueOnce({
            valid: false,
            source: configuration().source,
            questionnaire: buildQuestionnaire(),
            structural_issues: [
                {
                    severity: 'error',
                    field_path: 'overtime.standard_overtime_rate',
                    message: 'A numeric value is required.',
                },
            ],
        });
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                onConfigurationSaved={vi.fn()}
            />
        );
        fireEvent.change(
            await screen.findByLabelText('Standard overtime rate'),
            { target: { value: '' } }
        );
        fireEvent.click(screen.getByRole('button', { name: 'Validate' }));
        const matchingErrors = await screen.findAllByText(
            'A numeric value is required.'
        );
        expect(matchingErrors).toHaveLength(2);
        expect(
            screen.getByText(
                'Fix the highlighted structural errors before saving.'
            )
        ).toBeInTheDocument();

        const summary = screen.getByLabelText('Validation issues');
        expect(
            within(summary).getByText('Fix these issues before saving')
        ).toBeInTheDocument();
        const summaryLink = within(summary).getByRole('button', {
            name: /Standard overtime rate: A numeric value is required\./,
        });
        fireEvent.click(summaryLink);
        expect(document.activeElement).toBe(
            screen.getByLabelText('Standard overtime rate')
        );
    });

    it('uses clock times for span overtime and preserves decimal hours for saving', async () => {
        api.getRuleConfiguration.mockResolvedValueOnce(
            configurationWithSpanOvertime()
        );
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                onConfigurationSaved={vi.fn()}
            />
        );
        const beforeTime = await screen.findByLabelText(
            'Overtime applies before (24-hour time)'
        );
        const endTime = screen.getByLabelText(
            'Ordinary time ends (24-hour time)'
        );
        expect(beforeTime).toHaveValue('08:30');
        expect(endTime).toHaveValue('18:30');

        fireEvent.change(beforeTime, { target: { value: '09:15' } });
        fireEvent.change(endTime, { target: { value: '24:00' } });
        expect(beforeTime).toHaveValue('09:15');
        expect(endTime).toHaveValue('24:00');
        fireEvent.click(screen.getByRole('button', { name: 'Validate' }));

        await waitFor(() => {
            const [, , questionnaire] =
                api.validateRuleConfiguration.mock.calls.at(-1);
            expect(
                questionnaire.span_overtime.before_cutoff_hour.answer
            ).toBe(9.25);
            expect(questionnaire.span_overtime.cutoff_hour.answer).toBe(24);
        });
    });

    it('uses clock times for weekday penalty windows and preserves decimal hours', async () => {
        api.getRuleConfiguration.mockResolvedValueOnce(
            configurationWithWeekdayPenaltyWindow()
        );
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                onConfigurationSaved={vi.fn()}
            />
        );
        const start = await screen.findByLabelText(
            'Time-based penalty loadings (for specific work times) start 1'
        );
        const end = screen.getByLabelText('Time-based penalty loadings (for specific work times) end 1');
        expect(start).toHaveValue('22:00');
        expect(end).toHaveValue('24:00');

        fireEvent.change(start, { target: { value: '21:30' } });
        fireEvent.click(screen.getByRole('button', { name: 'Validate' }));

        await waitFor(() => {
            const [, , questionnaire] =
                api.validateRuleConfiguration.mock.calls.at(-1);
            expect(
                questionnaire.weekday_penalties.time_based_penalties.answer[0]
                    .start_hour
            ).toBe(21.5);
        });
    });

    it('validates before saving and brings save errors to the top summary', async () => {
        api.validateRuleConfiguration.mockResolvedValueOnce({
            valid: false,
            source: configuration().source,
            questionnaire: buildQuestionnaire(),
            structural_issues: [
                {
                    severity: 'error',
                    field_path: 'overtime.daily_overtime_configuration.default',
                    message: 'Enter a limit greater than zero.',
                },
            ],
        });
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                allowSaving
                onConfigurationSaved={vi.fn()}
            />
        );
        fireEvent.change(
            await screen.findByLabelText('Standard overtime rate'),
            { target: { value: '9' } }
        );
        fireEvent.click(
            screen.getByRole('button', { name: 'Create private copy' })
        );

        const summary = await screen.findByLabelText('Validation issues');
        expect(
            within(summary).getByText('Enter a limit greater than zero.')
        ).toBeInTheDocument();
        expect(api.createRuleConfiguration).not.toHaveBeenCalled();
        await waitFor(() => expect(document.activeElement).toBe(summary));
    });

    it('keeps guided edits temporary and exposes no save action', async () => {
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
            />
        );
        fireEvent.change(
            await screen.findByLabelText('Standard overtime rate'),
            { target: { value: '9' } }
        );
        expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument();
        expect(screen.getByText(/never saved/i)).toBeInTheDocument();
        expect(api.createRuleConfiguration).not.toHaveBeenCalled();
    });

    it('allows Customize to save a private-copy-ready configuration', async () => {
        const onConfigurationSaved = vi.fn();
        render(
            <RuleConfigurationEditor
                configurationId="builtin:fast_food"
                allowSaving
                onConfigurationSaved={onConfigurationSaved}
            />
        );
        fireEvent.change(
            await screen.findByLabelText('Standard overtime rate'),
            { target: { value: '9' } }
        );
        fireEvent.click(screen.getByRole('button', { name: 'Create private copy' }));
        await waitFor(() => expect(api.createRuleConfiguration).toHaveBeenCalled());
        await waitFor(() => expect(onConfigurationSaved).toHaveBeenCalled());
    });

    it('ignores a stale configuration response after the selection changes', async () => {
        const pending = {};
        api.getRuleConfiguration.mockImplementation(
            (id) =>
                new Promise((resolve) => {
                    pending[id] = resolve;
                })
        );
        const { rerender } = render(
            <RuleConfigurationEditor
                configurationId="custom:fast_food:first"
                onConfigurationSaved={vi.fn()}
            />
        );
        await waitFor(() =>
            expect(pending['custom:fast_food:first']).toBeTypeOf('function')
        );

        rerender(
            <RuleConfigurationEditor
                configurationId="custom:fast_food:second"
                onConfigurationSaved={vi.fn()}
            />
        );
        await waitFor(() =>
            expect(pending['custom:fast_food:second']).toBeTypeOf('function')
        );

        pending['custom:fast_food:second']({
            ...configuration(),
            id: 'custom:fast_food:second',
            kind: 'custom',
            source: 'class FastFoodAward2026Rules:\n    VALUE = 2\n',
        });
        expect(await screen.findByText('Pay rules')).toBeInTheDocument();

        pending['custom:fast_food:first']({
            ...configuration(),
            id: 'custom:fast_food:first',
            kind: 'custom',
            source: 'class FastFoodAward2026Rules:\n    VALUE = 1\n',
        });
        await waitFor(() =>
            expect(screen.getByText('Pay rules')).toBeInTheDocument()
        );
    });
});
