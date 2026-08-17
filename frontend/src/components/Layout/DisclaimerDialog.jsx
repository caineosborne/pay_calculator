import React, { useEffect, useState } from 'react';
import { api } from '../../services/apis';
import { usePay } from '../../context/PayContext';

export function DisclaimerDialog({ isOpen, onClose }) {
    const { state } = usePay();
    const [disclaimers, setDisclaimers] = useState(null);
    const [loadError, setLoadError] = useState(false);

    useEffect(() => {
        let isMounted = true;

        api.getDisclaimers()
            .then((data) => {
                if (isMounted) {
                    setDisclaimers(data);
                }
            })
            .catch(() => {
                if (isMounted) {
                    setLoadError(true);
                }
            });

        return () => {
            isMounted = false;
        };
    }, []);

    if (!isOpen) {
        return null;
    }

    const generic = disclaimers?.generic;
    const awardDisclaimer = disclaimers?.awards?.[state.config.award];
    const hasGroupedExclusions = awardDisclaimer?.exclusion_groups?.some(
        (group) => group?.items?.length > 0
    );

    return (
        <div className="disclaimer-backdrop" role="presentation">
            <section
                className="disclaimer-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="disclaimer-dialog-title"
            >
                <h2 id="disclaimer-dialog-title">{generic?.title || 'Important disclaimer'}</h2>

                {generic?.paragraphs?.map((paragraph) => (
                    <p key={paragraph}>{paragraph}</p>
                ))}

                {awardDisclaimer && (
                    <div className="award-limitations">
                        <h3>{awardDisclaimer.title}</h3>
                        {awardDisclaimer.paragraphs?.map((paragraph) => (
                            <p key={paragraph}>{paragraph}</p>
                        ))}
                        {awardDisclaimer.assumptions?.length > 0 && (
                            <>
                                <h4>Assumptions</h4>
                                <ul>
                                    {awardDisclaimer.assumptions.map((assumption) => (
                                        <li key={assumption}>{assumption}</li>
                                    ))}
                                </ul>
                            </>
                        )}
                        {awardDisclaimer.limitations?.length > 0 && (
                            <>
                                <h4>Limitations</h4>
                                <ul>
                                    {awardDisclaimer.limitations.map((limitation) => (
                                        <li key={limitation}>{limitation}</li>
                                    ))}
                                </ul>
                            </>
                        )}
                        {hasGroupedExclusions && (
                            <>
                                <h4>Exclusions</h4>
                                {awardDisclaimer.exclusion_groups.map((group) => (
                                    group?.items?.length > 0 && (
                                        <section className="exclusion-group" key={group.title}>
                                            <h5>{group.title}</h5>
                                            <ul>
                                                {group.items.map((item) => (
                                                    <li key={item}>{item}</li>
                                                ))}
                                            </ul>
                                        </section>
                                    )
                                ))}
                            </>
                        )}
                        {!hasGroupedExclusions && awardDisclaimer.exclusions?.length > 0 && (
                            <>
                                <h4>Exclusions</h4>
                                <ul>
                                    {awardDisclaimer.exclusions.map((exclusion) => (
                                        <li key={exclusion}>{exclusion}</li>
                                    ))}
                                </ul>
                            </>
                        )}
                        {awardDisclaimer.closing_paragraphs?.map((paragraph) => (
                            <p key={paragraph}>{paragraph}</p>
                        ))}
                    </div>
                )}

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
