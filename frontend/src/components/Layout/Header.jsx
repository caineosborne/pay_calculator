/**
 * Header Component
 * 
 * This component renders the application header and provides controls for managing shift data.
 * It includes functionality to reset shifts to default 9-5 schedule or clear all shifts.
 * 
 * The component uses the PayContext to dispatch actions that update the global state.
 * 
 * @module Components/Layout
 */

import React from 'react';
import { usePay } from '../../context/PayContext';
import { createFortnightShifts, createShift } from '../Config/shifts';

/**
 * Default shift template for a 9-5 work schedule
 * Each object represents a day with start time, end time, and break duration
 * Weekend days are left empty by default
 */
const DEFAULT_SHIFTS = createFortnightShifts(true, true);

/**
 * Empty shift template for clearing all shifts
 * Maintains day structure but removes all times
 */
const EMPTY_SHIFTS = createFortnightShifts(false);

/**
 * Header component for the application
 * @returns {JSX.Element} Rendered header component
 */
export default function Header() {
    const { state, dispatch } = usePay();

    /**
     * Resets all shifts to default 9-5 schedule
     * Dispatches UPDATE_SHIFTS action to PayContext
     */
    const resetToDefault = () => {
        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: DEFAULT_SHIFTS
        });
    };

    /**
     * Clears all shift times while maintaining day structure
     * Dispatches UPDATE_SHIFTS action to PayContext
     */
    const clearAllShifts = () => {
        // Clear shifts
        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: EMPTY_SHIFTS
        });
        // Reset calculations and payments
        dispatch({
            type: 'UPDATE_CALCULATIONS',
            payload: {
                calculations: {
                    ordinaryHours: 0,
                    overtimeHours: 0,
                    totalHours: 0
                },
                payments: {
                    ordinaryPay: 0,
                    overtimePay: 0,
                    penaltyPay: 0,
                    totalPay: 0
                }
            }
        });
    };

    const copyPreviousWeek = () => {
        const previousWeek = state.shifts.filter((shift) => shift.week === 1);
        const newShifts = [
            ...previousWeek,
            ...previousWeek.map((shift, index) => createShift({
                week: 2,
                day: shift.day,
                sequence: index + 1,
                isPrimary: shift.isPrimary !== false,
                start: shift.start,
                end: shift.end,
                break_duration: shift.break_duration,
            })),
        ];

        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: newShifts
        });
    };

    return (
        <header className="pay-header pay-shell">
                <div className="pay-brand">
                    {/* Title and subtitle section */}
                    <span className="brand-mark" aria-hidden="true">$</span>
                    <div>
                        <p className="eyebrow">Fortnightly pay estimate</p>
                        <h1>
                            Pay Checker
                        </h1>
                        <p className="sr-only">
                            Calculate your fortnightly earnings
                        </p>
                    </div>

                    {/* Control buttons section */}
                    <div className="header-actions">
                        <button
                            onClick={copyPreviousWeek}
                            className="pay-button"
                        >
                            Copy Previous Week
                        </button>
                        <button
                            onClick={resetToDefault}
                            className="pay-button"
                        >
                            Set to 9-5
                        </button>
                        <button
                            onClick={clearAllShifts}
                            className="pay-button"
                        >
                            Clear All
                        </button>
                    </div>
                </div>
        </header>
    );
}
