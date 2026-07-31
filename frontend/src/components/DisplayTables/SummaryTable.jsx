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
        <section className="summary-panel panel" aria-labelledby="pay-summary-title">
            <div className="summary-main">
                <p className="section-kicker">Calculated from your shifts</p>
                <h2 id="pay-summary-title">Pay breakdown</h2>
                <div className="summary-grid">
                    <div className="summary-item"><div className="summary-item-label">Ordinary</div><div className="summary-item-value">{formatCurrency(payments?.ordinaryPay || 0)}</div><div className="summary-item-hours">{calculations?.ordinaryHours || '0.00'} hrs</div></div>
                    <div className="summary-item"><div className="summary-item-label">Overtime</div><div className="summary-item-value">{formatCurrency(payments?.overtimePay || 0)}</div><div className="summary-item-hours">{calculations?.overtimeHours || '0.00'} hrs</div></div>
                    <div className="summary-item"><div className="summary-item-label">Penalty</div><div className="summary-item-value">{formatCurrency(payments?.penaltyPay || 0)}</div><div className="summary-item-hours">{calculations?.totalHours || '0.00'} total hrs</div></div>
                    <div className="summary-item"><div className="summary-item-label">Top-up</div><div className="summary-item-value">{formatCurrency(payments?.topupPay || 0)}</div><div className="summary-item-hours">{calculations?.topupHours || '0.00'} hrs</div></div>
                </div>
            </div>
            <div className="net-pay">
                <p className="eyebrow">Estimated take-home</p>
                <div className="net-pay-value">{formatCurrency(estimatedNetPay)}</div>
                <div className="net-pay-note">From {formatCurrency(totalPay.toFixed(2))} gross. This estimate includes income tax and the 2% Medicare levy only.</div>
            </div>
        </section>
    );
};

export default SummaryTable;
