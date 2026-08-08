import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ShiftTimeInput from './ShiftTimeInput';

let payContext;

vi.mock('../../context/PayContext', () => ({
    usePay: () => payContext,
}));

const renderTimeInput = () => {
    const dispatch = vi.fn();
    payContext = {
        state: {
            shifts: [{ id: 'monday', week: 1, day: 'Monday', start: '9', end: '17', break_duration: '0.5' }],
            publicHolidays: [],
        },
        dispatch,
    };
    render(
        <table><tbody>
            <ShiftTimeInput renderRow={(shift, idx, renderInputs) => <tr key={shift.id}>{renderInputs(shift, idx)}</tr>} />
        </tbody></table>
    );
    return dispatch;
};

describe('ShiftTimeInput', () => {
    beforeEach(() => vi.clearAllMocks());

    it.each([
        ['3', '3'],
        ['3.5', (3 + (50 / 60)).toString()],
        ['09:15', '9.25'],
        ['08:06', '8.1'],
    ])('commits %s when the input loses focus', (entry, expectedStart) => {
        const dispatch = renderTimeInput();
        const input = screen.getByLabelText('Week 1 Monday primary shift start');

        fireEvent.change(input, { target: { value: entry } });
        fireEvent.blur(input);

        expect(dispatch).toHaveBeenCalledWith({
            type: 'UPDATE_SHIFTS',
            payload: [expect.objectContaining({ start: expectedStart })],
        });
    });

    it('lets a user set an optional lunch start time', () => {
        const dispatch = renderTimeInput();
        const input = screen.getByLabelText('Week 1 Monday primary lunch start');

        fireEvent.change(input, { target: { value: '12:15' } });
        fireEvent.blur(input);

        expect(dispatch).toHaveBeenCalledWith({
            type: 'UPDATE_SHIFTS',
            payload: [expect.objectContaining({ lunch_start: '12.25' })],
        });
    });
});
