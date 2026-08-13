
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
        const isPrimary = shift.isPrimary !== false;
        const breakdown = state.calculations.dailyBreakdown?.[getShiftKey(shift)];
        return (
            <tr key={shift.id || `${getShiftKey(shift)}-${idx}`} className={isPrimary ? 'hover:bg-gray-50' : 'bg-blue-50/40'}>
                {renderShiftInputs(shift, idx)}
                {isPrimary ? <>
                    <td className="px-2 py-1 whitespace-nowrap text-sm text-gray-900 font-medium">
                        {(Number(breakdown?.hours?.ordinary || 0) + Number(breakdown?.hours?.overtime || 0)).toFixed(2)}
                    </td>
                    <td className="px-2 py-1 whitespace-nowrap text-sm text-gray-600">{breakdown?.hours?.ordinary || '0.00'}</td>
                    <td className="px-2 py-1 whitespace-nowrap text-sm text-red-600">{breakdown?.hours?.overtime || '0.00'}</td>
                    <td className="px-2 py-1 whitespace-nowrap text-sm font-medium text-gray-900">${breakdown?.pay?.total || '0.00'}</td>
                    <td className="min-w-64 px-2 py-1 text-sm text-gray-600 whitespace-normal">{breakdown?.applied_rules?.join(', ') || '-'}</td>
                </> : <td colSpan="5" className="px-2 py-1 text-xs italic text-gray-500">Combined with the workday above</td>}
            </tr>
        );
    };

    return (
        <section className="shift-card panel" aria-label="Fortnightly shift entries">
            {state.calculationError && (
                <p role="alert" className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {state.calculationError}
                </p>
            )}
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fortnight Day</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">End</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lunch starts</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unpaid break (hrs)</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Manual OT</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Manual ORD</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Public Holiday</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Hours</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">ORD Hours</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">OT Hours</th>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
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
