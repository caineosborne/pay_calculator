import React from 'react';
import Header from './Header';  // Make sure Header.jsx exists in the same folder

export function Layout({ children }) {
    return (
        <div className="min-h-screen bg-gray-50 py-2 px-4 sm:px-6 lg:px-8">
            <Header />
            <div className="w-full max-w-7xl mx-auto space-y-4">
                {children}
            </div>
        </div>
    );
}