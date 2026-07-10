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
import { formatCurrency } from '../../utils/formatters';

const FORTNIGHTS_PER_YEAR = 26;
const MEDICARE_LEVY_RATE = 0.02;

// The 15% first bracket is the rate effective from 1 July 2026.
const calculateIncomeTax = (annualIncome) => {
    if (annualIncome <= 18200) return 0;
    if (annualIncome <= 45000) return (annualIncome - 18200) * 0.15;
    if (annualIncome <= 135000) return 4020 + (annualIncome - 45000) * 0.30;
    if (annualIncome <= 190000) return 31020 + (annualIncome - 135000) * 0.37;
    return 51370 + (annualIncome - 190000) * 0.45;
};

const calculateEstimatedFortnightlyNetPay = (fortnightlyGrossPay) => {
    const annualGrossPay = fortnightlyGrossPay * FORTNIGHTS_PER_YEAR;
    const annualTax = calculateIncomeTax(annualGrossPay);
    const annualMedicareLevy = annualGrossPay * MEDICARE_LEVY_RATE;

    return (annualGrossPay - annualTax - annualMedicareLevy) / FORTNIGHTS_PER_YEAR;
};

const SummaryTable = () => {
    const { state } = usePay();
    const { calculations, payments } = state;
    const totalPay =
        parseFloat(payments?.ordinaryPay || 0) +
        parseFloat(payments?.overtimePay || 0) +
        parseFloat(payments?.topupPay || 0) +
        parseFloat(payments?.penaltyPay || 0);
    const estimatedNetPay = calculateEstimatedFortnightlyNetPay(totalPay);

    return (
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
            <h2 className="text-xl font-semibold mb-4">Pay Summary</h2>

            <div className="flex flex-wrap gap-4">
                {/* Ordinary Box */}
                <div className="flex-1 bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-gray-600 mb-2">Ordinary</div>
                    <div className="text-blue-500 font-bold text-xl">{formatCurrency(payments?.ordinaryPay || 0)}</div>
                    <div className="text-gray-500 text-sm">{calculations?.ordinaryHours || '0.00'} hrs</div>
                </div>

                {/* Overtime Box */}
                <div className="flex-1 bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-gray-600 mb-2">Overtime</div>
                    <div className="text-blue-500 font-bold text-xl">{formatCurrency(payments?.overtimePay || 0)}</div>
                    <div className="text-gray-500 text-sm">{calculations?.overtimeHours || '0.00'} hrs</div>
                </div>

                {/* Penalty Box */}
                <div className="flex-1 bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-gray-600 mb-2">Penalty</div>
                    <div className="text-blue-500 font-bold text-xl">{formatCurrency(payments?.penaltyPay || 0)}</div>
                    <div className="text-gray-500 text-sm">&nbsp;</div>
                </div>

                {/* Top-up Box */}
                <div className="flex-1 bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-gray-600 mb-2">Top-up</div>
                    <div className="text-blue-500 font-bold text-xl">{formatCurrency(payments?.topupPay || 0)}</div>
                    <div className="text-gray-500 text-sm">{calculations?.topupHours || '0.00'} hrs</div>
                </div>

                {/* Total Box */}
                <div className="flex-1 bg-blue-50 p-4 rounded-lg text-center">
                    <div className="text-gray-600 mb-2">Total</div>
                    <div className="text-blue-500 font-bold text-xl">
                        {formatCurrency(
                            totalPay.toFixed(2)
                        )}
                    </div>
                    <div className="text-gray-500 text-sm">{calculations?.totalHours || '0.00'} hrs</div>
                </div>
            </div>

            <div className="mt-4 border-t border-gray-200 pt-4 text-center">
                <div className="text-gray-600 mb-1">Estimated net pay</div>
                <div className="text-green-600 font-bold text-2xl">{formatCurrency(estimatedNetPay)}</div>
                <div className="text-gray-500 text-xs mt-1">
                    Approximate fortnightly amount after income tax and the 2% Medicare levy only.
                </div>
            </div>
        </div>
    );
};

export default SummaryTable;
