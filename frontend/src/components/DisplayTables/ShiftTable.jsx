
import React from 'react';
import { usePay } from '../../context/PayContext';
import ShiftTimeInput from './ShiftTimeInput';
import ShiftResults from './ShiftResults';

/**
 * ShiftTable Component
 *
 * Displays a table for editing and viewing fortnightly shift data.
 * Allows users to set start/end times and break duration for each day, and clear a day's values.
 *
 * Data Flow:
 * - state.shifts: Array of shift objects, from PayContext (global state)
 * - state.calculations: Calculated hours and totals, from PayContext (updated by ShiftCalculator)
 * - dispatch: Function from PayContext to update shifts in global state
 */

export default function ShiftTable() {
    const { state } = usePay();
    const getShiftKey = (shift) => `Week ${shift.week || 1} - ${shift.day}`;

    // Function to render a complete row by combining inputs and results
    const renderRow = (shift, idx, renderShiftInputs) => {
        return (
            <tr key={getShiftKey(shift)} className="hover:bg-gray-50">
                {renderShiftInputs(shift, idx)}
                <td className="px-2 py-1 whitespace-nowrap text-sm text-gray-900 font-medium">
                    {(Number(state.calculations.dailyBreakdown?.[getShiftKey(shift)]?.hours?.ordinary || 0) +
                        Number(state.calculations.dailyBreakdown?.[getShiftKey(shift)]?.hours?.overtime || 0)).toFixed(2)}
                </td>
                <td className="px-2 py-1 whitespace-nowrap text-sm text-gray-600">
                    {state.calculations.dailyBreakdown?.[getShiftKey(shift)]?.hours?.ordinary || '0.00'}
                </td>
                <td className="px-2 py-1 whitespace-nowrap text-sm text-red-600">
                    {state.calculations.dailyBreakdown?.[getShiftKey(shift)]?.hours?.overtime || '0.00'}
                </td>
                <td className="px-2 py-1 whitespace-nowrap text-sm text-gray-600">
                    {state.calculations.dailyBreakdown?.[getShiftKey(shift)]?.applied_rules?.join(', ') || '-'}
                </td>
            </tr>
        );
    };

    return (
        <section className="shift-card panel" aria-label="Fortnightly shift entries">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fortnight Day</th>
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
                    <ShiftTimeInput renderRow={renderRow} />
                    <ShiftResults />
                </tbody>
            </table>
        </section>
    );
}
