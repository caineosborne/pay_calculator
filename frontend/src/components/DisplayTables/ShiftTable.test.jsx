import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ShiftTable from './ShiftTable';

let payContext;

vi.mock('../../context/PayContext', () => ({
    usePay: () => payContext,
}));

vi.mock('./ShiftTimeInput', () => ({
    default: ({ renderRow }) => renderRow(
        { id: 'monday', week: 1, day: 'Monday', isPrimary: true },
        0,
        () => null
    ),
}));

vi.mock('./ShiftResults', () => ({
    default: () => null,
}));

describe('ShiftTable', () => {
    it('always displays cents in daily pay totals', () => {
        payContext = {
            state: {
                calculations: {
                    dailyBreakdown: {
                        'Week 1 - Monday': {
                            hours: { ordinary: 8, overtime: 0 },
                            pay: { total: 123.4 },
                            applied_rules: [],
                        },
                    },
                },
            },
        };

        render(<ShiftTable />);

        expect(screen.getByText('$123.40')).toBeInTheDocument();
    });
});
