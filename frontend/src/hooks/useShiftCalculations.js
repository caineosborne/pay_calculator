// hooks/useShiftCalculations.js
import { useEffect } from 'react';
import { usePay } from '../context/PayContext';
import { api } from '../services/apis';

export function useShiftCalculations() {
    const { state, dispatch } = usePay();

    useEffect(() => {
        const calculatePay = async () => {
            try {
                const result = await api.calculatePay({
                    hourly_rate: state.config.hourlyRate,
                    shifts: state.shifts,
                });

                dispatch({ type: 'UPDATE_CALCULATIONS', payload: result });
            } catch (error) {
                dispatch({ type: 'SET_ERROR', payload: error.message });
            }
        };

        if (state.shifts.length > 0) {
            calculatePay();
        }
    }, [state.shifts, state.config.hourlyRate]);
}