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

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

/**
 * Default shift template for a 9-5 work schedule
 * Each object represents a day with start time, end time, and break duration
 * Weekend days are left empty by default
 */
const DEFAULT_SHIFTS = [
    ...WEEKDAYS.map((day, index) => ({
        week: 1,
        day,
        start: index < 5 ? '9' : '',
        end: index < 5 ? '17' : '',
        break_duration: '0.5'
    })),
    ...WEEKDAYS.map((day, index) => ({
        week: 2,
        day,
        start: index < 5 ? '9' : '',
        end: index < 5 ? '17' : '',
        break_duration: '0.5'
    }))
];

/**
 * Empty shift template for clearing all shifts
 * Maintains day structure but removes all times
 */
const EMPTY_SHIFTS = DEFAULT_SHIFTS.map(({ week, day }) => ({
    week,
    day,
    start: '',
    end: '',
    break_duration: ''
}));

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
        const previousWeek = state.shifts.slice(0, 7);
        const newShifts = [...state.shifts];

        previousWeek.forEach((shift, index) => {
            newShifts[index + 7] = {
                ...shift,
                week: 2
            };
        });

        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: newShifts
        });
    };

    return (
        <header className="bg-gray-100 shadow">
            <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center">
                    {/* Title and subtitle section */}
                    <div>
                        <h1 className="text-2xl font-bold text-black">
                            🧾 Pay Checker
                        </h1>
                        <p className="mt-1 text-sm text-black">
                            Calculate your fortnightly earnings
                        </p>
                    </div>

                    {/* Control buttons section */}
                    <div className="flex space-x-3">
                        <button
                            onClick={copyPreviousWeek}
                            className="inline-flex items-center px-3 py-2 border
                                     text-sm leading-4 font-medium rounded-md text-black
                                     bg-grey-400 hover:bg-gray-700 focus:outline-none
                                     focus:ring-2 focus:ring-offset-2 focus:ring-black"
                        >
                            Copy Previous Week
                        </button>
                        <button
                            onClick={resetToDefault}
                            className="inline-flex items-center px-3 py-2 border  
                                     text-sm leading-4 font-medium rounded-md text-black 
                                     bg-grey-400 hover:bg-gray-800 focus:outline-none 
                                     focus:ring-2 focus:ring-offset-2 focus:ring-black"
                        >
                            Set to 9-5
                        </button>
                        <button
                            onClick={clearAllShifts}
                            className="inline-flex items-center px-3 py-2 border 
                                     text-sm leading-4 font-medium rounded-md text-black 
                                     bg-grey-400 hover:bg-gray-600 focus:outline-none 
                                     focus:ring-2 focus:ring-offset-2 focus:ring-black"
                        >
                            Clear All
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
}
