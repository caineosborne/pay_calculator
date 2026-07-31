// Deliberately test-side math: it does not import production rules or services.
export const RATE = 30;

export function hours(shifts) {
  return shifts.reduce((total, shift) => {
    const end = shift.end > shift.start ? shift.end : shift.end + 24;
    return total + end - shift.start - (shift.break ?? 0);
  }, 0);
}

export function hospitalityShiftWorker(shifts, { dailyLimit = 10, periodLimit = 76 } = {}) {
  const days = new Map();
  for (const shift of shifts) {
    const key = `${shift.week ?? 1}-${shift.day}`;
    days.set(key, [...(days.get(key) ?? []), shift]);
  }
  const rows = [...days.entries()].map(([key, dayShifts]) => {
    const worked = hours(dayShifts);
    const ordinary = Math.min(worked, dailyLimit);
    return { key, day: dayShifts[0].day, worked, ordinary, overtime: worked - ordinary, shifts: dayShifts };
  });
  let excess = Math.max(0, rows.reduce((sum, row) => sum + row.ordinary, 0) - periodLimit);
  for (const row of [...rows].reverse()) {
    const moved = Math.min(row.ordinary, excess);
    row.ordinary -= moved;
    row.overtime += moved;
    excess -= moved;
  }
  const ordinary = rows.reduce((sum, row) => sum + row.ordinary, 0);
  const overtime = rows.reduce((sum, row) => sum + row.overtime, 0);
  const weekendLoading = rows.reduce((sum, row) => sum + row.ordinary * (row.day === 'Saturday' ? .25 : row.day === 'Sunday' ? .5 : 0), 0);
  const timeLoading = rows.reduce((sum, row) => sum + row.shifts.reduce((subtotal, shift) => {
    const end = shift.end > shift.start ? shift.end : shift.end + 24;
    const evening = Math.max(0, Math.min(end, 24) - Math.max(shift.start, 19));
    const night = Math.max(0, Math.min(end, 31) - Math.max(shift.start, 24));
    return subtotal + evening * .2 + night * .5;
  }, 0), 0);
  return {
    ordinary, overtime, penaltyPay: (weekendLoading + timeLoading) * RATE,
    gross: ordinary * RATE + overtime * RATE * 1.5 + (weekendLoading + timeLoading) * RATE,
    rows,
  };
}

export function partTimeTopUp(worked, contractedPerWeek) {
  const topup = Math.max(0, contractedPerWeek * 2 - worked);
  return { topup, gross: (worked + topup) * RATE };
}
