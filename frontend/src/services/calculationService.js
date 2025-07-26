export const calculatePay = async (hourlyRate, shifts) => {
    const payload = {
        hourly_rate: hourlyRate,
        shifts: shifts.map((s) => ({
            day: s.day,
            start: s.start ? parseInt(s.start) : null,
            end: s.end ? parseInt(s.end) : null,
        })),
    };

    // Dynamically determine API URL based on environment
    const apiUrl = import.meta.env.PROD
        ? 'https://pay-calculator-api.onrender.com/calculate' // Replace with your actual backend URL on Render
        : 'http://localhost:8000/calculate';

    try {
        const response = await fetch(apiUrl, {
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