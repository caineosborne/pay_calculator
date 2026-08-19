import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import AcademicCalculator from './AcademicCalculator';
import { api } from '../../services/apis';

vi.mock('../../services/apis', () => ({
    api: {
        getAcademicRuleset: vi.fn(),
        calculateAcademicPay: vi.fn(),
    },
}));

const ruleset = {
    scheme: { label: 'QUT Sessional Academic Staff', minimum_engagement_hours: 2 },
    eligibility: {
        standard: 'Standard sessional rate',
        relevant_phd: 'Relevant doctoral qualification',
        full_coordinator: 'Full course/unit coordination duties',
    },
    activities: {
        tutorial: {
            label: 'Tutorial',
            payment_basis: 'composite_unit',
            quantity_label: 'Tutorial delivery hours',
            quantity_help: 'Enter tutorial time delivered. The published rate already includes associated working time.',
            course_required: true,
            topic_required: true,
            repeatable: true,
            variants: { normal: 'Normal tutorial' },
            default_variant: 'normal',
        },
        marking: {
            label: 'Marking',
            payment_basis: 'direct_hour',
            quantity_label: 'Approved hours',
            course_required: true,
            repeatable: false,
            requires_approval: true,
            variants: { standard: 'Standard marking' },
            default_variant: 'standard',
        },
    },
};

const emptyResult = {
    line_items: [],
    occasions: [],
    activity_pay: 0,
    direct_hours_pay: 0,
    total_pay: 0,
    delivered_hours: 0,
    direct_hours: 0,
    incorporated_hours: 0,
    actual_associated_hours: 0,
    review_warnings: [],
};

describe('AcademicCalculator', () => {
    beforeEach(() => {
        const storage = {};
        Object.defineProperty(window, 'localStorage', {
            configurable: true,
            value: {
                getItem: vi.fn((key) => storage[key] ?? null),
                setItem: vi.fn((key, value) => { storage[key] = value; }),
                removeItem: vi.fn((key) => { delete storage[key]; }),
                clear: vi.fn(() => Object.keys(storage).forEach((key) => delete storage[key])),
            },
        });
        api.getAcademicRuleset.mockResolvedValue(ruleset);
        api.calculateAcademicPay.mockResolvedValue(emptyResult);
    });

    it('starts blank and submits a date-only activity using the academic route', async () => {
        render(<AcademicCalculator scheme="qut_sessional" />);

        expect(await screen.findByRole('heading', { name: 'QUT Sessional Academic Staff' })).toBeInTheDocument();
        expect(screen.getAllByText('No work entered')).toHaveLength(14);

        fireEvent.change(screen.getByLabelText('Course code'), { target: { value: 'LLB101' } });
        fireEvent.click(screen.getByRole('button', { name: 'Add course' }));

        const courseSelect = screen.getByLabelText('Course taught');
        fireEvent.change(courseSelect, { target: { value: courseSelect.options[1].value } });

        fireEvent.change(screen.getByLabelText('Topic or teaching week'), {
            target: { value: 'Week 3 - Negligence' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Add to fortnight' }));

        await waitFor(() => expect(api.calculateAcademicPay).toHaveBeenCalled());
        const payload = api.calculateAcademicPay.mock.calls.at(-1)[0];
        expect(payload.scheme).toBe('qut_sessional');
        expect(payload.work_items[0]).toMatchObject({
            kind: 'activity',
            activity: 'tutorial',
            topic: 'Week 3 - Negligence',
            delivered_quantity: 1,
        });
        expect(payload.work_items[0]).not.toHaveProperty('start');
        expect(payload.work_items[0]).not.toHaveProperty('end');
        expect(screen.getByPlaceholderText('e.g. Week 3 - Negligence')).toHaveAttribute('list', 'academic-topic-options');
        expect(document.querySelector('#academic-topic-options option')).toHaveAttribute('value', 'Week 3 - Negligence');
        expect(
            screen.getByText('Was this part of the same work occasion?').closest('label')?.querySelector('select')
        ).toBeInTheDocument();
    });

    it('switches the form to required direct hours for marking', async () => {
        render(<AcademicCalculator scheme="qut_sessional" />);
        await screen.findByRole('heading', { name: 'QUT Sessional Academic Staff' });

        fireEvent.change(screen.getByLabelText('Work type'), { target: { value: 'marking' } });

        expect(screen.getByText('Direct hours', { selector: 'h2' })).toBeInTheDocument();
        expect(screen.getByLabelText('Approved hours')).toBeInTheDocument();
        expect(screen.getByText('These hours were required or approved.')).toBeInTheDocument();
    });
});
