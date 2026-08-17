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
        expect(screen.getByText('Unsaved guided edits')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Discard' }));
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
            within(section).getByLabelText('Whole-shift penalty loadings code 1')
        ).toHaveValue('shift_based_loading_1');
        fireEvent.change(
            within(section).getByLabelText(
                'Whole-shift penalty loadings code 1'
            ),
            { target: { value: 'custom_loading' } }
        );
        expect(
            within(section).getByLabelText(
                'Whole-shift penalty loadings code 1'
            )
        ).toHaveValue('custom_loading');
        const condition = within(section).getByLabelText(
            'Whole-shift penalty loadings condition 1'
        );
        expect(condition).toHaveTextContent('Shift start and end both match');
        fireEvent.change(condition, { target: { value: 'start_and_end' } });
        expect(
            within(section).getByLabelText(
                'Whole-shift penalty loadings finish start 1'
            )
        ).toBeInTheDocument();
        expect(
            within(section).getByLabelText(
                'Whole-shift penalty loadings finish end 1'
            )
        ).toBeInTheDocument();
        fireEvent.click(within(section).getByRole('button', { name: 'Remove' }));
        expect(
            within(section).queryByLabelText('Whole-shift penalty loadings code 1')
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
        expect(
            await screen.findByText('A numeric value is required.')
        ).toBeInTheDocument();
        expect(
            screen.getByText(
                'Fix the highlighted structural errors before saving.'
            )
        ).toBeInTheDocument();
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
