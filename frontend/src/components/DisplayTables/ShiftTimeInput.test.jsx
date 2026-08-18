import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
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
            shifts: [{ id: 'monday', week: 1, day: 'Monday', start: '9', end: '17', break_duration: '0', public_holiday: false }],
            publicHolidays: [],
            config: { workerType: 'shift' },
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

    it('sets public holiday status on the individual shift segment', () => {
        const dispatch = renderTimeInput();
        fireEvent.click(screen.getByLabelText('Week 1 Monday public holiday'));

        expect(dispatch).toHaveBeenCalledWith({
            type: 'UPDATE_SHIFTS',
            payload: [expect.objectContaining({ public_holiday: true })],
        });
    });

    it('copies Sunday into the destination Monday of the following week', () => {
        const dispatch = vi.fn();
        payContext = {
            state: {
                shifts: [
                    { id: 'sunday', week: 1, day: 'Sunday', start: '9', end: '17', break_duration: '0', public_holiday: false },
                    { id: 'week-two-monday', week: 2, day: 'Monday', start: '', end: '', break_duration: '0', public_holiday: false },
                ],
                publicHolidays: [],
                config: { workerType: 'shift' },
            },
            dispatch,
        };
        render(
            <table><tbody>
                <ShiftTimeInput renderRow={(shift, idx, renderInputs) => <tr key={shift.id}>{renderInputs(shift, idx)}</tr>} />
            </tbody></table>
        );

        const mondayRow = screen
            .getByLabelText('Week 2 Monday primary shift start')
            .closest('tr');
        fireEvent.click(
            within(mondayRow).getAllByRole('button', { name: 'Copy previous' })[0]
        );

        expect(dispatch).toHaveBeenCalledWith({
            type: 'UPDATE_SHIFTS',
            payload: [
                expect.objectContaining({ id: 'sunday', week: 1, day: 'Sunday' }),
                expect.objectContaining({ week: 2, day: 'Monday', start: '9', end: '17' }),
            ],
        });
    });
});
