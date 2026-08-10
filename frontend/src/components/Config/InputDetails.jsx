import React, { useState, useEffect, useMemo } from 'react';
import { usePay } from '../../context/PayContext';
import { DisplayRules } from './DisplayRules';
import { RuleConfigurationEditor } from './RuleConfigurationEditor';
import { api } from '../../services/apis';

export function InputDetails() {
    const { state, dispatch } = usePay();
    const [showRules, setShowRules] = useState(false);
    const [showConfigurationEditor, setShowConfigurationEditor] = useState(false);
    const [awards, setAwards] = useState([]);
    const [ruleConfigurations, setRuleConfigurations] = useState([]);
    const [rateOption, setRateOption] = useState('custom');
    const defaultAward = awards.find((award) => award.default)?.key || 'fast_food';
    const selectedAward = awards.find(
        (award) => award.key === state.config.award
    );
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
    };

    const handleAwardChange = (award) => {
        dispatch({
            type: 'UPDATE_AWARD',
            payload: award
        });
        dispatch({
            type: 'UPDATE_RULE_CONFIGURATION',
            payload: `builtin:${award}`
        });

        const defaultRate = awards.find(
            (awardOption) => awardOption.key === award
        )?.hourly_rate_options?.[0];
        if (defaultRate) {
            setRateOption(defaultRate.key);
            dispatch({
                type: 'UPDATE_HOURLY_RATE',
                payload: defaultRate.hourly_rate,
            });
        } else {
            setRateOption('custom');
        }
    };

    const handleRateChange = (optionValue) => {
        setRateOption(optionValue);
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

    const handleRuleConfigurationChange = (configurationId) => {
        dispatch({
            type: 'UPDATE_RULE_CONFIGURATION',
            payload: configurationId
        });
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
        if (
            awards.length > 0 &&
            !awards.some((award) => award.key === state.config.award)
        ) {
            dispatch({
                type: 'UPDATE_AWARD',
                payload:
                    awards.find((award) => award.default)?.key ||
                    awards[0].key
            });
        }
    }, [awards, dispatch, state.config.award]);

    useEffect(() => {
        const matchingRate = hourlyRateOptions.find(
            (option) => option.hourly_rate === Number(state.config.hourlyRate)
        );
        setRateOption(matchingRate?.key || 'custom');
    }, [hourlyRateOptions, state.config.hourlyRate]);

    const refreshRuleConfigurations = async () => {
        const configurations = await api.getRuleConfigurations();
        setRuleConfigurations(configurations);
        return configurations;
    };

    useEffect(() => {
        refreshRuleConfigurations().catch((error) => {
            console.error('Failed to load rule configurations:', error);
        });
    }, []);

    useEffect(() => {
        if (!ruleConfigurations.length) {
            return;
        }
        const selectedConfiguration = ruleConfigurations.find(
            (configuration) =>
                configuration.id === state.config.ruleConfiguration
        );
        if (
            !selectedConfiguration ||
            selectedConfiguration.base_award !== state.config.award
        ) {
            dispatch({
                type: 'UPDATE_RULE_CONFIGURATION',
                payload: `builtin:${state.config.award}`
            });
        }
    }, [
        dispatch,
        ruleConfigurations,
        state.config.award,
        state.config.ruleConfiguration,
    ]);

    const handleConfigurationSaved = async (savedConfiguration) => {
        await refreshRuleConfigurations();
        handleRuleConfigurationChange(savedConfiguration.id);
        dispatch({ type: 'REFRESH_CALCULATION' });
    };

    const awardRuleConfigurations = ruleConfigurations.filter(
        (configuration) =>
            configuration.base_award === state.config.award
    );

    return (
        <section className="config-panel panel" aria-label="Pay details">
            <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between gap-4">
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

                    {/* Award selection dropdown */}
                    <div className="flex-1">
                        <label htmlFor="award" className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                            Award
                        </label>
                        <select
                            id="award"
                            value={state.config.award || defaultAward}
                            onChange={(e) => handleAwardChange(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
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

                <div className="flex items-end gap-4">
                    <div className="flex-1">
                        <label htmlFor="rule-configuration" className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                            Rule Configuration
                        </label>
                        <select
                            id="rule-configuration"
                            value={
                                state.config.ruleConfiguration ||
                                `builtin:${state.config.award}`
                            }
                            onChange={(event) =>
                                handleRuleConfigurationChange(event.target.value)
                            }
                            className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                            {awardRuleConfigurations.map((configuration) => (
                                <option
                                    key={configuration.id}
                                    value={configuration.id}
                                >
                                    {configuration.kind === 'custom'
                                        ? `Custom: ${configuration.name}`
                                        : `Built-in: ${configuration.name}`}
                                </option>
                            ))}
                        </select>
                    </div>
                    <button
                        type="button"
                        onClick={() =>
                            setShowConfigurationEditor(
                                !showConfigurationEditor
                            )
                        }
                        className="bg-gray-100 text-gray-700 hover:bg-gray-200"
                    >
                        {showConfigurationEditor
                            ? 'Close rule editor'
                            : 'Edit rule configuration'}
                    </button>
                </div>
            </div>
            {showConfigurationEditor && (
                <RuleConfigurationEditor
                    configurationId={state.config.ruleConfiguration}
                    onConfigurationSaved={handleConfigurationSaved}
                />
            )}
            <DisplayRules showRules={showRules} />
        </section>
    );
}
