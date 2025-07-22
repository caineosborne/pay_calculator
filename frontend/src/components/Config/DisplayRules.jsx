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

    if (!showRules || !state.calculations?.appliedRules) return null;

    const rules = state.calculations.appliedRules;
    return (
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm">
            <h3 className="font-medium mb-2 text-gray-900 dark:text-gray-100">
                {state.config.workerType === 'shift' ? 'Shift Worker' : 'Day Worker'} Rules
            </h3>
            <div className="space-y-2">
                {rules.span_hours && (
                    <div>
                        <span className="text-gray-600 dark:text-gray-300">Time of work overtime : </span>
                        <span className="font-medium">
                            {rules.span_hours.threshold === 'N/A'
                                ? 'N/A'
                                : `Overtime ${rules.span_hours.threshold}, paid at ${rules.span_hours.rate}`}
                        </span>
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
}
