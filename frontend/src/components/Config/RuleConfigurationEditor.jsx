import React, { useEffect, useRef, useState } from 'react';
import { api } from '../../services/apis';
import {
    DAYS,
    QUESTIONNAIRE_SECTIONS,
    fieldPath,
} from './ruleQuestionnaire';

const clone = (value) => JSON.parse(JSON.stringify(value));

const inputClass =
    'mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm disabled:bg-gray-100 disabled:text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:disabled:bg-gray-800';

const ruleFieldId = (path) => `rule-field-${path}`;

function decimalHoursToClockTime(value) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 24) {
        return typeof value === 'string' ? value : '';
    }
    const totalMinutes = Math.round(value * 60);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

function clockTimeToDecimalHours(value) {
    const match = /^(\d{1,2}):(\d{2})$/.exec(value);
    if (!match) {
        return null;
    }
    const hours = Number(match[1]);
    const minutes = Number(match[2]);
    if (hours > 24 || minutes > 59 || (hours === 24 && minutes !== 0)) {
        return null;
    }
    return hours + (minutes / 60);
}

function ClockTimeInput({ ariaLabel, value, disabled, onChange }) {
    return (
        <input
            aria-label={ariaLabel}
            type="text"
            inputMode="numeric"
            placeholder="HH:MM"
            pattern="(?:[01]?\\d|2[0-4]):[0-5]\\d"
            value={decimalHoursToClockTime(value)}
            disabled={disabled}
            onChange={(event) => {
                const rawValue = event.target.value;
                const decimalHours = clockTimeToDecimalHours(rawValue);
                onChange(rawValue === '' ? null : decimalHours ?? rawValue);
            }}
            className={inputClass}
        />
    );
}

function fieldLabelForPath(path) {
    for (const section of QUESTIONNAIRE_SECTIONS) {
        for (const [field, label] of section.fields) {
            const fieldPathValue = fieldPath(section.key, field);
            if (path === fieldPathValue || path.startsWith(`${fieldPathValue}.`)) {
                return label;
            }
        }
    }
    return 'Rule configuration';
}

function focusRuleField(path) {
    const candidates = Array.from(
        document.querySelectorAll('[data-rule-field-path]')
    )
        .filter((element) => {
            const candidatePath = element.dataset.ruleFieldPath;
            return path === candidatePath || path.startsWith(`${candidatePath}.`);
        })
        .sort(
            (first, second) =>
                (second.dataset.ruleFieldPath?.length || 0) -
                (first.dataset.ruleFieldPath?.length || 0)
        );
    const target = candidates[0];
    if (!target) {
        return;
    }
    target.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
    const control = target.matches('input, select, textarea, button')
        ? target
        : target.querySelector('input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])');
    control?.focus();
}

function ValidationSummary({ issues, hasErrors, summaryRef }) {
    if (!issues.length) {
        return null;
    }
    const orderedIssues = [...issues].sort(
        (first, second) =>
            Number(first.severity !== 'error') - Number(second.severity !== 'error')
    );
    return (
        <section
            ref={summaryRef}
            tabIndex="-1"
            role={hasErrors ? 'alert' : 'status'}
            className={`mt-4 rounded-md border p-3 text-sm ${
                hasErrors
                    ? 'border-red-300 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100'
                    : 'border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100'
            }`}
            aria-live="polite"
            aria-label="Validation issues"
        >
            <strong>
                {hasErrors ? 'Fix these issues before saving' : 'Review notes'}
            </strong>
            <ol className="mt-2 mb-0 list-inside space-y-1 p-0">
                {orderedIssues.map((issue, index) => (
                    <li key={`${issue.field_path}-${index}`}>
                        <button
                            type="button"
                            onClick={() => focusRuleField(issue.field_path)}
                            className="text-left underline decoration-current underline-offset-2 hover:no-underline focus:outline-none focus:ring-2 focus:ring-current"
                        >
                            <span className="font-medium">
                                {fieldLabelForPath(issue.field_path)}:
                            </span>{' '}
                            {issue.message}
                        </button>
                    </li>
                ))}
            </ol>
        </section>
    );
}

