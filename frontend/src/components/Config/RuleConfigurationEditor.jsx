import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../../services/apis';
import {
    DAYS,
    QUESTIONNAIRE_SECTIONS,
    fieldPath,
    hasStructuralErrors,
} from './ruleQuestionnaire';

const clone = (value) => JSON.parse(JSON.stringify(value));

const inputClass =
    'mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm disabled:bg-gray-100 disabled:text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:disabled:bg-gray-800';

function FieldContext({ record }) {
    if (!record) {
        return null;
    }
    const references = [
        ...(record.clause_references || []),
        ...(record.source_rule_ids || []),
    ];
    return (
        <details className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            <summary className="cursor-pointer">
                Context: {record.status || 'derived'}
            </summary>
            {record.reasoning_summary && (
                <p className="mt-1 mb-0">{record.reasoning_summary}</p>
            )}
            {references.length > 0 && (
                <p className="mt-1 mb-0">
                    Evidence: {references.join(', ')}
                </p>
            )}
            {(record.special_case_notes || []).length > 0 && (
                <p className="mt-1 mb-0">
                    Notes: {record.special_case_notes.join(' · ')}
                </p>
            )}
        </details>
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
            field === 'cutoff_hour' &&
            questionnaire?.span_overtime?.applies?.answer !== true) ||
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

    if (type === 'boolean') {
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
        <div className={dependentDisabled ? 'opacity-60' : ''}>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                {label}
            </label>
            {control}
            <FieldIssues path={path} issues={issues} />
            <FieldContext record={record} />
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
    const updateRow = (index, key, value) => {
        const next = clone(rows);
        next[index][key] = value;
        onChange(next);
    };
    const addRow = () => {
        onChange([
            ...rows,
            {
                code_name: `${expectedType}_loading_${rows.length + 1}`,
                type: expectedType,
                basis: 'start',
                start_hour: 0,
                end_hour: 24,
                rate: 0,
                description: '',
                applies_to: expectedType === 'shift_based' ? ['shift'] : ['day'],
                extra: {},
            },
        ]);
    };

    return (
        <div>
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
                        key={`${row.code_name}-${index}`}
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
                            <label className="text-xs">
                                Basis
                                <select
                                    value={row.basis || ''}
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
                                    <option value="start">Shift start</option>
                                    <option value="end">Shift end</option>
                                    <option value="duration">Duration</option>
                                </select>
                            </label>
                            <label className="text-xs">
                                Start
                                <input
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
                            </label>
                            <label className="text-xs">
                                End
                                <input
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
                            </label>
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
            <FieldContext record={record} />
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
    onConfigurationSaved,
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
    const [reviewHelperEnabled, setReviewHelperEnabled] = useState(true);
    const [advancedOpen, setAdvancedOpen] = useState(false);
    const [dirtyLayer, setDirtyLayer] = useState(null);
    const [importName, setImportName] = useState('');
    const [pythonFile, setPythonFile] = useState(null);
    const [questionnaireFile, setQuestionnaireFile] = useState(null);

    const loadConfiguration = async (id) => {
        const loaded = await api.getRuleConfiguration(id);
        setConfiguration(loaded);
        setSource(loaded.source);
        setInitialSource(loaded.source);
        setQuestionnaire(clone(loaded.questionnaire));
        setInitialQuestionnaire(clone(loaded.questionnaire));
        setIssues(loaded.structural_issues || []);
        setCopyName(
            loaded.kind === 'builtin' ? `${loaded.name} Custom` : ''
        );
        setImportName(`${loaded.name} Import`);
        setDirtyLayer(null);
        return loaded;
    };

    useEffect(() => {
        let isMounted = true;
        const load = async () => {
            if (!configurationId) {
                return;
            }
            setIsWorking(true);
            setMessage('');
            try {
                if (isMounted) {
                    await loadConfiguration(configurationId);
                }
            } catch (error) {
                if (isMounted) {
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
        };
    }, [configurationId]);

    const hasErrors = useMemo(() => hasStructuralErrors(issues), [issues]);

    const changeAnswer = (section, field, value) => {
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

    const changeSource = (value) => {
        if (dirtyLayer === 'guided') {
            return;
        }
        setSource(value);
        setDirtyLayer('raw');
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
            if (dirtyLayer === 'raw') {
                setQuestionnaire(clone(result.questionnaire));
            }
            setMessage(
                result.valid === false
                    ? 'Fix the highlighted structural errors before saving.'
                    : dirtyLayer === 'guided'
                      ? 'Guided values are structurally valid and ready to save.'
                      : 'Valid Python rule class. The Review Helper preview is refreshed.'
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
            const guidedValues =
                dirtyLayer === 'guided' ? questionnaire : null;
            if (guidedValues) {
                const validation = await api.validateRuleConfiguration(
                    configuration.base_award,
                    source,
                    guidedValues
                );
                setIssues(validation.structural_issues || []);
                if (validation.valid === false) {
                    setMessage(
                        'Fix the highlighted structural errors before saving.'
                    );
                    return;
                }
            }
            const saved =
                configuration.kind === 'builtin'
                    ? await api.createRuleConfiguration(
                          configuration.base_award,
                          copyName,
                          source,
                          guidedValues
                      )
                    : await api.updateRuleConfiguration(
                          configuration.id,
                          source,
                          guidedValues
                      );
            setConfiguration(saved);
            setSource(saved.source);
            setInitialSource(saved.source);
            setQuestionnaire(clone(saved.questionnaire));
            setInitialQuestionnaire(clone(saved.questionnaire));
            setIssues(saved.structural_issues || []);
            setDirtyLayer(null);
            setMessage('Custom configuration saved and selected.');
            await onConfigurationSaved(saved);
        } catch (error) {
            setMessage(error.message);
        } finally {
            setIsWorking(false);
        }
    };

    const toggleReviewHelper = () => {
        if (dirtyLayer) {
            setMessage(
                'Save or discard your current edits before changing editor mode.'
            );
            return;
        }
        setReviewHelperEnabled((enabled) => !enabled);
        setAdvancedOpen(reviewHelperEnabled);
    };

    const importFiles = async () => {
        if (!configuration || !pythonFile || !importName.trim()) {
            return;
        }
        setIsWorking(true);
        setMessage('');
        try {
            const importedSource = await pythonFile.text();
            let importedQuestionnaire = null;
            if (questionnaireFile) {
                importedQuestionnaire = JSON.parse(
                    await questionnaireFile.text()
                );
            }
            const saved = await api.createRuleConfiguration(
                configuration.base_award,
                importName,
                importedSource,
                importedQuestionnaire
            );
            setMessage('Award Extractor files imported and selected.');
            await onConfigurationSaved(saved);
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
    const rawDisabled = isWorking || dirtyLayer === 'guided';

    return (
        <div className="mt-4 rounded-lg border border-gray-200 p-4 text-left dark:border-gray-600">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <h3 className="m-0 text-lg font-semibold text-gray-900 dark:text-white">
                        Ruleset Review Helper
                    </h3>
                    <p className="mt-1 mb-0 text-sm text-gray-600 dark:text-gray-300">
                        Python remains the calculation source of truth. This
                        helper edits only the fields Paychecker uses.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={reviewHelperEnabled}
                            onChange={toggleReviewHelper}
                            disabled={isWorking}
                        />
                        Review Helper
                    </label>
                    <span className="rounded bg-gray-100 px-2 py-1 text-xs uppercase dark:bg-gray-700">
                        {configuration?.kind || 'loading'}
                    </span>
                </div>
            </div>

            {configuration?.kind === 'builtin' && (
                <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                        New custom configuration name
                    </label>
                    <input
                        type="text"
                        value={copyName}
                        onChange={(event) => setCopyName(event.target.value)}
                        className={inputClass}
                    />
                    <p className="mt-1 text-xs text-gray-500">
                        Built-ins are immutable. Saving creates a custom copy
                        beneath {configuration.name}.
                    </p>
                </div>
            )}

            {issues.length > 0 && (
                <div className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
                    <strong>
                        {hasErrors
                            ? 'Review required before guided save.'
                            : 'Code-derived warnings'}
                    </strong>
                    <span className="ml-2">
                        {issues.length} structural issue
                        {issues.length === 1 ? '' : 's'} shown beside the
                        affected fields.
                    </span>
                </div>
            )}

            {reviewHelperEnabled && questionnaire && (
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

            <details
                className="mt-4 rounded-lg border border-gray-200 p-4 dark:border-gray-600"
                open={!reviewHelperEnabled || advancedOpen}
                onToggle={(event) => setAdvancedOpen(event.currentTarget.open)}
            >
                <summary className="cursor-pointer font-semibold">
                    Advanced Python
                </summary>
                {dirtyLayer === 'guided' && (
                    <p className="rounded bg-blue-50 p-2 text-sm text-blue-800">
                        Python editing is locked while the Review Helper has
                        unsaved edits. Save or discard those changes first.
                    </p>
                )}
                <textarea
                    aria-label="Rule class source"
                    value={source}
                    onChange={(event) => changeSource(event.target.value)}
                    spellCheck="false"
                    disabled={rawDisabled}
                    className="mt-3 block h-96 w-full resize-y rounded-md border border-gray-300 bg-gray-950 p-3 font-mono text-xs text-gray-100 shadow-sm disabled:opacity-60"
                />
            </details>

            <div className="mt-4 flex flex-wrap items-center gap-2">
                <button
                    type="button"
                    onClick={validateCurrent}
                    disabled={isWorking || !configuration || !dirtyLayer}
                    className="bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                >
                    Validate
                </button>
                <button
                    type="button"
                    onClick={saveCurrent}
                    disabled={
                        isWorking ||
                        !configuration ||
                        !dirtyLayer ||
                        (dirtyLayer === 'guided' && hasErrors) ||
                        (configuration.kind === 'builtin' && !copyName.trim())
                    }
                    className="bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                >
                    {configuration?.kind === 'builtin'
                        ? 'Save custom copy'
                        : 'Save changes'}
                </button>
                <button
                    type="button"
                    onClick={discardChanges}
                    disabled={isWorking || !dirtyLayer}
                    className="bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                >
                    Discard
                </button>
                {dirtyLayer && (
                    <span className="text-xs font-medium uppercase text-blue-700">
                        Unsaved {dirtyLayer} edits
                    </span>
                )}
            </div>

            <details className="mt-4 rounded-lg border border-gray-200 p-4 dark:border-gray-600">
                <summary className="cursor-pointer font-semibold">
                    Import Award Extractor files
                </summary>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    Import a calculator Python file and, optionally, its
                    questionnaire JSON as review evidence. The Python class
                    must match this award.
                </p>
                <div className="grid gap-3 md:grid-cols-3">
                    <label className="text-sm">
                        Custom name
                        <input
                            value={importName}
                            onChange={(event) =>
                                setImportName(event.target.value)
                            }
                            className={inputClass}
                        />
                    </label>
                    <label className="text-sm">
                        Calculator Python
                        <input
                            type="file"
                            accept=".py,text/x-python"
                            onChange={(event) =>
                                setPythonFile(event.target.files?.[0] || null)
                            }
                            className={inputClass}
                        />
                    </label>
                    <label className="text-sm">
                        Questionnaire JSON (optional)
                        <input
                            type="file"
                            accept=".json,application/json"
                            onChange={(event) =>
                                setQuestionnaireFile(
                                    event.target.files?.[0] || null
                                )
                            }
                            className={inputClass}
                        />
                    </label>
                </div>
                <button
                    type="button"
                    onClick={importFiles}
                    disabled={
                        isWorking ||
                        Boolean(dirtyLayer) ||
                        !pythonFile ||
                        !importName.trim()
                    }
                    className="mt-3 bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                >
                    Import as custom configuration
                </button>
            </details>

            {message && (
                <p className="mt-3 mb-0 text-sm text-gray-700 dark:text-gray-200">
                    {message}
                </p>
            )}
        </div>
    );
}
