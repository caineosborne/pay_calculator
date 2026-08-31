import React, { useEffect, useState } from 'react';
import { usePay } from '../../context/PayContext';
import { api } from '../../services/apis';
import { PUBLIC_AWARD_DEFAULT_RATES, TAB_ORDER } from './awardTabsData';

export function AwardTabs() {
    const { state, dispatch } = usePay();
    const [awards, setAwards] = useState([]);

    useEffect(() => {
        api.getAwards().then((loadedAwards) => {
            setAwards(loadedAwards);

            const params = new URLSearchParams(window.location.search);
            const requestedAward = params.get('award');
            if (TAB_ORDER.some((tab) => tab.key === requestedAward)) {
                const award = loadedAwards.find((item) => item.key === requestedAward);
                dispatch({
                    type: 'SELECT_AWARD',
                    payload: {
                        award: requestedAward,
                        hourlyRate: award?.hourly_rate_options?.[0]?.hourly_rate
                            ?? PUBLIC_AWARD_DEFAULT_RATES[requestedAward],
                    },
                });
            } else if (params.get('customize') === '1') {
                dispatch({ type: 'OPEN_CUSTOMIZE' });
            }
        }).catch(() => setAwards([]));
    }, [dispatch]);

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
        window.history.replaceState({}, '', `${window.location.pathname}?award=${encodeURIComponent(awardKey)}`);
    };

    const openCustomize = () => {
        if (!confirmDiscardRuleEdits()) {
            return;
        }
        dispatch({ type: 'OPEN_CUSTOMIZE' });
        window.history.replaceState({}, '', `${window.location.pathname}?customize=1`);
    };

    return (
        <nav className="award-tabs" aria-label="Choose an award calculator">
            <div className="site-notice" role="note">
                PayGuide.au Calculators — Independent tools for understanding your pay
            </div>
            <div className="award-tabs-inner">
                <div className="award-tabs-heading">
                    <p className="section-kicker">PayGuide.au Calculators</p>
                    <p className="award-tabs-intro">Choose your award</p>
                </div>
                <div className="award-tab-list" role="group" aria-label="Payguide pages and calculators">
                    <a className="award-tab topbar-about" href="/about.html">About</a>
                    {TAB_ORDER.map((tab) => (
                        <button
                            key={tab.key}
                            type="button"
                            aria-pressed={state.view !== 'customize' && state.config.award === tab.key}
                            className={`award-tab ${state.view !== 'customize' && state.config.award === tab.key ? 'is-active' : ''}`}
                            onClick={() => selectAward(tab.key)}
                        >
                            {tab.label}
                        </button>
                    ))}
                    <button
                        type="button"
                        aria-pressed={state.view === 'customize'}
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
