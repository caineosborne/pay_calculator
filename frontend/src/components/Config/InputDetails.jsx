import React, { useState, useEffect, useMemo, useRef } from 'react';
import { usePay } from '../../context/PayContext';
import { DisplayRules } from './DisplayRules';
import { RuleConfigurationEditor } from './RuleConfigurationEditor';
import { api } from '../../services/apis';
import { PUBLIC_AWARD_DEFAULT_RATES } from '../Layout/awardTabsData';

const FALLBACK_AWARD_DETAILS = {
    woolies_2024_demo: { label: 'Woolies EA 2024' },
    coles_2024: { label: 'Coles EA 2024' },
    fast_food: { label: 'Fast Food Award 2026' },
    gria_2026: { label: 'General Retail Industry Award 2026 (GRIA)' },
};

export function InputDetails() {
    const { state, dispatch } = usePay();
    const [showRules, setShowRules] = useState(false);
    const [showConfigurationEditor, setShowConfigurationEditor] = useState(false);
    const [awards, setAwards] = useState([]);
    const [rateOption, setRateOption] = useState('custom');
    const customRateSelected = useRef(false);
    const selectedAward = useMemo(() => awards.find(
        (award) => award.key === state.config.award
    ) || {
        key: state.config.award,
        ...FALLBACK_AWARD_DETAILS[state.config.award],
        hourly_rate_options: state.config.award === 'gria_2026'
            ? [{
                key: 'default',
                label: 'Base rate',
                hourly_rate: PUBLIC_AWARD_DEFAULT_RATES[state.config.award],
            }]
            : [],
    }, [awards, state.config.award]);
    const hourlyRateOptions = useMemo(
        () => selectedAward?.hourly_rate_options || [],
        [selectedAward]
    );

    // Keep handlers named when several controls share them or when one action
    // coordinates more than one state update.
    const handleWorkerTypeChange = (type) => {
        dispatch({
            type: 'UPDATE_WORKER_TYPE',
            payload: type
        });
        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: (state.shifts || []).map((shift) => ({
                ...shift,
                break_duration: type === 'shift' ? '0' : '0.5',
            })),
        });
    };

    const handleRateChange = (optionValue) => {
        setRateOption(optionValue);
        customRateSelected.current = optionValue === 'custom';
        const selectedRate = hourlyRateOptions.find(
            (option) => option.key === optionValue
        );

        if (selectedRate) {
            dispatch({
                type: 'UPDATE_HOURLY_RATE',
                payload: selectedRate.hourly_rate,
            });
        }
    };

    const handleEmploymentTypeChange = (type) => {
        dispatch({
            type: 'UPDATE_EMPLOYMENT_TYPE',
            payload: type
        });

        if (type === 'full_time' || type === 'casual') {
            dispatch({
                type: 'UPDATE_CONTRACTED_HOURS',
                payload: null
            });
        }
    };

    useEffect(() => {
        // Full-time contracted hours follow the active ruleset's period limit.
        if (state.config.employmentType === 'full_time') {
            const periodRule = state.calculations?.appliedRules?.weekly_overtime;
            const weeklyLimit = periodRule?.threshold
                ? Number(periodRule.threshold) / (periodRule.basis === 'pay_period' ? 2 : 1)
                : 38;

            dispatch({
                type: 'UPDATE_CONTRACTED_HOURS',
                payload: weeklyLimit
            });
        }
    }, [state.config.award, state.config.employmentType, state.calculations?.appliedRules, dispatch]);

    useEffect(() => {
        let isMounted = true;

        // Awards are registry data, so one request at mount is sufficient.
        const loadAwards = async () => {
            try {
                const awardOptions = await api.getAwards();
                if (!isMounted) {
                    return;
                }

                setAwards(awardOptions);
            } catch (error) {
                console.error('Failed to load awards:', error);
            }
        };

        loadAwards();

        return () => {
            isMounted = false;
        };
    }, [dispatch]);

    useEffect(() => {
        if (customRateSelected.current) {
            return;
        }
        const matchingRate = hourlyRateOptions.find(
            (option) => option.hourly_rate === Number(state.config.hourlyRate)
        );
        setRateOption(matchingRate?.key || 'custom');
    }, [hourlyRateOptions, state.config.hourlyRate]);

    return (
        <section className="config-panel panel" aria-label="Pay details">
            <div className="flex flex-col gap-4">
                <div className="config-primary-row flex items-center justify-between gap-4">
                    {/* Awards with published classifications select their configured rate. */}
                    <div className="flex-1">
                        {hourlyRateOptions.length > 0 ? (
                            <>
                                <label htmlFor="award-classification" className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                                    Classification and hourly rate
                                </label>
                                <select
                                    id="award-classification"
                                    value={rateOption}
                                    onChange={(event) => handleRateChange(event.target.value)}
                                    className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                >
                                    {hourlyRateOptions.map((option) => (
                                        <option key={option.key} value={option.key}>
                                            {option.label} — ${option.hourly_rate.toFixed(2)}/hr
                                        </option>
                                    ))}
                                    <option value="custom">Enter your own rate</option>
                                </select>
                                {rateOption === 'custom' && (
                                    <div className="mt-2">
                                        <label htmlFor="hourly-rate" className="sr-only">
                                            Your hourly rate ($)
                                        </label>
                                        <input
                                            id="hourly-rate"
                                            type="number"
                                            min="0"
                                            step="0.01"
                                            value={state.config.hourlyRate}
                                            onChange={(event) =>
                                                dispatch({
                                                    type: 'UPDATE_HOURLY_RATE',
                                                    payload: Number.parseFloat(event.target.value) || 0,
                                                })
                                            }
                                            className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                            placeholder="Enter hourly rate"
                                        />
                                    </div>
                                )}
                            </>
                        ) : (
                            <>
                                <label htmlFor="hourly-rate" className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                                    Hourly Rate ($)
                                </label>
                                <input
                                    id="hourly-rate"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={state.config.hourlyRate}
                                    onChange={(event) =>
                                        dispatch({
                                            type: 'UPDATE_HOURLY_RATE',
                                            payload: Number.parseFloat(event.target.value) || 0
                                        })
                                    }
                                    className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                />
                            </>
                        )}
                    </div>

                    <div className="award-lockup" aria-label="Selected award">
                        <span className="section-kicker">Selected award</span>
                        <strong>{selectedAward?.label || 'Loading rules'}</strong>
                        <span>Selected from the bar above</span>
                    </div>

                    {/* Worker type toggle section */}
                    <div className="worker-controls flex-shrink-0">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                            Worker Type
                        </label>
                        <div className="worker-control-stack">
                            <div className="worker-type-row bg-gray-50 dark:bg-gray-700 rounded-lg">
                                <button
                                    onClick={() => handleWorkerTypeChange('day')}
                                    className={`px-3 py-1 rounded-md text-xs font-medium transition-colors border-2 ${state.config.workerType === 'day'
                                        ? 'bg-blue-500 text-white border-blue-600'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent'
                                        }`}
                                >
                                    Day Worker
                                </button>
                                <button
                                    onClick={() => handleWorkerTypeChange('shift')}
                                    className={`px-3 py-1 rounded-md text-xs font-medium transition-colors border-2 ${state.config.workerType === 'shift'
                                        ? 'bg-blue-500 text-white border-blue-600'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent'
                                        }`}
                                >
                                    Shift Worker
                                </button>
                            </div>
                            <div className="control-button-row">
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
                                <button
                                    type="button"
                                    onClick={() => setShowConfigurationEditor(!showConfigurationEditor)}
                                    className="bg-gray-100 text-gray-700 hover:bg-gray-200"
                                >
                                    {showConfigurationEditor ? 'Close editor' : 'Edit'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Employment type and contracted hours section */}
                <div className="config-secondary-row flex items-center gap-4">
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

                    {/* Effective contracted hours input - only shown for part-time employees */}
                    {state.config.employmentType === 'part_time' && (
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                                Effective Contracted Hours per Week
                            </label>
                            <input
                                aria-label="Effective Contracted Hours per Week"
                                type="number"
                                value={state.config.contractedHours || ''}
                                onChange={(event) =>
                                    dispatch({
                                        type: 'UPDATE_CONTRACTED_HOURS',
                                        payload:
                                            Number.parseFloat(
                                                event.target.value
                                            ) || 0
                                    })
                                }
                                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                placeholder="Enter hours"
                                required
                            />
                        </div>
                    )}

                    {/* Display effective contracted hours for full-time */}
                    {state.config.employmentType === 'full_time' && (
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                                Effective Contracted Hours per Week
                            </label>
                            <div className="mt-1 py-2 px-3 bg-gray-100 dark:bg-gray-700 rounded-md text-gray-700 dark:text-gray-200">
                                {state.config.contractedHours || 38}
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
            {showConfigurationEditor && (
                <RuleConfigurationEditor
                    configurationId={state.config.ruleConfiguration}
                />
            )}
            <DisplayRules showRules={showRules} />
        </section>
    );
}
