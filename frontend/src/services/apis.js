const BASE_URL = import.meta.env.PROD
    ? import.meta.env.VITE_API_URL
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
        const response = await fetch(`${BASE_URL}/awards`);
        return responseJson(response, 'Failed to load awards');
    },

    async getDisclaimers() {
        const response = await fetch(`${BASE_URL}/disclaimers`);
        return responseJson(response, 'Failed to load disclaimers');
    },

    async getRuleConfigurations() {
        const response = await fetch(`${BASE_URL}/rule-configurations`);
        return responseJson(response, 'Failed to load rule configurations');
    },

    async getRuleConfiguration(configurationId, options = {}) {
        const response = await fetch(
            `${BASE_URL}/rule-configurations/${encodeURIComponent(configurationId)}`,
            options
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

    async renameRuleConfiguration(configurationId, name) {
        const response = await fetch(
            `${BASE_URL}/rule-configurations/${encodeURIComponent(configurationId)}/name`,
            {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
            }
        );
        return responseJson(response, 'Failed to rename custom configuration');
    },

    async deleteRuleConfiguration(configurationId) {
        const response = await fetch(
            `${BASE_URL}/rule-configurations/${encodeURIComponent(configurationId)}`,
            { method: 'DELETE' }
        );
        if (response.ok) {
            return;
        }
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || 'Failed to delete custom configuration');
    },

    async calculatePay(payload, options = {}) {
        const response = await fetch(`${BASE_URL}/calculate`, {
            ...options,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return responseJson(response, 'Calculation failed');
    }
};
