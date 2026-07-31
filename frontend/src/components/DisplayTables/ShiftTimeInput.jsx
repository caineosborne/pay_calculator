import React from 'react';
import { usePay } from '../../context/PayContext';

export default function ShiftTimeInput({ renderRow }) {
    const { state, dispatch } = usePay();

    const handleShiftChange = (idx, field, value) => {
        const newShifts = [...state.shifts];
        newShifts[idx] = {
            ...newShifts[idx],
            [field]: value
        };

        // Check if all shifts are empty (no start or end times)
        const allShiftsEmpty = newShifts.every(shift => !shift.start || !shift.end);

        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: newShifts
        });

        // If all shifts are empty, reset calculations and payments
        if (allShiftsEmpty) {
            dispatch({
                type: 'UPDATE_CALCULATIONS',
                payload: {
                    calculations: {
                        ordinaryHours: 0,
                        overtimeHours: 0,
                        totalHours: 0,
                        dailyBreakdown: {}
                    },
                    payments: {
                        ordinaryPay: 0,
                        overtimePay: 0,
                        penaltyPay: 0,
                        totalPay: 0
                    }
                }
            });
        }
    };

    const formatTimeDisplay = (value) => {
        if (!value && value !== 0) return '';
        const numValue = parseInt(value);
        if (isNaN(numValue)) return '';
        // Keep the API value as 24-30 for next-day times, but show the
        // corresponding clock hour (midnight through 6am) in the UI.
        return (numValue >= 24 ? numValue - 24 : numValue).toString();
    };

    const parseTimeInput = (value, currentValue, field) => {
        if (!value && value !== 0) return null;
        const parsed = parseInt(value);
        if (!isNaN(parsed)) {
            // If the current value is next-day, interpret displayed 0-6am
            // values as next-day values while preserving the API contract.
            const isNextDay = currentValue > 23;
            const displayMax = field === 'end' ? 6 : 0;
            if (isNextDay && parsed >= 0 && parsed <= displayMax) {
                return (parsed + 24).toString();
            }

            // Also continue to accept the raw next-day values when entered
            // directly (for example, 25), as before.
            if (parsed >= 0 && parsed <= 30) {
                return parsed.toString();
            }
        }
        return null;
    };

    const handleTimeChange = (idx, field, value, isInput = false) => {
        let newValue;
        const shift = state.shifts[idx];

        if (field === 'break_duration') {
            newValue = value === '' ? shift.break_duration :
                Math.max(0, Math.min(24, parseFloat(value) || 0)).toString();
        } else if (isInput) {
            // Handle direct input
            const currentValue = parseInt(shift[field]);
            const parsedValue = parseTimeInput(value, currentValue, field);
            if (parsedValue === null) {
                newValue = shift[field];
            } else {
                const intValue = parseInt(parsedValue);
                // For next-day times (>24), keep the actual value for API
                newValue = intValue > 24 ? intValue.toString() :
                    Math.min(field === 'end' ? 30 : 24, Math.max(0, intValue || 0)).toString();
            }
        } else {
            const currentValue = parseInt(shift[field]);
            if (value === 'increment') {
                if (!currentValue && currentValue !== 0) {
                    // Field is blank, try to get previous day's value
                    if (idx > 0) {
                        const prevValue = parseInt(state.shifts[idx - 1][field]);
                        newValue = (prevValue || (field === 'end' ? 17 : 9)).toString();
                    } else {
                        newValue = field === 'end' ? '17' : '9'; // Default to 17 for end time, 9 for start time
                    }
                } else {
                    const maxValue = field === 'end' ? 30 : 24;
                    newValue = Math.min(maxValue, currentValue + 1).toString();
                }
            } else if (value === 'decrement') {
                newValue = Math.max(0, (currentValue || 0) - 1).toString();
            }
        }
        handleShiftChange(idx, field, newValue);
    };

    const clearDay = (idx) => {
        const newShifts = [...state.shifts];
        newShifts[idx] = {
            ...newShifts[idx],
            start: '',
            end: '',
            break_duration: '0.5'
        };

        // Check if all shifts are now empty
        const allShiftsEmpty = newShifts.every(shift => !shift.start || !shift.end);

        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: newShifts
        });

        // If all shifts are empty, reset calculations and payments
        if (allShiftsEmpty) {
            dispatch({
                type: 'UPDATE_CALCULATIONS',
                payload: {
                    calculations: {
                        ordinaryHours: 0,
                        overtimeHours: 0,
                        totalHours: 0,
                        dailyBreakdown: {}
                    },
                    payments: {
                        ordinaryPay: 0,
                        overtimePay: 0,
                        penaltyPay: 0,
                        totalPay: 0
                    }
                }
            });
        }
    };

    const renderShiftInputs = (shift, idx) => {
        const isFirstDayOfWeek = idx % 7 === 0;
        return (
            <>
                <td className="px-2 py-1 whitespace-nowrap text-sm font-medium text-gray-900">
                    Week {shift.week || 1} - {shift.day}
                </td>
                <td className="px-2 py-1 whitespace-nowrap">
                    <div className="flex items-center space-x-1">
                        <button aria-label={`Decrease ${shift.day} start time`} onClick={() => handleTimeChange(idx, 'start', 'decrement')} className="time-adjust">−</button>
                        <input
                            type="text"
                            value={formatTimeDisplay(shift.start)}
                            onChange={(e) => handleTimeChange(idx, 'start', e.target.value, true)}
                            className="shift-input text-center"
                        />
                        <button aria-label={`Increase ${shift.day} start time`} onClick={() => handleTimeChange(idx, 'start', 'increment')} className="time-adjust">+</button>
                    </div>
                </td>
                <td className="px-2 py-1 whitespace-nowrap">
                    <div className="flex items-center space-x-1">
                        <button aria-label={`Decrease ${shift.day} end time`} onClick={() => handleTimeChange(idx, 'end', 'decrement')} className="time-adjust">−</button>
                        <input
                            type="text"
                            value={formatTimeDisplay(shift.end)}
                            onChange={(e) => handleTimeChange(idx, 'end', e.target.value, true)}
                            className="shift-input text-center"
                        />
                        <button aria-label={`Increase ${shift.day} end time`} onClick={() => handleTimeChange(idx, 'end', 'increment')} className="time-adjust">+</button>
                    </div>
                </td>
                <td className="px-2 py-1 whitespace-nowrap">
                    <div className="flex items-center space-x-1">
                        <input
                            type="number"
                            value={shift.break_duration}
                            onChange={(e) => handleTimeChange(idx, 'break_duration', e.target.value, true)}
                            className="shift-input text-center"
                            step="0.5"
                            min="0"
                            max="24"
                        />
                        <div className="flex space-x-1">
                            <button
                                onClick={() => clearDay(idx)}
                                className="day-action ml-2"
                                title="Clear times"
                            >
                                Clear
                            </button>
                            <button
                                onClick={() => {
                                    if (idx > 0 && !isFirstDayOfWeek) {
                                        const prevShift = state.shifts[idx - 1];
                                        const newShifts = [...state.shifts];
                                        newShifts[idx] = {
                                            ...newShifts[idx],
                                            start: prevShift.start,
                                            end: prevShift.end,
                                            break_duration: prevShift.break_duration
                                        };
                                        dispatch({
                                            type: 'UPDATE_SHIFTS',
                                            payload: newShifts
                                        });
                                    }
                                }}
                                className="day-action"
                                title="Copy times from previous day"
                                disabled={isFirstDayOfWeek}
                            >
                                Copy Prev
                            </button>
                        </div>
                    </div>
                </td>
            </>
        );
    };

    return state.shifts.map((shift, idx) => renderRow(shift, idx, renderShiftInputs));
}
