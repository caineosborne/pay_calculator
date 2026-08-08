import { expect, test } from '@playwright/test';
import { RATE, hospitalityShiftWorker, partTimeTopUp } from './payroll-reference.js';

const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

function inputName(shift, field) {
  return `Week ${shift.week ?? 1} ${shift.day} ${shift.additional ? 'additional' : 'primary'} shift ${field}`;
}

async function openCalculator(page, { employment = 'casual' } = {}) {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Pay breakdown' })).toBeVisible();
  await page.getByLabel('Hourly Rate ($)').fill(String(RATE));
  if (employment === 'casual') await page.getByRole('button', { name: 'Casual' }).click();
  for (const week of [1, 2]) {
    for (const day of weekdays) {
      await page.getByRole('row', { name: new RegExp(`Week ${week} - ${day}`) }).getByTitle('Clear times').click();
    }
  }
}

async function enterShifts(page, shifts) {
  for (const shift of shifts) {
    if (shift.additional) {
      await page.getByRole('row', { name: new RegExp(`Week ${shift.week ?? 1} - ${shift.day}`) }).getByTitle('Add another shift period').click();
    }
    await page.getByLabel(inputName(shift, 'start')).fill(String(shift.start));
    await page.getByLabel(inputName(shift, 'end')).fill(String(shift.end));
    await page.getByLabel(`Week ${shift.week ?? 1} ${shift.day} ${shift.additional ? 'additional' : 'primary'} unpaid break hours`).fill(String(shift.break ?? 0));
  }
}

function money(value) {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency', currency: 'AUD', minimumFractionDigits: 2,
  }).format(value);
}

async function expectSummary(page, expected, context) {
  await expect(page.getByTestId('gross-pay'), context).toHaveText(money(expected.gross));
  await expect(page.getByTestId('ordinary-summary'), context).toContainText(`${expected.ordinary.toFixed(2)} hrs`);
  await expect(page.getByTestId('overtime-summary'), context).toContainText(`${expected.overtime.toFixed(2)} hrs`);
  if ('penaltyPay' in expected) await expect(page.getByTestId('penalty-summary'), context).toContainText(money(expected.penaltyPay));
}

const matrix = [
  {
    name: 'ordinary weekday 9–5 roster with unpaid lunches',
    shifts: weekdays.slice(0, 5).map((day) => ({ day, start: 9, end: 17, break: .5 })),
    applied: [],
  },
  {
    name: 'short shift plus a long shift above daily overtime',
    shifts: [{ day: 'Monday', start: 9, end: 12, break: .5 }, { day: 'Tuesday', start: 8, end: 19, break: .5 }],
    applied: ['Daily Overtime'],
  },
  {
    name: 'ten shifts that exceed the fortnightly ordinary limit',
    shifts: [1, 2].flatMap((week) => weekdays.slice(0, 5).map((day) => ({ week, day, start: 9, end: 17, break: 0 }))),
    applied: ['Period Overtime'],
  },
  {
    name: 'hospitality evening, Saturday and Sunday roster',
    shifts: [{ day: 'Friday', start: 18, end: 22, break: 0 }, { day: 'Saturday', start: 9, end: 17, break: 0 }, { day: 'Sunday', start: 9, end: 17, break: 0 }],
    applied: ['Evening Hours Penalty (20%)', 'Saturday Penalty (25%)', 'Sunday Penalty (50%)'],
  },
  {
    name: 'split hospitality shift with evening loading only on attended time',
    shifts: [{ day: 'Monday', start: 9, end: 12, break: 0 }, { day: 'Monday', additional: true, start: 17, end: 22, break: 0 }],
    applied: ['Evening Hours Penalty (20%)'],
  },
];

for (const scenario of matrix) {
  test(`payroll math: ${scenario.name}`, async ({ page }) => {
    await openCalculator(page);
    await enterShifts(page, scenario.shifts);
    const expected = hospitalityShiftWorker(scenario.shifts);
    const context = `\nshifts=${JSON.stringify(scenario.shifts)}\nexpected=${JSON.stringify(expected)}`;
    await expectSummary(page, expected, context);
    for (const rule of scenario.applied) await expect(page.getByText(rule, { exact: false }), context).toBeVisible();
  });
}