function FieldIssues({ path, issues }) {
    const matching = issues.filter(
        (issue) =>
            issue.field_path === path ||
            issue.field_path.startsWith(`${path}.`)
    );
    if (!matching.length) {
        return null;
    }
    return (
        <div className="mt-1 space-y-1">
            {matching.map((issue, index) => (
                <p
                    key={`${issue.field_path}-${index}`}
                    className={`m-0 text-xs ${
                        issue.severity === 'error'
                            ? 'text-red-600'
                            : 'text-amber-700 dark:text-amber-300'
                    }`}
                >
                    {issue.message}
                </p>
            ))}
        </div>
    );
}

function OvertimeLimitField({ label, record, disabled, issues, path, onChange, periodSettings = false }) {
    const value = record?.answer || { variation: 'default', default: null };
    const variation = value.variation || 'default';
    const fields = variation === 'worker_type'
        ? [['day', 'Day workers'], ['shift', 'Shift workers']]
        : variation === 'employment_type'
          ? [['full_time', 'Full-time employees'], ['part_time', 'Part-time employees'], ['casual', 'Casual employees']]
          : [['default', 'All employees']];
    const update = (key, nextValue) => onChange({ ...value, [key]: nextValue });
    const updateVariation = (nextVariation) => {
        const currentBasis = value.basis;
        const fallbackBasis = typeof currentBasis === 'object'
            ? currentBasis.default || currentBasis.full_time || currentBasis.part_time || currentBasis.casual || 'weekly'
            : currentBasis || 'weekly';
        const nextValue = { variation: nextVariation };
        if (periodSettings) {
            nextValue.basis = nextVariation === 'employment_type'
                ? { full_time: fallbackBasis, part_time: fallbackBasis, casual: fallbackBasis }
                : fallbackBasis;
        }
        onChange(nextValue);
    };
    const periodBasisFields = variation === 'employment_type'
        ? [['full_time', 'Full-time employees'], ['part_time', 'Part-time employees'], ['casual', 'Casual employees']]
        : [['default', 'All employees']];
    const updatePeriodBasis = (key, nextValue) => {
        if (variation === 'employment_type') {
            const current = typeof value.basis === 'object' && value.basis ? value.basis : {};
            update('basis', { ...current, [key]: nextValue });
            return;
        }
        update('basis', nextValue);
    };

    return (
        <div
            id={ruleFieldId(path)}
            data-rule-field-path={path}
            className="md:col-span-2 rounded-md border border-gray-200 p-3 dark:border-gray-600"
        >
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">{label}</label>
            <select
                aria-label={`${label} variation`}
                value={variation}
                disabled={disabled}
                onChange={(event) => updateVariation(event.target.value)}
                className={inputClass}
            >
                <option value="default">One limit for everyone</option>
                <option value="worker_type">Different limits for day and shift workers</option>
                <option value="employment_type">Different limits for full-time, part-time and casual employees</option>
            </select>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
                {fields.map(([key, fieldLabel]) => (
                    <label key={key} className="text-xs">
                        {fieldLabel}
                        <input
                            aria-label={`${label} ${fieldLabel}`}
                            type="number"
                            step="any"
                            value={value[key] ?? ''}
                            disabled={disabled}
                            onChange={(event) => update(
                                key,
                                event.target.value === '' ? null : Number(event.target.value)
                            )}
                            className={inputClass}
                        />
                    </label>
                ))}
            </div>
            {periodSettings && <div className="mt-3 grid gap-3 md:grid-cols-2">
                {periodBasisFields.map(([key, fieldLabel]) => <label key={key} className="text-xs">Overtime period{variation === 'employment_type' ? ` — ${fieldLabel}` : ''}
                    <select aria-label={`${label} basis ${fieldLabel}`} value={(typeof value.basis === 'object' ? value.basis?.[key] : value.basis) || 'weekly'} disabled={disabled}
                        onChange={(event) => updatePeriodBasis(key, event.target.value)} className={inputClass}>
                        <option value="weekly">Each week</option>
                        <option value="pay_period">Entire pay period</option>
                    </select>
                </label>)}
                <label className="text-xs">Maximum worked days (optional)
                    <input aria-label={`${label} maximum worked days`} type="number" min="1" step="1"
                        value={value.max_work_days ?? ''} disabled={disabled}
                        onChange={(event) => update('max_work_days', event.target.value === '' ? null : Number(event.target.value))}
                        className={inputClass} />
                </label>
            </div>}
            <FieldIssues path={path} issues={issues} />
        </div>
    );
}

