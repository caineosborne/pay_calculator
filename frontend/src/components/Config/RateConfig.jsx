
/**
 * RateConfig Component
 *
 * This component allows the user to set or update their hourly pay rate.
 * It reads the current hourly rate from PayContext and updates it using dispatch.
 *
 * Data Flow:
 * - state.config.hourlyRate: Current hourly rate, from PayContext (global state)
 * - dispatch: Function from PayContext to update the hourly rate in global state
 *
 * When the input value changes, handleRateChange dispatches an UPDATE_HOURLY_RATE action,
 * which updates PayContext and triggers recalculation in ShiftCalculator.
 */
import React, { useState } from 'react';
import { usePay } from '../../context/PayContext';

export function RateConfig() {
    // Access global state and dispatch from PayContext
    // state.config.hourlyRate: current hourly rate
    // state.config.workerType: current worker type
    // dispatch: function to update hourly rate and worker type
    const { state, dispatch } = usePay();
    const [showRules, setShowRules] = useState(false);

    // Format applied rules to be more readable
    const formatRuleValue = (rule) => {
        if (typeof rule === 'number') {
            return rule + ' hours';
        }
        if (typeof rule === 'string') {
            // Format strings like '1.5x' or time strings
            return rule.includes(':') ? rule : (parseFloat(rule) * 100) + '%';
        }
        return rule;
    };

    const renderRules = () => {
        if (!state.calculations?.appliedRules) return null;

        const rules = state.calculations.appliedRules;
        return (
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm">
                <h3 className="font-medium mb-2 text-gray-900 dark:text-gray-100">
                    {state.config.workerType === 'shift' ? 'Shift Worker' : 'Day Worker'} Rules
                </h3>
                <div className="space-y-2">
                    {rules.span_hours && (
                        <div>
                            <span className="text-gray-600 dark:text-gray-300">Span Hours: </span>
                            <span className="font-medium">Overtime {rules.span_hours.threshold}, paid at {rules.span_hours.rate}</span>
                        </div>
                    )}
                    {rules.daily_overtime && (
                        <div>
                            <span className="text-gray-600 dark:text-gray-300">Daily Overtime: </span>
                            <span className="font-medium">After {formatRuleValue(rules.daily_overtime.threshold)}, paid at {rules.daily_overtime.rate}</span>
                        </div>
                    )}
                    {rules.weekly_overtime && (
                        <div>
                            <span className="text-gray-600 dark:text-gray-300">Weekly Overtime: </span>
                            <span className="font-medium">After {formatRuleValue(rules.weekly_overtime.threshold)}, paid at {rules.weekly_overtime.rate}</span>
                        </div>
                    )}
                    {rules.saturday_rules && (
                        <div>
                            <span className="text-gray-600 dark:text-gray-300">Saturday: </span>
                            <span className="font-medium">
                                {rules.saturday_rules.is_overtime ? 'All hours as overtime' :
                                    `Penalty rate ${formatRuleValue(rules.saturday_rules.penalty_rate)}`}
                            </span>
                        </div>
                    )}
                    {rules.sunday_rules && (
                        <div>
                            <span className="text-gray-600 dark:text-gray-300">Sunday: </span>
                            <span className="font-medium">
                                {rules.sunday_rules.is_overtime ? 'All hours as overtime' :
                                    `Penalty rate ${formatRuleValue(rules.sunday_rules.penalty_rate)}`}
                            </span>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    /**
     * Handles changes to the hourly rate input field.
     * Dispatches UPDATE_HOURLY_RATE to PayContext, updating global state.
     * @param {string|number} value - New hourly rate entered by user
     */
    const handleRateChange = (value) => {
        dispatch({
            type: 'UPDATE_HOURLY_RATE',
            payload: parseFloat(value) || 0 // Ensure value is a number
        });
    };

    /**
     * Handles changes to the worker type toggle.
     * Dispatches UPDATE_WORKER_TYPE to PayContext, updating global state.
     * @param {string} type - Worker type: 'shift' or 'day'
     */
    const handleWorkerTypeChange = (type) => {
        dispatch({
            type: 'UPDATE_WORKER_TYPE',
            payload: type
        });
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3">
            <div className="flex items-center justify-between gap-4">
                {/* Hourly rate input section */}
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                        Hourly Rate ($)
                    </label>
                    <input
                        type="number"
                        value={state.config.hourlyRate}
                        onChange={(e) => handleRateChange(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                </div>

                {/* Worker type toggle section */}
                <div className="flex-shrink-0">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                        Worker Type
                    </label>
                    <div className="flex flex-col space-y-2">
                        <div className="flex bg-gray-50 dark:bg-gray-700 rounded-lg p-1">
                            <button
                                onClick={() => handleWorkerTypeChange('shift')}
                                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors border-2 ${state.config.workerType === 'shift'
                                    ? 'bg-blue-500 text-white border-blue-600'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent'
                                    }`}
                            >
                                Shift Worker
                            </button>
                            <button
                                onClick={() => handleWorkerTypeChange('day')}
                                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors border-2 ${state.config.workerType === 'day'
                                    ? 'bg-blue-500 text-white border-blue-600'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent'
                                    }`}
                            >
                                Day Worker
                            </button>
                        </div>
                        <button
                            onClick={() => setShowRules(!showRules)}
                            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors border-2
                                ${showRules
                                    ? 'bg-green-500 text-white border-green-600'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent'
                                }`}
                        >
                            {showRules ? 'Hide Rules' : 'Show Rules'}
                        </button>
                    </div>
                </div>
            </div>
            {showRules && renderRules()}
        </div>
    );
}