test('part-time contracted-hours top-up changes exactly when a shift is amended', async ({ page }) => {
  await openCalculator(page, { employment: 'full_time' });
  await page.getByRole('button', { name: 'Part Time' }).click();
  await page.getByLabel('Effective Contracted Hours per Week').fill('20');
  const shifts = [{ day: 'Monday', start: 9, end: 17, break: 0 }, { day: 'Tuesday', start: 9, end: 17, break: 0 }];
  await enterShifts(page, shifts);
  const initial = partTimeTopUp(16, 20);
  await expect(page.getByTestId('topup-summary')).toContainText(`${initial.topup.toFixed(2)} hrs`);
  await expect(page.getByTestId('gross-pay')).toHaveText(money(initial.gross));
  await page.getByLabel(inputName(shifts[1], 'end')).fill('19');
  const amended = partTimeTopUp(18, 20);
  await expect(page.getByTestId('topup-summary')).toContainText(`${amended.topup.toFixed(2)} hrs`);
  await expect(page.getByTestId('gross-pay')).toHaveText(money(amended.gross));
  await expect(page.getByText('Contracted Hours Top-up', { exact: false })).toBeVisible();
});

test('full-time top-up entitlement is disabled and re-enabled through a custom ruleset', async ({ page }) => {
  await openCalculator(page, { employment: 'full_time' });
  await page.getByRole('button', { name: 'Edit rule configuration' }).click();
  await page.getByLabel('New custom configuration name').fill('E2E full-time-topup-toggle');
  await page.getByLabel('Contracted-hours top-up for full-time employees').selectOption('false');
  await page.getByRole('button', { name: 'Save custom copy' }).click();
  await expect(page.getByLabel('Rule Configuration')).toHaveValue('custom:hospitality:e2e-full-time-topup-toggle');

  const shift = { day: 'Monday', start: 9, end: 17, break: 0 };
  await enterShifts(page, [shift]);
  await expect(page.getByTestId('topup-summary')).toContainText('0.00 hrs');
  await expect(page.getByTestId('gross-pay')).toHaveText(money(8 * RATE));
  await expect(page.getByText('Contracted Hours Top-up', { exact: true })).toHaveCount(0);

  await page.getByRole('button', { name: 'Close rule editor' }).click();
  await page.getByRole('button', { name: 'Edit rule configuration' }).click();
  await page.getByLabel('Contracted-hours top-up for full-time employees').selectOption('true');
  await page.getByRole('button', { name: 'Save changes' }).click();
  const enabled = partTimeTopUp(8, 38);
  await expect(page.getByTestId('topup-summary')).toContainText(`${enabled.topup.toFixed(2)} hrs`);
  await expect(page.getByTestId('gross-pay')).toHaveText(money(enabled.gross));
  await expect(page.getByText('Contracted Hours Top-up', { exact: true })).toBeVisible();
});

test('custom award mutation changes daily overtime threshold through the frontend', async ({ page }) => {
  await openCalculator(page);
  await page.getByRole('button', { name: 'Edit rule configuration' }).click();
  await page.getByLabel('New custom configuration name').fill('E2E daily-overtime-8');
  await page.getByLabel('Daily ordinary-hours limit Shift workers').fill('8');
  await page.getByRole('button', { name: 'Save custom copy' }).click();
  await expect(page.getByLabel('Rule Configuration')).toContainText('Custom: E2E Daily Overtime 8');
  const shift = { day: 'Monday', start: 8, end: 17, break: 0 };
  await enterShifts(page, [shift]);
  await expectSummary(page, hospitalityShiftWorker([shift], { dailyLimit: 8 }), 'daily limit 8');
  await expect(page.getByRole('cell', { name: 'Daily Overtime', exact: true })).toBeVisible();

  await page.getByRole('button', { name: 'Close rule editor' }).click();
  await page.getByRole('button', { name: 'Edit rule configuration' }).click();
  await page.getByLabel('Daily ordinary-hours limit Shift workers').fill('10');
  await page.getByRole('button', { name: 'Save changes' }).click();
  await expect(page.getByLabel('Rule Configuration')).toContainText('Custom: E2E Daily Overtime 8');
  await expectSummary(page, hospitalityShiftWorker([shift], { dailyLimit: 10 }), 'daily limit 10');
});

test('invalid overlapping periods are rejected rather than silently paid', async ({ page }) => {
  await openCalculator(page);
  const first = { day: 'Monday', start: 9, end: 14, break: 0 };
  const second = { day: 'Monday', additional: true, start: 13, end: 17, break: 0 };
  await enterShifts(page, [first, second]);
  await expect(page.getByRole('alert')).toContainText('Overlapping shifts are not allowed');
});
