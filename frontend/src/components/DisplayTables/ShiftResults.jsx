import React from 'react';
import { usePay } from '../../context/PayContext';

export default function ShiftResults() {
    const { state } = usePay();

    return (
        <>
            {/* This function is only for the totals row */}
            <tr className="bg-gray-50 font-semibold">
                <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">Totals</td>
                <td className="px-2 py-2"></td>
                <td className="px-2 py-2"></td>
                <td className="px-2 py-2"></td>
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
                <td className="px-2 py-2"></td>
            </tr>
        </>
    );
}
