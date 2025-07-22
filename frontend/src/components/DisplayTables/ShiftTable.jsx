
import React from 'react';
import { usePay } from '../../context/PayContext';
/**
 * ShiftTable Component
 *
 * Displays a table for editing and viewing weekly shift data.
 * Allows users to set start/end times and break duration for each day, and clear a day's values.
 *
 * Data Flow:
 * - state.shifts: Array of shift objects, from PayContext (global state)
 * - state.calculations: Calculated hours and totals, from PayContext (updated by ShiftCalculator)
 * - dispatch: Function from PayContext to update shifts in global state
 *
 * Key Sections:
 * - handleShiftChange: Updates a single shift in the array and dispatches to PayContext
 * - handleTimeChange: Handles increment/decrement/input for time fields, validates input, and calls handleShiftChange
 * - clearDay: Clears all time values for a specific day and dispatches update
 * - Table rendering: Displays editable fields for each day, and calculated results for ordinary/OT/total hours
 * - Totals row: Shows weekly totals for ordinary, overtime, and total hours
 */

export default function ShiftTable() {
    const { state, dispatch } = usePay();

    // console.log('Shift Table State:', state);

    // --- Shift update logic ---

    /**
     * Updates a single shift in the array and dispatches to PayContext
     * @param {number} idx - Index of the shift to update
     * @param {string} field - Field to update (start, end, break_duration)
     * @param {string|number} value - New value for the field
     */
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

    /**
     * Handles increment/decrement/input for time fields, validates input, and calls handleShiftChange
     * @param {number} idx - Index of the shift
     * @param {string} field - Field to update
     * @param {string|number} value - New value or action (increment/decrement)
     * @param {boolean} isInput - True if direct input, false if button
     */
    // Helper function to format time display
    const formatTimeDisplay = (value) => {
        if (!value && value !== 0) return '';
        const numValue = parseInt(value);
        if (isNaN(numValue)) return '';
        return numValue.toString();
    };

    // Helper function to parse time input
    const parseTimeInput = (value) => {
        if (!value && value !== 0) return null;
        const parsed = parseInt(value);
        if (!isNaN(parsed)) {
            // Allow values 0-30 (up to 6am next day)
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
            const parsedValue = parseTimeInput(value);
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

    /**
     * Clears all time values for a specific day and dispatches update
     * @param {number} idx - Index of the shift/day to clear
     */
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

    // --- Table rendering ---

    return (
        <div className="bg-white rounded-lg shadow overflow-hidden">
            {/* Table header: Days and fields */}
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Day</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">End</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Break (hrs)</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Hours</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">ORD Hours</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">OT Hours</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Applied Rules</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {/* Render each day's shift row */}
                    {state.shifts.map((shift, idx) => (
                        <tr key={shift.day} className="hover:bg-gray-50">
                            <td className="px-2 py-1 whitespace-nowrap text-sm font-medium text-gray-900">
                                {shift.day}
                            </td>
                            {/* Editable start time */}
                            <td className="px-2 py-1 whitespace-nowrap">
                                <div className="flex items-center space-x-1">
                                    <button onClick={() => handleTimeChange(idx, 'start', 'decrement')} className="p-1 text-gray-500 hover:text-gray-700">-</button>
                                    <input
                                        type="text"
                                        value={formatTimeDisplay(shift.start)}
                                        onChange={(e) => handleTimeChange(idx, 'start', e.target.value, true)}
                                        className="w-16 p-1 text-center border rounded"
                                    />
                                    <button onClick={() => handleTimeChange(idx, 'start', 'increment')} className="p-1 text-gray-500 hover:text-gray-700">+</button>
                                </div>
                            </td>
                            {/* Editable end time */}
                            <td className="px-2 py-1 whitespace-nowrap">
                                <div className="flex items-center space-x-1">
                                    <button onClick={() => handleTimeChange(idx, 'end', 'decrement')} className="p-1 text-gray-500 hover:text-gray-700">-</button>
                                    <input
                                        type="text"
                                        value={formatTimeDisplay(shift.end)}
                                        onChange={(e) => handleTimeChange(idx, 'end', e.target.value, true)}
                                        className="w-16 p-1 text-center border rounded"
                                    />
                                    <button onClick={() => handleTimeChange(idx, 'end', 'increment')} className="p-1 text-gray-500 hover:text-gray-700">+</button>
                                </div>
                            </td>
                            {/* Editable break duration and clear button */}
                            <td className="px-2 py-1 whitespace-nowrap">
                                <div className="flex items-center space-x-1">
                                    <input
                                        type="number"
                                        value={shift.break_duration}
                                        onChange={(e) => handleTimeChange(idx, 'break_duration', e.target.value, true)}
                                        className="w-16 p-1 text-center border rounded"
                                        step="0.5"
                                        min="0"
                                        max="24"
                                    />
                                    <div className="flex space-x-1">
                                        <button
                                            onClick={() => clearDay(idx)}
                                            className="ml-2 px-2 py-0.5 bg-gray-200 rounded text-xs hover:bg-gray-300"
                                            title="Clear times"
                                        >
                                            Clear
                                        </button>
                                        <button
                                            onClick={() => {
                                                if (idx > 0) {
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
                                            className="px-2 py-0.5 bg-blue-100 rounded text-xs hover:bg-blue-200"
                                            title="Copy times from previous day"
                                            disabled={idx === 0}
                                        >
                                            Copy Prev
                                        </button>
                                    </div>
                                </div>
                            </td>
                            {/* Calculated total hours for the day */}
                            <td className="px-2 py-1 whitespace-nowrap text-sm text-gray-900 font-medium">
                                {(Number(state.calculations.dailyBreakdown?.[shift.day]?.hours?.ordinary || 0) +
                                    Number(state.calculations.dailyBreakdown?.[shift.day]?.hours?.overtime || 0)).toFixed(2)}
                            </td>
                            {/* Calculated ordinary hours for the day */}
                            <td className="px-2 py-1 whitespace-nowrap text-sm text-gray-600">
                                {state.calculations.dailyBreakdown?.[shift.day]?.hours?.ordinary || '0.00'}
                            </td>
                            {/* Calculated overtime hours for the day */}
                            <td className="px-2 py-1 whitespace-nowrap text-sm text-red-600">
                                {state.calculations.dailyBreakdown?.[shift.day]?.hours?.overtime || '0.00'}
                            </td>
                            <td className="px-2 py-1 whitespace-nowrap text-sm text-gray-600">
                                {state.calculations.dailyBreakdown?.[shift.day]?.applied_rules?.join(', ') || '-'}
                            </td>
                        </tr>
                    ))}
                    {/* Totals Row: Weekly totals for ordinary, overtime, and total hours */}
                    <tr className="bg-gray-50 font-semibold">
                        <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">Totals</td>
                        <td className="px-2 py-2"></td>
                        <td className="px-2 py-2"></td>
                        <td className="px-2 py-2"></td>
                        <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                            {state.calculations.totalHours || '0.00'}
                        </td>
                        <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-600">
                            {state.calculations.ordinaryHours || '0.00'}
                        </td>
                        <td className="px-2 py-2 whitespace-nowrap text-sm text-red-600">
                            {state.calculations.overtimeHours || '0.00'}
                        </td>
                        <td className="px-2 py-2"></td>
                    </tr>
                </tbody>
            </table>
        </div>
    );
}