import React from 'react';
import { usePay } from '../../context/PayContext';

export default function ShiftResults() {
    const { state } = usePay();

    return (
        <>
            {/* This function is only for the totals row */}
            <tr className="shift-totals-row bg-gray-50 font-semibold">
                <td className="shift-totals-label px-2 py-2 whitespace-nowrap text-sm text-gray-900">Pay period totals</td>
                <td className="shift-totals-spacer px-2 py-2"></td>
                <td className="shift-totals-spacer px-2 py-2"></td>
                <td className="shift-totals-spacer px-2 py-2"></td>
                <td className="shift-totals-spacer px-2 py-2"></td>
                <td className="shift-totals-spacer px-2 py-2"></td>
                <td className="shift-totals-spacer px-2 py-2"></td>
                <td className="shift-totals-spacer px-2 py-2"></td>
                <td className="shift-output-cell shift-total-cell px-2 py-2 whitespace-nowrap text-sm text-gray-900" data-label="Total hours">
                    {state.calculations.totalHours || '0.00'}
                </td>
                <td className="shift-output-cell shift-ordinary-cell px-2 py-2 whitespace-nowrap text-sm text-gray-600" data-label="Ordinary">
                    {state.calculations.ordinaryHours || '0.00'}
                </td>
                <td className="shift-output-cell shift-overtime-cell px-2 py-2 whitespace-nowrap text-sm text-red-600" data-label="Overtime">
                    {state.calculations.overtimeHours || '0.00'}
                </td>
                <td className="shift-amount-cell px-2 py-2"></td>
                <td className="shift-rules-cell px-2 py-2"></td>
            </tr>
        </>
    );
}
