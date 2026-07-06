// services/api.js
// Dynamically determine API URL based on environment
const BASE_URL = import.meta.env.PROD
    ? import.meta.env.VITE_API_URL // Uses the URL from .env.production
    : 'http://localhost:8000';

export const api = {
    async getAwards() {
        try {
            const response = await fetch(`${BASE_URL}/awards`);

            if (!response.ok) throw new Error('Failed to load awards');
            return await response.json();
        } catch (error) {
            console.error('Awards API Error:', error);
            throw error;
        }
    },

    async calculatePay(payload) {
        try {
            const response = await fetch(`${BASE_URL}/calculate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error('Calculation failed');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
};
