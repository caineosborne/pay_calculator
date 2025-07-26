// services/api.js
// Dynamically determine API URL based on environment
const BASE_URL = import.meta.env.PROD
    ? 'https://pay-calculator-api.onrender.com' // Replace with your actual backend URL on Render
    : 'http://localhost:8000';

export const api = {
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