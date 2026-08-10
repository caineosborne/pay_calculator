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

    return (
        <div className="disclaimer-backdrop" role="presentation">
            <section
                className="disclaimer-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="disclaimer-dialog-title"
            >
                <p className="section-kicker">Before you use this calculator</p>
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
                        {awardDisclaimer.limitations?.length > 0 && (
                            <ul>
                                {awardDisclaimer.limitations.map((limitation) => (
                                    <li key={limitation}>{limitation}</li>
                                ))}
                            </ul>
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
