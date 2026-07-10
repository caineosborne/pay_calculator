import React from 'react';
import { usePay } from '../../context/PayContext';

export function DisplayRules({ showRules }) {
    const { state } = usePay();

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

    // Format rule name to be more readable
    const formatRuleName = (ruleName) => {
        if (ruleName === 'weekly_overtime') return 'Fortnightly Overtime';
        return ruleName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    // Render rule content based on rule type
    const renderRuleContent = (ruleName, ruleData) => {
        // Safety check for null or undefined ruleData
        if (ruleData === null || ruleData === undefined) {
            return <span className="font-medium">Not available</span>;
        }

        // Handle span hours rule
        if (ruleName === 'span_hours') {
            if (!ruleData.threshold || !ruleData.rate) {
                return <span className="font-medium">Not specified</span>;
            }
            return (
                <span className="font-medium">
                    {ruleData.threshold === 'N/A'
                        ? 'N/A'
                        : `Overtime ${ruleData.threshold}, paid at ${ruleData.rate}`}
                </span>
            );
        }

        // Handle daily and weekly overtime rules
        if (ruleName === 'daily_overtime' || ruleName === 'weekly_overtime') {
            if (!ruleData.threshold || !ruleData.rate) {
                return <span className="font-medium">Not specified</span>;
            }

            // For weekly overtime, show additional part-time information if available
            if (ruleName === 'weekly_overtime' &&
                state.config.employmentType === 'part_time' &&
                state.calculations?.appliedRules?.use_contracted_hours_for_overtime) {
                return (
                    <span className="font-medium">
                        After {formatRuleValue(state.config.contractedHours || ruleData.threshold)}, paid at {ruleData.rate}
                        {' '}<span className="italic text-xs">(Using contracted hours)</span>
                    </span>
                );
            }

            return (
                <span className="font-medium">
                    After {formatRuleValue(ruleData.threshold)}, paid at {ruleData.rate}
                </span>
            );
        }

        // Handle day-specific rules (saturday, sunday, etc.)
        if (ruleName.includes('_rules') && ruleData.hasOwnProperty('is_overtime')) {
            if (ruleData.is_overtime) {
                return <span className="font-medium">All hours as overtime</span>;
            } else if (ruleData.penalty_rate) {
                return <span className="font-medium">Penalty rate {formatRuleValue(ruleData.penalty_rate)}</span>;
            } else {
                return <span className="font-medium">Not specified</span>;
            }
        }

        // Handle penalty rules
        if (ruleName.includes('penalty') || ruleName.includes('allowance')) {
            // Check if ruleData exists and has the expected properties
            const rateValue = ruleData?.rate || ruleData?.penalty_rate ||
                (typeof ruleData === 'string' || typeof ruleData === 'number' ? ruleData : null);

            if (rateValue !== null && rateValue !== undefined) {
                return (
                    <span className="font-medium">
                        {formatRuleValue(rateValue)}
                    </span>
                );
            } else {
                return (
                    <span className="font-medium">Not specified</span>
                );
            }
        }

        // Default rendering for other rules
        try {
            if (typeof ruleData === 'object' && ruleData !== null) {
                // Try to extract useful information from complex objects
                const simpleRepresentation = Object.entries(ruleData)
                    .filter(([key, value]) => value !== null && value !== undefined)
                    .map(([key, value]) => {
                        if (typeof value === 'boolean') {
                            return value ? key : `not ${key}`;
                        } else if (typeof value === 'string' || typeof value === 'number') {
                            return `${key}: ${value}`;
                        }
                        return null;
                    })
                    .filter(item => item !== null)
                    .join(', ');

                if (simpleRepresentation) {
                    return <span className="font-medium">{simpleRepresentation}</span>;
                }
            }

            // Fall back to string representation for simple values
            if (typeof ruleData === 'string' || typeof ruleData === 'number' || typeof ruleData === 'boolean') {
                return <span className="font-medium">{String(ruleData)}</span>;
            }

            // Last resort: JSON stringify
            return <span className="font-medium">{JSON.stringify(ruleData)}</span>;
        } catch (error) {
            return <span className="font-medium">Error displaying rule</span>;
        }
    };

    if (!showRules || !state.calculations?.appliedRules) return null;

    const rules = state.calculations.appliedRules;
    return (
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm">
            <h3 className="font-medium mb-2 text-gray-900 dark:text-gray-100">
                {state.config.workerType === 'shift' ? 'Shift Worker' : 'Day Worker'} Rules
                {state.config.employmentType && ` (${state.config.employmentType.replace('_', ' ')})`}
            </h3>
            <div className="space-y-2">
                {state.config.employmentType === 'part_time' && (
                    <div>
                        <span className="text-gray-600 dark:text-gray-300">Contracted Hours: </span>
                        <span className="font-medium">{state.config.contractedHours || 'Not specified'}</span>
                    </div>
                )}
                {Object.entries(rules).map(([ruleName, ruleData]) => (
                    <div key={ruleName}>
                        <span className="text-gray-600 dark:text-gray-300">{formatRuleName(ruleName)}: </span>
                        {renderRuleContent(ruleName, ruleData)}
                    </div>
                ))}
            </div>
        </div>
    );
}
