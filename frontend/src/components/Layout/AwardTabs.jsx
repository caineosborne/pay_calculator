import React, { useEffect, useState } from 'react';
import { usePay } from '../../context/PayContext';
import { api } from '../../services/apis';
import { PUBLIC_AWARD_DEFAULT_RATES, TAB_ORDER } from './awardTabsData';

export function AwardTabs() {
    const { state, dispatch } = usePay();
    const [awards, setAwards] = useState([]);

    useEffect(() => {
        api.getAwards().then(setAwards).catch(() => setAwards([]));
    }, []);

    const confirmDiscardRuleEdits = () => {
        if (!state.ruleEditorDirty) {
            return true;
        }
        if (!window.confirm('Discard unsaved rule changes?')) {
            return false;
        }
        dispatch({ type: 'SET_RULE_EDITOR_DIRTY', payload: false });
        return true;
    };

    const selectAward = (awardKey) => {
        if (!confirmDiscardRuleEdits()) {
            return;
        }
        const award = awards.find((item) => item.key === awardKey);
        const defaultRate = award?.hourly_rate_options?.[0] || {
            hourly_rate: PUBLIC_AWARD_DEFAULT_RATES[awardKey],
        };
        dispatch({
            type: 'SELECT_AWARD',
            payload: {
                award: awardKey,
                hourlyRate: defaultRate?.hourly_rate,
            },
        });
    };

    const openCustomize = () => {
        if (!confirmDiscardRuleEdits()) {
            return;
        }
        dispatch({ type: 'OPEN_CUSTOMIZE' });
    };

    return (
        <nav className="award-tabs" aria-label="Choose an award calculator">
            <div className="award-tabs-inner">
                <div className="award-tabs-heading">
                    <p className="section-kicker">payguide.au calculators</p>
                    <p className="award-tabs-intro">Choose an award</p>
                </div>
                <div className="award-tab-list" role="tablist" aria-label="Award calculators">
                    {TAB_ORDER.map((tab) => (
                        <button
                            key={tab.key}
                            type="button"
                            role="tab"
                            aria-selected={state.view !== 'customize' && state.config.award === tab.key}
                            className={`award-tab ${state.view !== 'customize' && state.config.award === tab.key ? 'is-active' : ''}`}
                            onClick={() => selectAward(tab.key)}
                        >
                            {tab.label}
                        </button>
                    ))}
                    <button
                        type="button"
                        role="tab"
                        aria-selected={state.view === 'customize'}
                        className={`award-tab ${state.view === 'customize' ? 'is-active' : ''}`}
                        onClick={openCustomize}
                    >
                        Create Custom Ruleset
                    </button>
                </div>
            </div>
        </nav>
    );
}
