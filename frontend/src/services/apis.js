// services/api.js
// Dynamically determine API URL based on environment
const BASE_URL = import.meta.env.PROD
    ? import.meta.env.VITE_API_URL // Uses the URL from .env.production
    : 'http://localhost:8000';

const responseJson = async (response, fallbackMessage) => {
    if (response.ok) {
        return await response.json();
    }
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || fallbackMessage);
};

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

    async getRuleConfigurations() {
        const response = await fetch(`${BASE_URL}/rule-configurations`);
        return responseJson(response, 'Failed to load rule configurations');
    },

    async getRuleConfiguration(configurationId) {
        const response = await fetch(
            `${BASE_URL}/rule-configurations/${encodeURIComponent(configurationId)}`
        );
        return responseJson(response, 'Failed to load rule source');
    },

    async validateRuleConfiguration(baseAward, source, questionnaire = null) {
        const response = await fetch(`${BASE_URL}/rule-configurations/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                base_award: baseAward,
                source,
                ...(questionnaire ? { questionnaire } : {}),
            }),
        });
        return responseJson(response, 'Rule source is invalid');
    },

    async createRuleConfiguration(
        baseAward,
        name,
        source,
        questionnaire = null
    ) {
        const response = await fetch(`${BASE_URL}/rule-configurations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                base_award: baseAward,
                name,
                source,
                ...(questionnaire ? { questionnaire } : {}),
            }),
        });
        return responseJson(response, 'Failed to save custom configuration');
    },

    async updateRuleConfiguration(
        configurationId,
        source,
        questionnaire = null
    ) {
        const response = await fetch(
            `${BASE_URL}/rule-configurations/${encodeURIComponent(configurationId)}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source,
                    ...(questionnaire ? { questionnaire } : {}),
                }),
            }
        );
        return responseJson(response, 'Failed to update custom configuration');
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
