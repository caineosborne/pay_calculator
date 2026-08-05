const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const shiftId = (week, day, sequence = 1) => `shift-${week}-${day}-${sequence}`;

export const createShift = ({ week, day, sequence = 1, isPrimary = sequence === 1, start = '', end = '', break_duration = '0.5', manual_overtime = false, manual_ordinary = false }) => ({
    id: shiftId(week, day, sequence),
    week,
    day,
    isPrimary,
    start,
    end,
    break_duration,
    manual_overtime,
    manual_ordinary,
});

export const createFortnightShifts = (includeDefaultHours = false, includeSecondWeekDefault = false) => [1, 2].flatMap((week) =>
    WEEKDAYS.map((day, index) => createShift({
        week,
        day,
        start: includeDefaultHours && (week === 1 || includeSecondWeekDefault) && index < 5 ? '9' : '',
        end: includeDefaultHours && (week === 1 || includeSecondWeekDefault) && index < 5 ? '17' : '',
    }))
);

// The second week starts blank and can be populated with "Copy Previous Week".
export const initialShifts = createFortnightShifts(true);