function SimpleField({
    section,
    field,
    label,
    type,
    record,
    questionnaire,
    disabled,
    issues,
    onChange,
}) {
    const path = fieldPath(section, field);
    const answer = record?.answer;
    const dependentDisabled =
        (section === 'overtime' &&
            [
                'extended_overtime_rate',
                'two_tier_overtime_threshold',
                'extended_overtime_days',
            ].includes(field) &&
            questionnaire?.overtime?.two_tier_overtime?.answer !== true) ||
        (section === 'span_overtime' &&
            ['before_cutoff_hour', 'cutoff_hour'].includes(field) &&
            questionnaire?.span_overtime?.applies?.answer !== true) ||
        (section === 'long_day' &&
            ['uses_per_week', 'ordinary_limit_hours'].includes(field) &&
            questionnaire?.long_day?.enabled?.answer !== true) ||
        (section === 'gap_between_shifts' &&
            ['minimum_hours', 'penalty_rate'].includes(field) &&
            questionnaire?.gap_between_shifts?.applies?.answer !== true) ||
        (section === 'weekend_treatment' &&
            field.endsWith('_penalty_loading') &&
            questionnaire?.weekend_treatment?.[
                field.replace('_penalty_loading', '_treatment')
            ]?.answer !== 'penalty');
    const isDisabled = disabled || dependentDisabled;
    let control;

    if (type === 'overtime_limits' || type === 'period_overtime_limits') {
        const periodSettings = type === 'period_overtime_limits';
        return <OvertimeLimitField label={label} record={record} disabled={disabled} issues={issues} path={path} onChange={onChange} periodSettings={periodSettings} />;
    } else if (type === 'boolean') {
        control = (
            <select
                aria-label={label}
                value={
                    answer === true ? 'true' : answer === false ? 'false' : ''
                }
                disabled={isDisabled}
                onChange={(event) =>
                    onChange(
                        event.target.value === ''
                            ? null
                            : event.target.value === 'true'
                    )
                }
                className={inputClass}
            >
                <option value="">Select…</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
            </select>
        );
    } else if (type === 'weekend') {
        control = (
            <select
                aria-label={label}
                value={answer ?? ''}
                disabled={isDisabled}
                onChange={(event) => onChange(event.target.value || null)}
                className={inputClass}
            >
                <option value="">Select…</option>
                <option value="overtime">Overtime</option>
                <option value="penalty">Penalty loading</option>
                <option value="not_applicable">Not applicable</option>
            </select>
        );
    } else if (type === 'days') {
        control = (
            <div className="mt-2 flex flex-wrap gap-3">
                {DAYS.map((day) => (
                    <label key={day} className="flex items-center gap-1 text-sm">
                        <input
                            type="checkbox"
                            checked={(answer || []).includes(day)}
                            disabled={isDisabled}
                            onChange={(event) => {
                                const current = answer || [];
                                onChange(
                                    event.target.checked
                                        ? [...current, day]
                                        : current.filter((item) => item !== day)
                                );
                            }}
                        />
                        {day.slice(0, 3)}
                    </label>
                ))}
            </div>
        );
    } else if (type === 'time') {
        control = (
            <ClockTimeInput
                ariaLabel={label}
                value={answer}
                disabled={isDisabled}
                onChange={onChange}
            />
        );
    } else {
        control = (
            <input
                aria-label={label}
                type="number"
                step="any"
                value={answer ?? ''}
                disabled={isDisabled}
                onChange={(event) =>
                    onChange(
                        event.target.value === ''
                            ? null
                            : Number(event.target.value)
                    )
                }
                className={inputClass}
            />
        );
    }

    return (
        <div
            id={ruleFieldId(path)}
            data-rule-field-path={path}
            className={dependentDisabled ? 'opacity-60' : ''}
        >
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                {label}
            </label>
            {control}
            <FieldIssues path={path} issues={issues} />
        </div>
    );
}

