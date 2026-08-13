import React, { useState } from 'react';
import { usePay } from '../../context/PayContext';

export default function ShiftTimeInput({ renderRow }) {
    const { state, dispatch } = usePay();
    const [timeDrafts, setTimeDrafts] = useState({});
    const draftKey = (shift, field) => `${shift.id ?? `${shift.week}-${shift.day}`}-${field}`;

    const resetCalculationsIfEmpty = (newShifts) => {
        const allShiftsEmpty = newShifts.every(shift => !shift.start || !shift.end);
        if (allShiftsEmpty) {
            dispatch({
                type: 'UPDATE_CALCULATIONS',
                payload: {
                    calculations: { ordinaryHours: 0, overtimeHours: 0, totalHours: 0, dailyBreakdown: {} },
                    payments: { ordinaryPay: 0, overtimePay: 0, penaltyPay: 0, totalPay: 0 }
                }
            });
        }
    };

    const handleShiftChange = (idx, field, value) => {
        const newShifts = [...state.shifts];
        newShifts[idx] = {
            ...newShifts[idx],
            [field]: value
        };

        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: newShifts
        });
        resetCalculationsIfEmpty(newShifts);
    };

    const togglePublicHoliday = (idx) => {
        const shift = state.shifts[idx];
        handleShiftChange(idx, 'public_holiday', !shift.public_holiday);
    };

    const formatTimeDisplay = (value) => {
        if (!value && value !== 0) return '';
        const decimalHours = Number.parseFloat(value);
        if (Number.isNaN(decimalHours)) return '';
        const totalMinutes = Math.round((decimalHours % 24) * 60);
        const hours = Math.floor(totalMinutes / 60) % 24;
        const minutes = totalMinutes % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    };

    const timeValueAsDecimal = (value) => {
        if (value === '' || value === null || value === undefined) return null;
        const match = /^(\d{1,2}):(\d{2})$/.exec(value.toString().trim());
        if (match) {
            const hours = Number.parseInt(match[1], 10);
            const minutes = Number.parseInt(match[2], 10);
            return hours <= 23 && minutes <= 59 ? hours + (minutes / 60) : null;
        }
        const decimal = Number.parseFloat(value);
        return Number.isFinite(decimal) ? decimal : null;
    };

    const parseTimeInput = (value, currentValue) => {
        const input = value.trim();
        const clockMatch = /^(\d{1,2}):(\d{2})$/.exec(input);
        const hourMatch = /^(\d{1,2})$/.exec(input);
        // A dot is accepted as a quick time separator: 3.5 means 03:50,
        // while 3.25 means 03:25.
        const dotMatch = /^(\d{1,2})\.(\d{1,2})$/.exec(input);
        if (!clockMatch && !hourMatch && !dotMatch) return null;

        const hours = Number.parseInt((clockMatch || hourMatch || dotMatch)[1], 10);
        const minutes = clockMatch
            ? Number.parseInt(clockMatch[2], 10)
            : dotMatch
                ? Number.parseInt(dotMatch[2].padEnd(2, '0'), 10)
                : 0;
        if (hours > 23 || minutes > 59) return null;

        let decimalHours = hours + (minutes / 60);
        // Retain an explicitly selected next-day value when editing it.
        if (Number.parseFloat(currentValue) >= 24) decimalHours += 24;
        return decimalHours.toString();
    };

    const commitTimeInput = (idx, field, value) => {
        const shift = state.shifts[idx];
        const parsedValue = parseTimeInput(value, timeValueAsDecimal(shift[field]));
        setTimeDrafts((drafts) => {
            const next = { ...drafts };
            delete next[draftKey(shift, field)];
            return next;
        });
        if (parsedValue !== null) {
            handleShiftChange(idx, field, parsedValue);
        }
    };

    const handleTimeChange = (idx, field, value, isInput = false) => {
        let newValue;
        const shift = state.shifts[idx];

        if (field === 'break_duration') {
            newValue = value === '' ? shift.break_duration :
                Math.max(0, Math.min(24, parseFloat(value) || 0)).toString();
        } else if (!isInput) {
            const currentValue = timeValueAsDecimal(
                timeDrafts[draftKey(shift, field)] ?? shift[field]
            );
            if (value === 'increment') {
                if (!currentValue && currentValue !== 0) {
                    // Field is blank, try to get previous day's value
                    if (idx > 0) {
                        const prevValue = timeValueAsDecimal(state.shifts[idx - 1][field]);
                        newValue = (Number.isFinite(prevValue) ? prevValue : (field === 'end' ? 17 : 9)).toString();
                    } else {
                        newValue = field === 'end' ? '17' : '9'; // Default to 17 for end time, 9 for start time
                    }
                } else {
                    newValue = Math.min(47, currentValue + 0.25).toString();
                }
            } else if (value === 'decrement') {
                newValue = Math.max(0, (currentValue || 0) - 0.25).toString();
            }
        }
        handleShiftChange(idx, field, newValue);
    };

    const clearDay = (idx) => {
        const newShifts = [...state.shifts];
        newShifts[idx] = {
            ...newShifts[idx],
            start: '',
            end: '',
            break_duration: state.config.workerType === 'shift' ? '0' : '0.5',
            lunch_start: ''
        };

        dispatch({
            type: 'UPDATE_SHIFTS',
            payload: newShifts
        });
        resetCalculationsIfEmpty(newShifts);
    };

    const addShift = (shift) => {
        const sameDay = state.shifts.filter((item) => item.week === shift.week && item.day === shift.day);
        const newShift = {
            id: `shift-${shift.week}-${shift.day}-${Date.now()}-${sameDay.length}`,
            week: shift.week,
            day: shift.day,
            isPrimary: false,
            start: '',
            end: '',
            break_duration: state.config.workerType === 'shift' ? '0' : '0.5',
            lunch_start: '',
        };
        const index = state.shifts.findIndex((item) => item.id === shift.id);
        const insertAfter = state.shifts.findLastIndex(
            (item) => item.week === shift.week && item.day === shift.day
        );
        const targetIndex = insertAfter >= 0 ? insertAfter : index;
        const newShifts = [...state.shifts];
        newShifts.splice(targetIndex + 1, 0, newShift);
        dispatch({ type: 'UPDATE_SHIFTS', payload: newShifts });
    };

    const removeShift = (idx) => {
        const newShifts = state.shifts.filter((_, index) => index !== idx);
        dispatch({ type: 'UPDATE_SHIFTS', payload: newShifts });
        resetCalculationsIfEmpty(newShifts);
    };

    const copyPreviousDay = (shift) => {
        const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const currentDayIndex = dayOrder.indexOf(shift.day);
        if (currentDayIndex === 0 && shift.week === 1) {
            return;
        }

        const previousDay = currentDayIndex === 0 ? 'Sunday' : dayOrder[currentDayIndex - 1];
        const previousWeek = currentDayIndex === 0 ? shift.week - 1 : shift.week;
        const previousPeriods = state.shifts.filter(
            (item) => item.week === previousWeek && item.day === previousDay
        );
        const copiedPeriods = previousPeriods.map((item, index) => ({
            ...item,
            id: `shift-${shift.week}-${shift.day}-${Date.now()}-${index}`,
            day: shift.day,
            isPrimary: index === 0,
        }));
        const firstCurrentIndex = state.shifts.findIndex(
            (item) => item.week === shift.week && item.day === shift.day
        );
        const withoutCurrentDay = state.shifts.filter(
            (item) => item.week !== shift.week || item.day !== shift.day
        );
        withoutCurrentDay.splice(firstCurrentIndex, 0, ...copiedPeriods);
        dispatch({ type: 'UPDATE_SHIFTS', payload: withoutCurrentDay });
    };

    const renderShiftInputs = (shift, idx) => {
        const isPrimary = shift.isPrimary !== false;
        const startDraftKey = draftKey(shift, 'start');
        const endDraftKey = draftKey(shift, 'end');
        const lunchDraftKey = draftKey(shift, 'lunch_start');
        return (
            <>
                <td className="px-2 py-1 whitespace-nowrap text-sm font-medium text-gray-900">
                    {isPrimary ? `Week ${shift.week || 1} - ${shift.day}` : '↳ Additional shift'}
                </td>
                <td className="px-2 py-1 whitespace-nowrap">
                    <div className="flex items-center space-x-1">
                        <button aria-label={`Decrease ${shift.day} start time`} onClick={() => handleTimeChange(idx, 'start', 'decrement')} className="time-adjust">−</button>
                        <input
                            aria-label={`Week ${shift.week || 1} ${shift.day} ${isPrimary ? 'primary' : 'additional'} shift start`}
                            type="text"
                            value={timeDrafts[startDraftKey] ?? formatTimeDisplay(shift.start)}
                            onChange={(e) => setTimeDrafts((drafts) => ({ ...drafts, [startDraftKey]: e.target.value }))}
                            onBlur={(e) => commitTimeInput(idx, 'start', e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); }}
                            placeholder="HH:MM"
                            inputMode="numeric"
                            pattern="[0-2][0-9]:[0-5][0-9]"
                            className="shift-input text-center"
                        />
                        <button aria-label={`Increase ${shift.day} start time`} onClick={() => handleTimeChange(idx, 'start', 'increment')} className="time-adjust">+</button>
                    </div>
                </td>
                <td className="px-2 py-1 whitespace-nowrap">
                    <div className="flex items-center space-x-1">
                        <button aria-label={`Decrease ${shift.day} end time`} onClick={() => handleTimeChange(idx, 'end', 'decrement')} className="time-adjust">−</button>
                        <input
                            aria-label={`Week ${shift.week || 1} ${shift.day} ${isPrimary ? 'primary' : 'additional'} shift end`}
                            type="text"
                            value={timeDrafts[endDraftKey] ?? formatTimeDisplay(shift.end)}
                            onChange={(e) => setTimeDrafts((drafts) => ({ ...drafts, [endDraftKey]: e.target.value }))}
                            onBlur={(e) => commitTimeInput(idx, 'end', e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); }}
                            placeholder="HH:MM"
                            inputMode="numeric"
                            pattern="[0-2][0-9]:[0-5][0-9]"
                            className="shift-input text-center"
                        />
                        <button aria-label={`Increase ${shift.day} end time`} onClick={() => handleTimeChange(idx, 'end', 'increment')} className="time-adjust">+</button>
                    </div>
                </td>
                <td className="px-2 py-1 whitespace-nowrap">
                    <input
                        aria-label={`Week ${shift.week || 1} ${shift.day} ${isPrimary ? 'primary' : 'additional'} lunch start`}
                        type="text"
                        value={timeDrafts[lunchDraftKey] ?? formatTimeDisplay(shift.lunch_start)}
                        onChange={(e) => setTimeDrafts((drafts) => ({ ...drafts, [lunchDraftKey]: e.target.value }))}
                        onBlur={(e) => {
                            if (e.target.value.trim() === '') {
                                setTimeDrafts((drafts) => {
                                    const next = { ...drafts };
                                    delete next[lunchDraftKey];
                                    return next;
                                });
                                handleShiftChange(idx, 'lunch_start', '');
                            } else {
                                commitTimeInput(idx, 'lunch_start', e.target.value);
                            }
                        }}
                        onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); }}
                        placeholder="Optional"
                        inputMode="numeric"
                        pattern="[0-2][0-9]:[0-5][0-9]"
                        className="shift-input text-center"
                    />
                </td>
                <td className="px-2 py-1 whitespace-nowrap">
                    <div className="flex items-center space-x-1">
                        <input
                            aria-label={`Week ${shift.week || 1} ${shift.day} ${isPrimary ? 'primary' : 'additional'} unpaid break hours`}
                            type="number"
                            value={shift.break_duration}
                            onChange={(e) => handleTimeChange(idx, 'break_duration', e.target.value, true)}
                            className="shift-input text-center"
                            step="0.5"
                            min="0"
                            max="24"
                        />
                        <div className="flex space-x-1">
                            {isPrimary ? <>
                                <button onClick={() => clearDay(idx)} className="day-action ml-2" title="Clear times">Clear</button>
                                <button
                                    onClick={() => copyPreviousDay(shift)}
                                    className="day-action"
                                    title="Copy all shift periods from the previous day"
                                    disabled={shift.week === 1 && shift.day === 'Monday'}
                                >
                                    Copy Prev
                                </button>
                                <button onClick={() => addShift(shift)} className="day-action" title="Add another shift period">+ Add shift</button>
                            </> : <button onClick={() => removeShift(idx)} className="day-action ml-2" title="Remove this shift period">Remove</button>}
                        </div>
                    </div>
                </td>
                <td className="px-2 py-1 whitespace-nowrap text-center">
                    <input
                        aria-label={`Week ${shift.week || 1} ${shift.day} manual overtime`}
                        type="checkbox"
                        checked={Boolean(shift.manual_overtime)}
                        disabled={Boolean(shift.manual_ordinary)}
                        onChange={(event) => handleShiftChange(idx, 'manual_overtime', event.target.checked)}
                    />
                </td>
                <td className="px-2 py-1 whitespace-nowrap text-center">
                    <input
                        aria-label={`Week ${shift.week || 1} ${shift.day} manual ordinary`}
                        type="checkbox"
                        checked={Boolean(shift.manual_ordinary)}
                        disabled={Boolean(shift.manual_overtime)}
                        onChange={(event) => handleShiftChange(idx, 'manual_ordinary', event.target.checked)}
                    />
                </td>
                <td className="px-2 py-1 whitespace-nowrap text-center">
                    <input
                        aria-label={`Week ${shift.week || 1} ${shift.day} public holiday`}
                        type="checkbox"
                        checked={Boolean(shift.public_holiday)}
                        onChange={() => togglePublicHoliday(idx)}
                    />
                </td>
            </>
        );
    };

    return state.shifts.map((shift, idx) => renderRow(shift, idx, renderShiftInputs));
}
