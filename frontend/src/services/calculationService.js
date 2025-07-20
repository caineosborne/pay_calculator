export const calculatePay = async (hourlyRate, shifts) => {
    const payload = {
        hourly_rate: hourlyRate,
        shifts: shifts.map((s) => ({
            day: s.day,
            start: s.start ? parseInt(s.start) : null,
            end: s.end ? parseInt(s.end) : null,
        })),
    };

    try {
        const response = await fetch('http://localhost:8000/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            return await response.json();
        }
    } catch (err) {
        console.error('Auto-calc failed', err);
        throw err;
    }
};