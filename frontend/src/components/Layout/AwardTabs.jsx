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

    const selectAward = (awardKey) => {
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

    return (
        <nav className="award-tabs" aria-label="Choose an award calculator">
            <div className="award-tabs-inner">
                <div className="award-tabs-heading">
                    <p className="section-kicker">PayGuru calculators</p>
                    <p className="award-tabs-intro">Choose an award</p>
                </div>
                <div className="award-tab-list" role="tablist" aria-label="Award calculators">
                    {TAB_ORDER.map((tab) => (
                        <button
                            key={tab.key}
                            type="button"
                            role="tab"
                            aria-selected={state.config.award === tab.key}
                            className={`award-tab ${state.config.award === tab.key ? 'is-active' : ''}`}
                            onClick={() => selectAward(tab.key)}
                        >
                            {tab.label}
                        </button>
                    ))}
                    <button type="button" className="award-tab is-unavailable" disabled>
                        Customize <span>Coming soon</span>
                    </button>
                </div>
            </div>
        </nav>
    );
}
