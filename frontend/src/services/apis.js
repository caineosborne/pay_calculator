// services/api.js
const BASE_URL = 'http://localhost:8000';

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