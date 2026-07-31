/**
 * InputDetails Component
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
import React, { useState, useEffect } from 'react';
import { usePay } from '../../context/PayContext';
import { DisplayRules } from './DisplayRules';
import { api } from '../../services/apis';

export function InputDetails() {
    // Access global state and dispatch from PayContext
    // state.config.hourlyRate: current hourly rate
    // state.config.workerType: current worker type
    // dispatch: function to update hourly rate and worker type
    const { state, dispatch } = usePay();
    const [showRules, setShowRules] = useState(false);
    const [awards, setAwards] = useState([]);

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

    /**
     * Handles changes to the award selection dropdown.
     * Dispatches UPDATE_AWARD to PayContext, updating global state.
     * @param {string} award - Selected award key
     */
    const handleAwardChange = (award) => {
        dispatch({
            type: 'UPDATE_AWARD',
            payload: award
        });
    };

    /**
     * Handles changes to the employment type selection.
     * Dispatches UPDATE_EMPLOYMENT_TYPE to PayContext, updating global state.
     * @param {string} type - Employment type: 'full_time', 'part_time', 'casual'
     */
    const handleEmploymentTypeChange = (type) => {
        dispatch({
            type: 'UPDATE_EMPLOYMENT_TYPE',
            payload: type
        });

        // If changing to full_time or casual, reset contracted hours to null
        if (type === 'full_time' || type === 'casual') {
            dispatch({
                type: 'UPDATE_CONTRACTED_HOURS',
                payload: null
            });
        }
    };

    /**
     * Handles changes to the contracted hours input field.
     * Dispatches UPDATE_CONTRACTED_HOURS to PayContext, updating global state.
     * @param {string|number} value - New contracted hours entered by user
     */
    const handleContractedHoursChange = (value) => {
        dispatch({
            type: 'UPDATE_CONTRACTED_HOURS',
            payload: parseFloat(value) || 0
        });
    };

    // Effect to update contracted hours when award or employment type changes
    useEffect(() => {
        // For full-time employees, set contracted hours to the weekly overtime limit
        if (state.config.employmentType === 'full_time') {
            const weeklyLimit = state.calculations?.appliedRules?.weekly_overtime?.threshold ||
                (state.config.award === 'aged_care' ? 40 : 38);

            dispatch({
                type: 'UPDATE_CONTRACTED_HOURS',
                payload: weeklyLimit
            });
        }
    }, [state.config.award, state.config.employmentType, state.calculations?.appliedRules, dispatch]);

    useEffect(() => {
        let isMounted = true;

        const loadAwards = async () => {
            try {
                const awardOptions = await api.getAwards();
                if (!isMounted) {
                    return;
                }

                setAwards(awardOptions);

                const currentAwardExists = awardOptions.some(
                    (award) => award.key === state.config.award
                );
                if (!currentAwardExists && state.config.award !== null) {
                    dispatch({ type: 'UPDATE_AWARD', payload: null });
                }
            } catch (error) {
                console.error('Failed to load awards:', error);
            }
        };

        loadAwards();

        return () => {
            isMounted = false;
        };
    }, [dispatch]);

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3">
            <div className="flex flex-col gap-4">
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

                    {/* Award selection dropdown */}
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                            Award
                        </label>
                        <select
                            value={state.config.award || ''}
                            onChange={(e) => handleAwardChange(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                            <option value="" disabled>Select an award</option>
                            {awards.map((award) => (
                                <option key={award.key} value={award.key}>
                                    {award.label}
                                </option>
                            ))}
                        </select>
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

                {/* Employment type and contracted hours section */}
                <div className="flex items-center gap-4">
                    {/* Employment type selection */}
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                            Employment Type
                        </label>
                        <div className="mt-1 flex bg-gray-50 dark:bg-gray-700 rounded-lg p-1">
                            <button
                                onClick={() => handleEmploymentTypeChange('full_time')}
                                className={`flex-1 px-3 py-1 rounded-md text-xs font-medium transition-colors border-2 ${state.config.employmentType === 'full_time'
                                    ? 'bg-blue-500 text-white border-blue-600'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent'
                                    }`}
                            >
                                Full Time
                            </button>
                            <button
                                onClick={() => handleEmploymentTypeChange('part_time')}
                                className={`flex-1 px-3 py-1 rounded-md text-xs font-medium transition-colors border-2 ${state.config.employmentType === 'part_time'
                                    ? 'bg-blue-500 text-white border-blue-600'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent'
                                    }`}
                            >
                                Part Time
                            </button>
                            <button
                                onClick={() => handleEmploymentTypeChange('casual')}
                                className={`flex-1 px-3 py-1 rounded-md text-xs font-medium transition-colors border-2 ${state.config.employmentType === 'casual'
                                    ? 'bg-blue-500 text-white border-blue-600'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent'
                                    }`}
                            >
                                Casual
                            </button>
                        </div>
                    </div>

                    {/* Contracted hours input - only shown for part-time employees */}
                    {state.config.employmentType === 'part_time' && (
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                                Contracted Hours per Week
                            </label>
                            <input
                                type="number"
                                value={state.config.contractedHours || ''}
                                onChange={(e) => handleContractedHoursChange(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                placeholder="Enter hours"
                                required
                            />
                        </div>
                    )}

                    {/* Display selected contracted hours for full-time */}
                    {state.config.employmentType === 'full_time' && (
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                                Contracted Hours per Week
                            </label>
                            <div className="mt-1 py-2 px-3 bg-gray-100 dark:bg-gray-700 rounded-md text-gray-700 dark:text-gray-200">
                                {state.config.contractedHours ||
                                    (state.config.award === 'aged_care' ? 40 : 38)}
                            </div>
                        </div>
                    )}

                    {/* Spacer for casual workers */}
                    {state.config.employmentType === 'casual' && (
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                                Contracted Hours per Week
                            </label>
                            <div className="mt-1 py-2 px-3 bg-gray-100 dark:bg-gray-700 rounded-md text-gray-700 dark:text-gray-200">
                                Not applicable for casual workers
                            </div>
                        </div>
                    )}
                </div>
            </div>
            <DisplayRules showRules={showRules} />
        </div>
    );
}
