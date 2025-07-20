/**
 * SummaryTable Component
 *
 * Displays a summary of calculated pay and hours for the week.
 * Reads calculated results from PayContext (global state) and presents them in a grid.
 *
 * Data Flow:
 * - state.payments: Contains ordinary, overtime, penalty, and total pay (from API via ShiftCalculator)
 * - state.calculations: Contains ordinary, overtime, and total hours (from API via ShiftCalculator)
 *
 * Key Sections:
 * - Ordinary: Shows ordinary pay and hours
 * - Overtime: Shows overtime pay and hours
 * - Penalty: Shows penalty pay (if any)
 * - Total: Shows total pay and total hours
 *
 * This component is purely presentational and does not perform any calculations itself.
 */


import React from 'react';
import { usePay } from '../../context/PayContext';


export default function SummaryTable() {
    // Access calculated results from PayContext global state
    const { state } = usePay();

    // Check if total hours are zero
    const isZeroHours = state.calculations.totalHours === 0;

    return (
        <div className="w-full bg-white rounded-lg p-4">
            {/* Pay summary header */}
            <h2 className="text-xl font-bold text-gray-900 mb-3">Pay Summary</h2>
            {/* Grid of pay categories and hours */}
            <div className="w-full grid grid-cols-4 gap-3">
                {/* Ordinary pay and hours */}
                <div className="bg-gray-50 p-3 rounded-lg flex flex-col items-center">
                    <div className="text-sm text-gray-500">Ordinary</div>
                    <div className="mt-1 text-xl font-semibold text-blue-600">
                        ${isZeroHours ? '0.00' : state.payments.ordinaryPay || '0.00'}
                    </div>
                    <div className="mt-1 text-sm text-gray-600">
                        {isZeroHours ? '0.00' : state.calculations.ordinaryHours || '0.00'} hrs
                    </div>
                </div>
                {/* Overtime pay and hours */}
                <div className="bg-gray-50 p-3 rounded-lg flex flex-col items-center">
                    <div className="text-sm text-gray-500">Overtime</div>
                    <div className="mt-1 text-xl font-semibold text-blue-600">
                        ${isZeroHours ? '0.00' : state.payments.overtimePay || '0.00'}
                    </div>
                    <div className="mt-1 text-sm text-gray-600">
                        {isZeroHours ? '0.00' : state.calculations.overtimeHours || '0.00'} hrs
                    </div>
                </div>
                {/* Penalty pay (if any) */}
                <div className="bg-gray-50 p-3 rounded-lg flex flex-col items-center">
                    <div className="text-sm text-gray-500">Penalty</div>
                    <div className="mt-1 text-xl font-semibold text-blue-600">
                        ${isZeroHours ? '0.00' : state.payments.penaltyPay || '0.00'}
                    </div>
                    <div className="mt-1 text-sm text-gray-600">
                        &nbsp;
                    </div>
                </div>
                {/* Total pay and total hours */}
                <div className="bg-blue-50 p-3 rounded-lg flex flex-col items-center">
                    <div className="text-sm text-gray-500">Total</div>
                    <div className="mt-1 text-xl font-semibold text-blue-600">
                        ${isZeroHours ? '0.00' : state.payments.totalPay || '0.00'}
                    </div>
                    <div className="mt-1 text-sm text-gray-600">
                        {isZeroHours ? '0.00' : state.calculations.totalHours || '0.00'} hrs
                    </div>
                </div>
            </div>
        </div>
    );
}