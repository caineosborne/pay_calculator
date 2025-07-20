
/**
 * ShiftCalculator Component
 *
 * This component is responsible for triggering pay calculations whenever shift data or hourly rate changes.
 * It uses the usePay hook to access global state and dispatch actions to update calculations.
 *
 * Data Flow:
 * - state.shifts: Comes from PayContext, originally set by initialShifts in shifts.js
 * - state.config.hourlyRate: Comes from PayContext, default set in PayContext.jsx
 * - dispatch: Provided by PayContext, used to update calculations and payments in global state
 *
 * When shifts or hourlyRate change, useEffect triggers an API call to /calculate, then updates state with results.
 */
import React, { useEffect } from 'react';
import { usePay } from '../../context/PayContext';


/**
 * ShiftCalculator wrapper component
 * @param {React.ReactNode} children - Child components to render
 * @returns {JSX.Element}
 */
export function ShiftCalculator({ children }) {
    // Access global state and dispatch from PayContext
    // state: { config, shifts, calculations, payments }
    // dispatch: function to update state
    const { state, dispatch } = usePay();

    useEffect(() => {
        /**
         * Triggers calculation of pay and hours when shifts or hourly rate change.
         * - state.shifts: Array of shift objects from PayContext
         * - state.config.hourlyRate: Hourly rate from PayContext
         *
         * Calls backend API and updates global state with results.
         */
        const calculateShifts = async () => {
            // Log current state for debugging
            // console.log('Calculate Shift - Calculating shifts with state:', {
            //     hourlyRate: state.config.hourlyRate, // From PayContext
            //     workerType: state.config.workerType, // From PayContext
            //     shifts: state.shifts // From PayContext
            // });

            // Filter out shifts that don't have both start and end times
            // state.shifts comes from PayContext, originally set by initialShifts in shifts.js
            const validShifts = state.shifts.filter(shift => {
                const hasStart = shift.start !== '' && shift.start !== null && shift.start !== undefined;
                const hasEnd = shift.end !== '' && shift.end !== null && shift.end !== undefined;
                return hasStart && hasEnd;
            });

            // If no hourly rate or no valid shifts, skip calculation
            if (!state.config.hourlyRate || validShifts.length === 0) {
                console.log('No hourly rate or valid shifts, skipping calculation');
                return;
            }

            try {
                // Helper function to convert time strings to numbers
                const parseTimeValue = (value) => {
                    if (!value && value !== 0) return null;

                    // If it ends with 'n', it's a next-day time
                    if (value.toString().endsWith('n')) {
                        const baseHour = parseInt(value);
                        return !isNaN(baseHour) && baseHour >= 0 && baseHour <= 23 ? baseHour + 24 : null;
                    }

                    // For regular numbers
                    const parsed = parseInt(value);
                    return !isNaN(parsed) && parsed >= 0 && parsed <= 30 ? parsed : null;
                };

                // Prepare the payload with parsed values
                const payload = {
                    hourly_rate: parseFloat(state.config.hourlyRate),
                    worker_type: state.config.workerType,
                    shifts: validShifts.map(shift => ({
                        day: shift.day,
                        start: parseTimeValue(shift.start),
                        end: parseTimeValue(shift.end),
                        break_duration: parseFloat(shift.break_duration) || 0
                    }))
                };

                // Log request payload for debugging
                console.log('Sending to API:', payload);

                // Send POST request to backend API for calculation
                const response = await fetch('https://pay-backend-rnag.onrender.com/calculate', {

                    // const response = await fetch('http://localhost:8000/calculate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });

                // Handle API errors
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('API Error Response:', errorText);
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }

                // data is what is sent from the API  
                const data = await response.json();
                // console.log('API Response:', data);

                // Format the daily breakdown to separate hours and pay
                // data.daily_breakdown: returned from backend API
                const formattedDailyBreakdown = {};
                Object.entries(data.daily_breakdown || {}).forEach(([day, values]) => {
                    formattedDailyBreakdown[day] = {
                        hours: {
                            ordinary: Number(values.ordinary || 0).toFixed(2),
                            overtime: Number(values.overtime || 0).toFixed(2),
                            total: Number(values.total || 0).toFixed(2)
                        },
                        pay: {
                            ordinary: Number(values.ordinary_pay || 0).toFixed(2),
                            overtime: Number(values.overtime_pay || 0).toFixed(2),
                            total: Number(values.pay || 0).toFixed(2)
                        },
                        applied_rules: values.applied_rules || []
                    };
                });

                // Dispatch action to update calculations and payments in global state
                // This updates PayContext, which triggers UI updates in child components
                dispatch({
                    type: 'UPDATE_CALCULATIONS',
                    payload: {
                        calculations: {
                            ordinaryHours: Number(data.ordinary_hours || 0).toFixed(2), // From API response
                            overtimeHours: Number(data.overtime_hours || 0).toFixed(2), // From API response
                            totalHours: Number(data.total_hours || 0).toFixed(2), // From API response
                            dailyBreakdown: formattedDailyBreakdown // Formatted above
                        },
                        payments: {
                            ordinaryPay: Number(data.ordinary_pay || 0).toFixed(2), // From API response
                            overtimePay: Number(data.overtime_pay || 0).toFixed(2), // From API response
                            penaltyPay: Number(data.penalty_pay || 0).toFixed(2), // From API response
                            totalPay: Number(data.total_pay || 0).toFixed(2) // From API response
                        }
                    }
                });
            } catch (error) {
                // Log any errors from calculation or API
                console.error('Calculation error:', error);
            }
        };

        // Run calculation when shifts, hourly rate, or worker type change
        calculateShifts();
    }, [state.shifts, state.config.hourlyRate, state.config.workerType, dispatch]); // Dependencies: PayContext state

    // Render child components
    return <>{children}</>;
}
