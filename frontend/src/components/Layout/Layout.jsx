import React, { useState } from 'react';
import Header from './Header';  // Make sure Header.jsx exists in the same folder
import { DisclaimerDialog } from './DisclaimerDialog';

export function Layout({ children }) {
    const [isDisclaimerOpen, setIsDisclaimerOpen] = useState(true);

    return (
        <div className="pay-app">
            <Header onOpenLimitations={() => setIsDisclaimerOpen(true)} />
            <div className="pay-shell">
                {children}
            </div>
            <DisclaimerDialog
                isOpen={isDisclaimerOpen}
                onClose={() => setIsDisclaimerOpen(false)}
            />
        </div>
    );
}
