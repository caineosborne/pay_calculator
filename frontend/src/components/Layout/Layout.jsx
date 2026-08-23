import React, { useState } from 'react';
import Header from './Header';  // Make sure Header.jsx exists in the same folder
import { DisclaimerDialog, DisclaimerFooter } from './DisclaimerDialog';
import { AwardTabs } from './AwardTabs';

export function Layout({ children }) {
    const [disclaimerMode, setDisclaimerMode] = useState('general');

    return (
        <div className="pay-app">
            <AwardTabs />
            <Header onOpenLimitations={() => setDisclaimerMode('full')} />
            <div className="pay-shell">
                {children}
            </div>
            <DisclaimerFooter />
            <DisclaimerDialog
                isOpen={Boolean(disclaimerMode)}
                showAwardDetails={disclaimerMode === 'full'}
                onClose={() => setDisclaimerMode(null)}
            />
        </div>
    );
}
