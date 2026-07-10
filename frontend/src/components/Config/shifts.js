const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const createWeek = (week, includeDefaultHours = false) => WEEKDAYS.map((day, index) => ({
    week,
    day,
    start: includeDefaultHours && index < 5 ? '9' : '',
    end: includeDefaultHours && index < 5 ? '17' : '',
    break_duration: '0.5'
}));

// The second week starts blank and can be populated with "Copy Previous Week".
export const initialShifts = [
    ...createWeek(1, true),
    ...createWeek(2)
];
