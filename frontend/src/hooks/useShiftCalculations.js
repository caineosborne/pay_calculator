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
                    worker_type: state.config.workerType,
                    award: state.config.award,
                    rule_configuration: state.config.ruleConfiguration,
                });

                dispatch({ type: 'UPDATE_CALCULATIONS', payload: result });
            } catch (error) {
                dispatch({ type: 'SET_ERROR', payload: error.message });
            }
        };

        if (state.shifts.length > 0) {
            calculatePay();
        }
    }, [
        dispatch,
        state.shifts,
        state.config.hourlyRate,
        state.config.workerType,
        state.config.award,
        state.config.ruleConfiguration,
    ]);
}
