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

import React, { useState } from 'react';
import { usePay } from '../../context/PayContext';
import { formatCurrency } from '../../utils/formatters';
import { createFortnightShifts, createShift } from '../Config/shifts';
import { useAuth } from '../../context/AuthContext';

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
export default function Header({ onOpenLimitations }) {
    const { state, dispatch } = usePay();
    const { user, openLogin, logout } = useAuth();
    const [copyStatus, setCopyStatus] = useState('');

    /**
     * Resets all shifts to default 9-5 schedule
     * Dispatches UPDATE_SHIFTS action to PayContext
     */
    const resetToDefault = () => {
        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: DEFAULT_SHIFTS.map((shift) => ({
                ...shift,
                break_duration: state.config.workerType === 'shift' ? '0' : '0.5',
            }))
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
            payload: EMPTY_SHIFTS.map((shift) => ({
                ...shift,
                break_duration: state.config.workerType === 'shift' ? '0' : '0.5',
            }))
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
                lunch_start: shift.lunch_start,
                public_holiday: shift.public_holiday,
            })),
        ];

        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: newShifts
        });
    };

    const formatTime = (value) => {
        if (value === '' || value === null || value === undefined) return null;
        const input = value.toString().trim();
        const clockMatch = /^(\d{1,2}):(\d{2})$/.exec(input);
        const time = clockMatch
            ? Number.parseInt(clockMatch[1], 10) + (Number.parseInt(clockMatch[2], 10) / 60)
            : Number.parseFloat(input);
        if (!Number.isFinite(time)) return value;
        const totalMinutes = Math.round((time % 24) * 60);
        const hours = Math.floor(totalMinutes / 60) % 24;
        const minutes = totalMinutes % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    };

    const copyCalculationDetails = async () => {
        const summary = state.shifts
            .map((shift, index) => ({ shift, index }))
            .filter(({ shift }) => shift.start !== '' || shift.end !== '')
            .map(({ shift }) => {
                const key = `Week ${shift.week || 1} - ${shift.day}`;
                const daily = state.calculations.dailyBreakdown?.[key];
                const isPrimary = shift.isPrimary !== false;
                const flags = [
                    shift.manual_overtime && 'Manual overtime',
                    shift.manual_ordinary && 'Manual ordinary',
                    (shift.public_holiday || state.publicHolidays?.some(
                        (holiday) => holiday.week === shift.week && holiday.day === shift.day
                    )) && 'Public holiday',
                ].filter(Boolean);

                return {
                    dayOfWeek: key,
                    startTime: formatTime(shift.start),
                    endTime: formatTime(shift.end),
                    lunchTime: formatTime(shift.lunch_start),
                    lunchLengthHours: Number.parseFloat(shift.break_duration) || 0,
                    flags,
                    amount: isPrimary && daily ? formatCurrency(daily.pay?.total ?? 0) : null,
                    appliedRules: isPrimary ? (daily?.applied_rules || []) : [],
                };
            });

        try {
            await navigator.clipboard.writeText(JSON.stringify(summary, null, 2));
            setCopyStatus('Calculation details copied');
        } catch {
            setCopyStatus('Could not copy');
        }
    };

    return (
        <header className="pay-header pay-shell">
            <div className="pay-brand">
                {/* Title and subtitle section */}
                <span className="brand-mark" aria-hidden="true">$</span>
                <div>
                    <p className="eyebrow">Pay period estimate</p>
                    <h1>
                        payguide.au
                    </h1>
                    <p className="sr-only">
                        Calculate your pay-period earnings
                    </p>
                </div>
            </div>

            {/* Control buttons section */}
            <div className="header-actions">
                {user ? (
                    <>
                        <span className="auth-user">Signed in as {user.display_name}</span>
                        <button onClick={logout} className="pay-button">Sign out</button>
                    </>
                ) : (
                    <button onClick={openLogin} className="pay-button">Sign in to save</button>
                )}
                <button
                    onClick={onOpenLimitations}
                    className="pay-button"
                >
                    Assumptions & limitations
                </button>
                <button
                    onClick={copyPreviousWeek}
                    className="pay-button"
                >
                    Copy Previous Week
                </button>
                <button
                    onClick={copyCalculationDetails}
                    className="pay-button"
                >
                    {copyStatus || 'Copy calculation details'}
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
        </header>
    );
}
