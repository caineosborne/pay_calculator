import React from 'react';
import Header from './Header';  // Make sure Header.jsx exists in the same folder

export function Layout({ children }) {
    return (
        <div className="pay-app">
            <Header />
            <div className="pay-shell">
                {children}
            </div>
        </div>
    );
}