function PenaltyRows({
    section,
    field,
    label,
    record,
    disabled,
    issues,
    onChange,
}) {
    const rows = record?.answer || [];
    const expectedType =
        field === 'shift_based_penalties' ? 'shift_based' : 'time_based';
    const isShiftBased = expectedType === 'shift_based';
    const updateRow = (index, key, value) => {
        const next = clone(rows);
        next[index][key] = value;
        onChange(next);
    };
    const updateClockTime = (index, key, value) => {
        updateRow(index, key, value);
    };
    const addRow = () => {
        onChange([
            ...rows,
            {
                code_name: `${expectedType}_loading_${rows.length + 1}`,
                type: expectedType,
                basis: isShiftBased ? 'start' : 'time',
                start_hour: 0,
                end_hour: 24,
                finish_start_hour: null,
                finish_end_hour: null,
                rate: 0,
                description: '',
                applies_to: expectedType === 'shift_based' ? ['shift'] : ['day'],
                extra: {},
            },
        ]);
    };

    return (
        <div
            id={ruleFieldId(fieldPath(section, field))}
            data-rule-field-path={fieldPath(section, field)}
        >
            <div className="flex items-center justify-between gap-3">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                    {label}
                </label>
                <button
                    type="button"
                    onClick={addRow}
                    disabled={disabled}
                    className="bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                >
                    Add row
                </button>
            </div>
            <div className="mt-2 space-y-3">
                {rows.map((row, index) => (
                    <div
                        key={index}
                        className="rounded-md border border-gray-200 p-3 dark:border-gray-600"
                    >
                        <div className="grid gap-3 md:grid-cols-4">
                            <label className="text-xs">
                                Code name
                                <input
                                    aria-label={`${label} code ${index + 1}`}
                                    value={row.code_name || ''}
                                    disabled={disabled}
                                    onChange={(event) =>
                                        updateRow(
                                            index,
                                            'code_name',
                                            event.target.value
                                        )
                                    }
                                    className={inputClass}
                                />
                            </label>
                            {isShiftBased ? (
                                <label className="text-xs">
                                    Apply loading when
                                    <select
                                        aria-label={`${label} condition ${index + 1}`}
                                        value={row.basis || 'start'}
                                        disabled={disabled}
                                        onChange={(event) =>
                                            updateRow(
                                                index,
                                                'basis',
                                                event.target.value
                                            )
                                        }
                                        className={inputClass}
                                    >
                                        <option value="start">Shift starts in this window</option>
                                        <option value="end">Shift ends in this window</option>
                                        <option value="duration">Shift duration is in this range</option>
                                        <option value="start_and_end">Shift start and end both match</option>
                                    </select>
                                </label>
                            ) : (
                                <p className="m-0 self-end text-xs text-gray-500 dark:text-gray-400">
                                    Applies only to hours worked in this time window.
                                </p>
                            )}
                            <label className="text-xs">
                                {row.basis === 'duration'
                                    ? 'Minimum duration (hours)'
                                    : row.basis === 'end'
                                      ? 'Shift ends from (24-hour time)'
                                      : 'Shift starts from (24-hour time)'}
                                {row.basis === 'duration' ? (
                                    <input
                                        aria-label={`${label} start ${index + 1}`}
                                        type="number"
                                        step="any"
                                        value={row.start_hour ?? ''}
                                        disabled={disabled}
                                        onChange={(event) =>
                                            updateRow(
                                                index,
                                                'start_hour',
                                                event.target.value === ''
                                                    ? null
                                                    : Number(event.target.value)
                                            )
                                        }
                                        className={inputClass}
                                    />
                                ) : (
                                    <ClockTimeInput
                                        ariaLabel={`${label} start ${index + 1}`}
                                        value={row.start_hour}
                                        disabled={disabled}
                                        onChange={(value) => updateClockTime(index, 'start_hour', value)}
                                    />
                                )}
                            </label>
                            <label className="text-xs">
                                {row.basis === 'duration'
                                    ? 'Maximum duration (hours)'
                                    : row.basis === 'end'
                                      ? 'Shift ends before (24-hour time)'
                                      : 'Shift starts before (24-hour time)'}
                                {row.basis === 'duration' ? (
                                    <input
                                        aria-label={`${label} end ${index + 1}`}
                                        type="number"
                                        step="any"
                                        value={row.end_hour ?? ''}
                                        disabled={disabled}
                                        onChange={(event) =>
                                            updateRow(
                                                index,
                                                'end_hour',
                                                event.target.value === ''
                                                    ? null
                                                    : Number(event.target.value)
                                            )
                                        }
                                        className={inputClass}
                                    />
                                ) : (
                                    <ClockTimeInput
                                        ariaLabel={`${label} end ${index + 1}`}
                                        value={row.end_hour}
                                        disabled={disabled}
                                        onChange={(value) => updateClockTime(index, 'end_hour', value)}
                                    />
                                )}
                            </label>
                            {isShiftBased && row.basis === 'start_and_end' && (
                                <>
                                    <label className="text-xs">
                                        Shift ends from (24-hour time)
                                        <ClockTimeInput
                                            ariaLabel={`${label} finish start ${index + 1}`}
                                            value={row.finish_start_hour ?? ''}
                                            disabled={disabled}
                                            onChange={(value) => updateClockTime(index, 'finish_start_hour', value)}
                                        />
                                    </label>
                                    <label className="text-xs">
                                        Shift ends before (24-hour time)
                                        <ClockTimeInput
                                            ariaLabel={`${label} finish end ${index + 1}`}
                                            value={row.finish_end_hour ?? ''}
                                            disabled={disabled}
                                            onChange={(value) => updateClockTime(index, 'finish_end_hour', value)}
                                        />
                                    </label>
                                </>
                            )}
                            <label className="text-xs">
                                Loading
                                <input
                                    type="number"
                                    step="any"
                                    value={row.rate ?? ''}
                                    disabled={disabled}
                                    onChange={(event) =>
                                        updateRow(
                                            index,
                                            'rate',
                                            event.target.value === ''
                                                ? null
                                                : Number(event.target.value)
                                        )
                                    }
                                    className={inputClass}
                                />
                            </label>
                            <label className="text-xs md:col-span-2">
                                Description
                                <input
                                    value={row.description || ''}
                                    disabled={disabled}
                                    onChange={(event) =>
                                        updateRow(
                                            index,
                                            'description',
                                            event.target.value
                                        )
                                    }
                                    className={inputClass}
                                />
                            </label>
                            <div className="text-xs">
                                Applies to
                                <div className="mt-2 flex gap-3">
                                    {['day', 'shift'].map((worker) => (
                                        <label
                                            key={worker}
                                            className="flex items-center gap-1"
                                        >
                                            <input
                                                type="checkbox"
                                                checked={(
                                                    row.applies_to || []
                                                ).includes(worker)}
                                                disabled={disabled}
                                                onChange={(event) => {
                                                    const current =
                                                        row.applies_to || [];
                                                    updateRow(
                                                        index,
                                                        'applies_to',
                                                        event.target.checked
                                                            ? [
                                                                  ...current,
                                                                  worker,
                                                              ]
                                                            : current.filter(
                                                                  (item) =>
                                                                      item !==
                                                                      worker
                                                              )
                                                    );
                                                }}
                                            />
                                            {worker}
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <button
                            type="button"
                            disabled={disabled}
                            onClick={() =>
                                onChange(
                                    rows.filter(
                                        (_item, rowIndex) => rowIndex !== index
                                    )
                                )
                            }
                            className="mt-3 bg-red-50 text-red-700 hover:bg-red-100 disabled:opacity-50"
                        >
                            Remove
                        </button>
                    </div>
                ))}
                {!rows.length && (
                    <p className="text-sm text-gray-500">
                        No {label.toLowerCase()} configured.
                    </p>
                )}
            </div>
            <FieldIssues
                path={fieldPath(section, field)}
                issues={issues}
            />
        </div>
    );
}

function Questionnaire({
    questionnaire,
    issues,
    disabled,
    onAnswerChange,
}) {
    return (
        <div className="space-y-4">
            {QUESTIONNAIRE_SECTIONS.map((section) => (
                <section
                    key={section.key}
                    className="rounded-lg border border-gray-200 p-4 dark:border-gray-600"
                >
                    <h4 className="m-0 text-base font-semibold">
                        {section.title}
                    </h4>
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                        {section.description}
                    </p>
                    <div className="mt-4 grid gap-5 md:grid-cols-2">
                        {section.fields.map(([field, label, type]) =>
                            type === 'penalties' ? (
                                <div key={field} className="md:col-span-2">
                                    <PenaltyRows
                                        section={section.key}
                                        field={field}
                                        label={label}
                                        record={
                                            questionnaire?.[section.key]?.[
                                                field
                                            ]
                                        }
                                        disabled={disabled}
                                        issues={issues}
                                        onChange={(value) =>
                                            onAnswerChange(
                                                section.key,
                                                field,
                                                value
                                            )
                                        }
                                    />
                                </div>
                            ) : (
                                <SimpleField
                                    key={field}
                                    section={section.key}
                                    field={field}
                                    label={label}
                                    type={type}
                                    record={
                                        questionnaire?.[section.key]?.[field]
                                    }
                                    questionnaire={questionnaire}
                                    disabled={disabled}
                                    issues={issues}
                                    onChange={(value) =>
                                        onAnswerChange(
                                            section.key,
                                            field,
                                            value
                                        )
                                    }
                                />
                            )
                        )}
                    </div>
                </section>
            ))}
        </div>
    );
}

export function RuleConfigurationEditor({
    configurationId,
    allowSaving = false,
    onConfigurationSaved,
    onDirtyChange,
}) {
    const [configuration, setConfiguration] = useState(null);
    const [source, setSource] = useState('');
    const [questionnaire, setQuestionnaire] = useState(null);
    const [initialSource, setInitialSource] = useState('');
    const [initialQuestionnaire, setInitialQuestionnaire] = useState(null);
    const [issues, setIssues] = useState([]);
    const [copyName, setCopyName] = useState('');
    const [message, setMessage] = useState('');
    const [isWorking, setIsWorking] = useState(false);
    const [dirtyLayer, setDirtyLayer] = useState(null);
    const validationSummaryRef = useRef(null);

    useEffect(() => {
        let isMounted = true;
        const controller = new AbortController();
        const load = async () => {
            if (!configurationId) {
                return;
            }
            setIsWorking(true);
            setMessage('');
            try {
                const loaded = await api.getRuleConfiguration(
                    configurationId,
                    { signal: controller.signal }
                );
                if (isMounted) {
                    // Apply one response as a unit so source, form values, and
                    // configuration identity can never refer to different files.
                    setConfiguration(loaded);
                    setSource(loaded.source);
                    setInitialSource(loaded.source);
                    setQuestionnaire(clone(loaded.questionnaire));
                    setInitialQuestionnaire(clone(loaded.questionnaire));
                    setIssues(loaded.structural_issues || []);
                    setCopyName(
                        loaded.kind === 'builtin' ? `${loaded.name} Custom` : ''
                    );
                    setDirtyLayer(null);
                }
            } catch (error) {
                if (isMounted && error.name !== 'AbortError') {
                    setMessage(error.message);
                }
            } finally {
                if (isMounted) {
                    setIsWorking(false);
                }
            }
        };
        load();
        return () => {
            isMounted = false;
            controller.abort();
        };
    }, [configurationId]);

    useEffect(() => {
        onDirtyChange?.(Boolean(dirtyLayer));
    }, [dirtyLayer, onDirtyChange]);

    const hasErrors = issues.some((issue) => issue.severity === 'error');

    const showValidationSummary = () => {
        window.requestAnimationFrame(() => {
            validationSummaryRef.current?.scrollIntoView?.({
                behavior: 'smooth',
                block: 'start',
            });
            validationSummaryRef.current?.focus();
        });
    };

    const changeAnswer = (section, field, value) => {
        // Only one editor layer may own unsaved changes at a time.
        if (dirtyLayer === 'raw') {
            return;
        }
        setQuestionnaire((current) => {
            const next = clone(current);
            next[section][field].answer = value;
            return next;
        });
        setDirtyLayer('guided');
        setMessage('');
    };

    const discardChanges = () => {
        setSource(initialSource);
        setQuestionnaire(clone(initialQuestionnaire));
        setIssues(configuration?.structural_issues || []);
        setDirtyLayer(null);
        setMessage('Unsaved changes discarded.');
    };

    const validateCurrent = async () => {
        if (!configuration) {
            return;
        }
        setIsWorking(true);
        setMessage('');
        try {
            const result = await api.validateRuleConfiguration(
                configuration.base_award,
                source,
                dirtyLayer === 'guided' ? questionnaire : null
            );
            setIssues(result.structural_issues || []);
            if (result.valid === false) {
                showValidationSummary();
            }
            if (dirtyLayer === 'raw') {
                setQuestionnaire(clone(result.questionnaire));
            }
            setMessage(
                result.valid === false
                    ? 'Fix the highlighted structural errors before saving.'
                    : dirtyLayer === 'guided'
                      ? 'Guided values are structurally valid and ready to save.'
                      : 'Guided rule values are valid.'
            );
        } catch (error) {
            setMessage(error.message);
        } finally {
            setIsWorking(false);
        }
    };

    const saveCurrent = async () => {
        if (!configuration) {
            return;
        }
        setIsWorking(true);
        setMessage('');
        try {
            const validation = await api.validateRuleConfiguration(
                configuration.base_award,
                source,
                dirtyLayer === 'guided' ? questionnaire : null
            );
            setIssues(validation.structural_issues || []);
            if (validation.valid === false) {
                setMessage('Fix the errors shown at the top before saving.');
                showValidationSummary();
                return;
            }

            const saved = configuration.kind === 'builtin'
                ? await api.createRuleConfiguration(
                    configuration.base_award,
                    copyName,
                    source,
                    dirtyLayer === 'guided' ? questionnaire : null,
                )
                : await api.updateRuleConfiguration(
                    configuration.id,
                    source,
                    dirtyLayer === 'guided' ? questionnaire : null,
                );
            setConfiguration(saved);
            setSource(saved.source);
            setInitialSource(saved.source);
            setQuestionnaire(clone(saved.questionnaire));
            setInitialQuestionnaire(clone(saved.questionnaire));
            setIssues(saved.structural_issues || []);
            setDirtyLayer(null);
            setMessage('Custom configuration saved and selected.');
            await onConfigurationSaved?.(saved);
        } catch (error) {
            setMessage(error.message);
        } finally {
            setIsWorking(false);
        }
    };

    if (!configurationId) {
        return null;
    }

    const guidedDisabled = isWorking || dirtyLayer === 'raw';
    const saveActionLabel = configuration?.kind === 'builtin'
        ? 'Create private copy'
        : 'Save changes';
    const actionStatus = isWorking
        ? 'Checking changes…'
        : dirtyLayer
          ? 'Unsaved changes'
          : configuration?.kind === 'custom'
            ? 'Saved'
            : allowSaving
              ? 'Ready to create a private copy'
              : 'Temporary edits only';

    return (
        <div className="mt-4 rounded-lg border border-gray-200 p-4 text-left dark:border-gray-600">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <h3 className="m-0 text-lg font-semibold text-gray-900 dark:text-white">
                        Pay rules
                    </h3>
                    <p className="mt-1 mb-0 text-sm text-gray-600 dark:text-gray-300">
                        Enter the rules that apply to this award.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <span className="rounded bg-gray-100 px-2 py-1 text-xs uppercase dark:bg-gray-700">
                        {configuration?.kind || 'loading'}
                    </span>
                </div>
            </div>

            <ValidationSummary
                issues={issues}
                hasErrors={hasErrors}
                summaryRef={validationSummaryRef}
            />

            {allowSaving ? (
                configuration?.kind === 'builtin' && (
                    <div className="mt-4">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                            New custom configuration name
                        </label>
                        <input
                            aria-label="New custom configuration name"
                            type="text"
                            value={copyName}
                            onChange={(event) => setCopyName(event.target.value)}
                            className={inputClass}
                        />
                        <p className="mt-1 text-xs text-gray-500">
                            Built-ins are immutable. Saving creates a custom copy.
                        </p>
                    </div>
                )
            ) : <p className="temporary-rules-note">These rule edits are temporary. They are used for review in this session and are never saved.</p>}

            <div
                className="sticky top-2 z-10 mt-4 rounded-lg border border-gray-200 bg-white/95 p-3 shadow-sm backdrop-blur dark:border-gray-600 dark:bg-gray-800/95"
                aria-label="Rule configuration actions"
            >
                <div className="flex flex-wrap items-center gap-2">
                    <span
                        className={`mr-auto text-sm font-medium ${
                            dirtyLayer
                                ? 'text-blue-700 dark:text-blue-300'
                                : 'text-gray-700 dark:text-gray-200'
                        }`}
                        aria-live="polite"
                    >
                        {actionStatus}
                    </span>
                    <button
                        type="button"
                        onClick={validateCurrent}
                        disabled={isWorking || !configuration || !dirtyLayer}
                        className="bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                    >
                        Validate
                    </button>
                    {allowSaving && (
                        <button
                            type="button"
                            onClick={saveCurrent}
                            disabled={
                                isWorking || !configuration || !dirtyLayer ||
                                (configuration.kind === 'builtin' && !copyName.trim())
                            }
                            className="bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                        >
                            {saveActionLabel}
                        </button>
                    )}
                    <button
                        type="button"
                        onClick={discardChanges}
                        disabled={isWorking || !dirtyLayer}
                        className="bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                    >
                        Discard changes
                    </button>
                </div>
                {message && (
                    <p className="mt-2 mb-0 text-sm text-gray-700 dark:text-gray-200">
                        {message}
                    </p>
                )}
            </div>

            {questionnaire && (
                <div className="mt-4">
                    {dirtyLayer === 'raw' && (
                        <p className="rounded bg-blue-50 p-2 text-sm text-blue-800">
                            Questionnaire editing is locked while Python has
                            unsaved edits. Save or discard the Python changes
                            first.
                        </p>
                    )}
                    <Questionnaire
                        questionnaire={questionnaire}
                        issues={issues}
                        disabled={guidedDisabled}
                        onAnswerChange={changeAnswer}
                    />
                </div>
            )}

        </div>
    );
}
