// context/PayContext.jsx
import React, { createContext, useContext, useEffect, useReducer } from 'react';
import { initialShifts } from '../components/Config/shifts';

const PayContext = createContext();
const savedAward = typeof window !== 'undefined'
    ? window.localStorage.getItem('pay-checker.award')
    : null;
const liveAwards = new Set([
    'fast_food',
    'coles_2024',
    'gria_2026',
    'woolies_2024_demo',
]);
const defaultAward = liveAwards.has(savedAward) ? savedAward : 'fast_food';

const initialState = {
    config: {
        hourlyRate: 20, // Set default to 20
        workerType: 'shift', // Default to shift worker ('shift' or 'day')
        award: defaultAward, // Default to the configured award
        ruleConfiguration: `builtin:${defaultAward}`,
        employmentType: 'full_time', // Default to Full Time ('full_time', 'part_time', 'casual')
        contractedHours: null, // Default to null, will be set based on rules for part-time
    },
    shifts: initialShifts,
    publicHolidays: [],
    calculations: {
        ordinaryHours: 0,
        overtimeHours: 0,
        totalHours: 0,
        appliedRules: null
    },
    calculationRevision: 0,
    payments: {
        ordinaryPay: 0,
        overtimePay: 0,
        penaltyPay: 0,
        totalPay: 0
    },
    calculationError: null,
};


// Add debug logging to reducer
function payReducer(state, action) {
    // console.log('PayReducer:', { type: action.type, payload: action.payload });

    switch (action.type) {
        case 'UPDATE_HOURLY_RATE':
            return {
                ...state,
                config: {
                    ...state.config,
                    hourlyRate: action.payload
                }
            };
        case 'UPDATE_WORKER_TYPE':
            return {
                ...state,
                config: {
                    ...state.config,
                    workerType: action.payload
                }
            };
        case 'UPDATE_AWARD':
            return {
                ...state,
                config: {
                    ...state.config,
                    award: action.payload
                }
            };
        case 'UPDATE_RULE_CONFIGURATION':
            return {
                ...state,
                config: {
                    ...state.config,
                    ruleConfiguration: action.payload
                }
            };
        case 'UPDATE_EMPLOYMENT_TYPE':
            return {
                ...state,
                config: {
                    ...state.config,
                    employmentType: action.payload
                }
            };
        case 'UPDATE_CONTRACTED_HOURS':
            return {
                ...state,
                config: {
                    ...state.config,
                    contractedHours: action.payload
                }
            };
        case 'UPDATE_SHIFTS':
            return {
                ...state,
                shifts: action.payload,
                calculationError: null,
            };
        case 'UPDATE_PUBLIC_HOLIDAYS':
            return {
                ...state,
                publicHolidays: action.payload,
                calculationError: null,
            };
        case 'UPDATE_CALCULATIONS':
            return {
                ...state,
                calculations: action.payload.calculations,
                payments: action.payload.payments
            };
        case 'SET_CALCULATION_ERROR':
            return {
                ...state,
                calculationError: action.payload,
            };
        case 'REFRESH_CALCULATION':
            return {
                ...state,
                calculationRevision: state.calculationRevision + 1
            };
        default:
            return state;
    }
}

export function PayProvider({ children }) {
    const [state, dispatch] = useReducer(payReducer, initialState);

    useEffect(() => {
        window.localStorage.setItem('pay-checker.award', state.config.award);
    }, [state.config.award]);

    return (
        <PayContext.Provider value={{ state, dispatch }}>
            {children}
        </PayContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const usePay = () => useContext(PayContext);
