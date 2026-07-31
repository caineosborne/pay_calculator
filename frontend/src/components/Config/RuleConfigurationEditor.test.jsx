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
    id: 'builtin:hospitality',
    name: 'Hospitality Award',
    base_award: 'hospitality',
    class_name: 'HospitalityRules',
    kind: 'builtin',
    source: 'class HospitalityRules:\n    VALUE = 1\n',
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
                id: 'custom:hospitality:reviewed',
                kind: 'custom',
                source,
                questionnaire: questionnaire || buildQuestionnaire(),
            })
        );
    });

    it('locks raw Python during guided edits and discard unlocks it', async () => {
        render(
            <RuleConfigurationEditor
                configurationId="builtin:hospitality"
                onConfigurationSaved={vi.fn()}
            />
        );
        const field = await screen.findByLabelText('Standard overtime rate');
        const source = screen.getByLabelText('Rule class source');

        fireEvent.change(field, { target: { value: '9' } });
        expect(source).toBeDisabled();
        expect(screen.getByText('Unsaved guided edits')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Discard' }));
        expect(source).not.toBeDisabled();
        expect(field).toHaveValue(1);
    });

    it('locks the questionnaire during raw edits and refreshes it after validation', async () => {
        const refreshed = buildQuestionnaire();
        refreshed.overtime.standard_overtime_rate.answer = 1.7;
        api.validateRuleConfiguration.mockResolvedValueOnce({
            valid: true,
            source: 'class HospitalityRules:\n    VALUE = 7\n',
            questionnaire: refreshed,
            structural_issues: [],
        });
        render(
            <RuleConfigurationEditor
                configurationId="builtin:hospitality"
                onConfigurationSaved={vi.fn()}
            />
        );
        const source = await screen.findByLabelText('Rule class source');
        fireEvent.change(source, {
            target: { value: 'class HospitalityRules:\n    VALUE = 7\n' },
        });
        expect(
                screen.getByLabelText('Standard overtime rate')
        ).toBeDisabled();

        fireEvent.click(screen.getByRole('button', { name: 'Validate' }));
        await waitFor(() =>
            expect(
                screen.getByLabelText('Standard overtime rate')
            ).toHaveValue(1.7)
        );
    });

    it('switches to text-only mode when there are no unsaved edits', async () => {
        render(
            <RuleConfigurationEditor
                configurationId="builtin:hospitality"
                onConfigurationSaved={vi.fn()}
            />
        );
        const toggle = await screen.findByRole('checkbox', {
            name: 'Review Helper',
        });
        fireEvent.click(toggle);
        expect(screen.queryByText('Ordinary hours')).not.toBeInTheDocument();
        expect(screen.getByText('Advanced Python').parentElement).toHaveAttribute(
            'open'
        );
    });

    it('supports repeatable penalty rows', async () => {
        render(
            <RuleConfigurationEditor
                configurationId="builtin:hospitality"
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
                configurationId="builtin:hospitality"
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

    it('saves guided values as a selected custom copy', async () => {
        const onConfigurationSaved = vi.fn();
        render(
            <RuleConfigurationEditor
                configurationId="builtin:hospitality"
                onConfigurationSaved={onConfigurationSaved}
            />
        );
        fireEvent.change(
            await screen.findByLabelText('Standard overtime rate'),
            { target: { value: '9' } }
        );
        fireEvent.click(
            screen.getByRole('button', { name: 'Save custom copy' })
        );

        await waitFor(() =>
            expect(api.createRuleConfiguration).toHaveBeenCalled()
        );
        expect(api.createRuleConfiguration.mock.calls[0][3]).not.toBeNull();
        expect(onConfigurationSaved).toHaveBeenCalledWith(
            expect.objectContaining({
                id: 'custom:hospitality:reviewed',
            })
        );
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
                configurationId="custom:hospitality:first"
                onConfigurationSaved={vi.fn()}
            />
        );
        await waitFor(() =>
            expect(pending['custom:hospitality:first']).toBeTypeOf('function')
        );

        rerender(
            <RuleConfigurationEditor
                configurationId="custom:hospitality:second"
                onConfigurationSaved={vi.fn()}
            />
        );
        await waitFor(() =>
            expect(pending['custom:hospitality:second']).toBeTypeOf('function')
        );

        pending['custom:hospitality:second']({
            ...configuration(),
            id: 'custom:hospitality:second',
            kind: 'custom',
            source: 'class HospitalityRules:\n    VALUE = 2\n',
        });
        expect(await screen.findByLabelText('Rule class source')).toHaveValue(
            'class HospitalityRules:\n    VALUE = 2\n'
        );

        pending['custom:hospitality:first']({
            ...configuration(),
            id: 'custom:hospitality:first',
            kind: 'custom',
            source: 'class HospitalityRules:\n    VALUE = 1\n',
        });
        await waitFor(() =>
            expect(screen.getByLabelText('Rule class source')).toHaveValue(
                'class HospitalityRules:\n    VALUE = 2\n'
            )
        );
    });
});
