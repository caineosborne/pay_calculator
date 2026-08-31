import React, { useEffect, useState } from 'react';
import { api } from '../../services/apis';
import { usePay } from '../../context/PayContext';

function useDisclaimers() {
    const [disclaimers, setDisclaimers] = useState(null);
    const [loadError, setLoadError] = useState(false);

    useEffect(() => {
        let isMounted = true;
        api.getDisclaimers()
            .then((data) => isMounted && setDisclaimers(data))
            .catch(() => isMounted && setLoadError(true));
        return () => { isMounted = false; };
    }, []);

    return { disclaimers, loadError };
}

function DisclaimerContent({ disclaimers, awardKey, showAwardDetails = true, titleId }) {
    const generic = disclaimers?.generic;
    const awardDisclaimer = disclaimers?.awards?.[awardKey];
    const hasGroupedExclusions = awardDisclaimer?.exclusion_groups?.some(
        (group) => group?.items?.length > 0
    );

    return (
        <>
            <h2 id={titleId}>{generic?.title || 'Before you use this calculator'}</h2>
            {generic?.paragraphs?.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}

            {showAwardDetails && awardDisclaimer && (
                <div className="award-limitations">
                    <h3 className="award-specific-heading">
                        Specific commentary on this award/EA
                    </h3>
                    <div className="total-review-callout" role="note">
                        <strong>How the total is calculated</strong>
                        <span>All calculations are based on the assumptions and limitations specified below. Exclusions may mean additional amounts are payable.</span>
                    </div>
                    <h3>{awardDisclaimer.title}</h3>
                    {awardDisclaimer.paragraphs?.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
                    {awardDisclaimer.assumptions?.length > 0 && (
                        <section className="disclaimer-section disclaimer-assumptions">
                            <h4>Assumptions</h4>
                            <ul>{awardDisclaimer.assumptions.map((item) => <li key={item}>{item}</li>)}</ul>
                        </section>
                    )}
                    {awardDisclaimer.limitations?.length > 0 && (
                        <section className="disclaimer-section disclaimer-limitations">
                            <h4>Limitations</h4>
                            <ul>{awardDisclaimer.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
                        </section>
                    )}
                    {hasGroupedExclusions ? (
                        <section className="disclaimer-section disclaimer-exclusions">
                            <h4>Exclusions</h4>
                            {awardDisclaimer.exclusion_intro?.map((paragraph) => (
                                <p className="exclusion-intro" key={paragraph}>{paragraph}</p>
                            ))}
                            {awardDisclaimer.exclusion_groups.map((group) => group?.items?.length > 0 && (
                                <section className="exclusion-group" key={group.title}>
                                    <h5>{group.title}</h5>
                                    <ul>{group.items.map((item) => <li key={item}>{item}</li>)}</ul>
                                </section>
                            ))}
                        </section>
                    ) : awardDisclaimer.exclusions?.length > 0 && (
                        <section className="disclaimer-section disclaimer-exclusions">
                            <h4>Exclusions</h4>
                            {awardDisclaimer.exclusion_intro?.map((paragraph) => (
                                <p className="exclusion-intro" key={paragraph}>{paragraph}</p>
                            ))}
                            <ul>{awardDisclaimer.exclusions.map((item) => <li key={item}>{item}</li>)}</ul>
                        </section>
                    )}
                    {awardDisclaimer.closing_paragraphs?.map((paragraph) => (
                        <p className="disclaimer-closing" key={paragraph}>{paragraph}</p>
                    ))}
                </div>
            )}
        </>
    );
}

export function DisclaimerDialog({ isOpen, onClose, showAwardDetails = true }) {
    const { state } = usePay();
    const { disclaimers, loadError } = useDisclaimers();

    if (!isOpen) {
        return null;
    }

    return (
        <div className="disclaimer-backdrop" role="presentation">
            <section
                className="disclaimer-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="disclaimer-dialog-title"
            >
                <DisclaimerContent disclaimers={disclaimers} awardKey={state.config.award} showAwardDetails={showAwardDetails} titleId="disclaimer-dialog-title" />

                {loadError && (
                    <p className="disclaimer-error" role="alert">
                        The limitations notice could not be loaded. Please refresh before relying on this estimate.
                    </p>
                )}

                <button className="pay-button disclaimer-close" onClick={onClose} autoFocus>
                    I understand
                </button>
            </section>
        </div>
    );
}

export function DisclaimerFooter() {
    const { state } = usePay();
    const { disclaimers, loadError } = useDisclaimers();

    return (
        <footer className="disclaimer-footer pay-shell" aria-label="Disclaimer, assumptions and limitations">
            <DisclaimerContent disclaimers={disclaimers} awardKey={state.config.award} />
            {loadError && <p className="disclaimer-error" role="alert">The limitations notice could not be loaded. Please refresh before relying on this estimate.</p>}
        </footer>
    );
}
