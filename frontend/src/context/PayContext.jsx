// context/PayContext.jsx
import React, { createContext, useContext, useReducer } from 'react';
import { initialShifts } from '../components/Config/shifts';

const PayContext = createContext();
const defaultAward = 'hospitality';

const initialState = {
    config: {
        hourlyRate: 20, // Set default to 20
        workerType: 'shift', // Default to shift worker ('shift' or 'day')
        award: defaultAward, // Default to the configured award
        employmentType: 'full_time', // Default to Full Time ('full_time', 'part_time', 'casual')
        contractedHours: null, // Default to null, will be set based on rules for part-time
    },
    shifts: initialShifts,
    calculations: {
        ordinaryHours: 0,
        overtimeHours: 0,
        totalHours: 0,
        appliedRules: null
    },
    payments: {
        ordinaryPay: 0,
        overtimePay: 0,
        penaltyPay: 0,
        totalPay: 0
    }
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
                shifts: action.payload
            };
        case 'UPDATE_CALCULATIONS':
            return {
                ...state,
                calculations: action.payload.calculations,
                payments: action.payload.payments
            };
        default:
            return state;
    }
}

export function PayProvider({ children }) {
    const [state, dispatch] = useReducer(payReducer, initialState);

    return (
        <PayContext.Provider value={{ state, dispatch }}>
            {children}
        </PayContext.Provider>
    );
}

export const usePay = () => useContext(PayContext);
