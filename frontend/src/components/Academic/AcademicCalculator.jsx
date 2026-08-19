import React, { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../../services/apis';
import { formatCurrency } from '../../utils/formatters';

const STORAGE_KEY = 'payguide-academic-qut-v1';

const parseDate = (value) => {
    const [year, month, day] = value.split('-').map(Number);
    return new Date(year, month - 1, day, 12);
};

const toISODate = (value) => {
    const date = value instanceof Date ? value : parseDate(value);
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
};

const addDays = (value, amount) => {
    const date = value instanceof Date ? new Date(value) : parseDate(value);
    date.setDate(date.getDate() + amount);
    return date;
};

const defaultMonday = () => {
    const today = new Date();
    const offset = (today.getDay() + 6) % 7;
    return toISODate(addDays(today, -offset));
};

const newId = (prefix) => `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const loadLocalData = () => {
    try {
        const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '{}');
        return {
            courses: Array.isArray(stored.courses) ? stored.courses : [],
            workItems: Array.isArray(stored.workItems) ? stored.workItems : [],
            periodStart: stored.periodStart || defaultMonday(),
        };
    } catch {
        return { courses: [], workItems: [], periodStart: defaultMonday() };
    }
};

const initialItem = (date = '') => ({
    date,
    courseId: '',
    topic: '',
    activity: 'tutorial',
    variant: 'normal',
    hours: '1',
    actualAssociatedHours: '',
    existingOccasionId: '',
    requiredOrApproved: false,
    classificationOverride: '',
    overrideReason: '',
});

export default function AcademicCalculator({ scheme }) {
    const initial = useMemo(loadLocalData, []);
    const [ruleset, setRuleset] = useState(null);
    const [courses, setCourses] = useState(initial.courses);
    const [workItems, setWorkItems] = useState(initial.workItems);
    const [periodStart, setPeriodStart] = useState(initial.periodStart);
    const [courseDraft, setCourseDraft] = useState({ code: '', name: '', eligibility: 'standard' });
    const [itemDraft, setItemDraft] = useState(initialItem(initial.periodStart));
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const formRef = useRef(null);

    useEffect(() => {
        api.getAcademicRuleset(scheme)
            .then((data) => {
                setRuleset(data);
                const firstActivity = Object.keys(data.activities || {})[0] || 'tutorial';
                setItemDraft((current) => ({
                    ...current,
                    activity: firstActivity,
                    variant: data.activities?.[firstActivity]?.default_variant || '',
                }));
            })
            .catch((loadError) => setError(loadError.message));
    }, [scheme]);

    useEffect(() => {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ courses, workItems, periodStart }));
    }, [courses, workItems, periodStart]);

    useEffect(() => {
        if (courses.length > 0 && !courses.some((course) => course.id === itemDraft.courseId)) {
            setItemDraft((current) => ({ ...current, courseId: courses[0].id }));
        }
    }, [courses, itemDraft.courseId]);

    const periodDates = useMemo(
        () => Array.from({ length: 14 }, (_, index) => toISODate(addDays(periodStart, index))),
        [periodStart]
    );
    const periodEnd = periodDates[13];
    const lookbackStart = toISODate(addDays(periodStart, -7));
    const visibleItems = useMemo(
        () => workItems.filter((item) => item.date >= periodStart && item.date <= periodEnd),
        [workItems, periodStart, periodEnd]
    );
    const lookbackItems = useMemo(
        () => workItems.filter((item) => item.date >= lookbackStart && item.date < periodStart),
        [workItems, lookbackStart, periodStart]
    );

    useEffect(() => {
        if (!ruleset || visibleItems.length === 0) {
            setResult(null);
            setError('');
            return undefined;
        }
        const controller = new AbortController();
        const timer = window.setTimeout(() => {
            api.calculateAcademicPay({
                scheme,
                period_start: periodStart,
                courses: courses.map((course) => ({
                    id: course.id,
                    code: course.code,
                    name: course.name || null,
                    eligibility: course.eligibility,
                })),
                work_items: visibleItems.map((item) => item.payload),
                lookback_items: lookbackItems.map((item) => item.payload),
            }, { signal: controller.signal })
                .then((data) => {
                    setResult(data);
                    setError('');
                })
                .catch((calculationError) => {
                    if (calculationError.name !== 'AbortError') {
                        setError(calculationError.message);
                        setResult(null);
                    }
                });
        }, 120);
        return () => {
            window.clearTimeout(timer);
            controller.abort();
        };
    }, [courses, lookbackItems, periodStart, ruleset, scheme, visibleItems]);

    const activityRule = ruleset?.activities?.[itemDraft.activity];
    const isComposite = activityRule?.payment_basis === 'composite_unit';
    const variants = activityRule?.variants || {};
    const knownTopics = useMemo(
        () => [...new Set(workItems
            .filter((item) => item.payload.course_id === itemDraft.courseId)
            .map((item) => item.payload.topic)
            .filter(Boolean))],
        [itemDraft.courseId, workItems]
    );
    const sameDateOccasions = useMemo(() => {
        const occasions = new Map();
        visibleItems
            .filter((item) => item.date === itemDraft.date)
            .forEach((item) => {
                if (!occasions.has(item.payload.occasion_id)) {
                    const course = courses.find((value) => value.id === item.payload.course_id);
                    const activity = ruleset?.activities?.[item.payload.activity];
                    occasions.set(item.payload.occasion_id, {
                        id: item.payload.occasion_id,
                        label: [course?.code, activity?.label].filter(Boolean).join(' — ') || 'existing work',
                    });
                }
            });
        return [...occasions.values()];
    }, [courses, itemDraft.date, ruleset, visibleItems]);
    const resultsById = useMemo(
        () => Object.fromEntries((result?.line_items || []).map((line) => [line.id, line])),
        [result]
    );

    const addCourse = (event) => {
        event.preventDefault();
        const code = courseDraft.code.trim();
        if (!code) return;
        const course = { ...courseDraft, code, name: courseDraft.name.trim(), id: newId('course') };
        setCourses((current) => [...current, course]);
        setCourseDraft({ code: '', name: '', eligibility: 'standard' });
        setItemDraft((current) => ({ ...current, courseId: current.courseId || course.id }));
    };

    const selectActivity = (activity) => {
        const nextRule = ruleset.activities[activity];
        setItemDraft((current) => ({
            ...current,
            activity,
            variant: nextRule.default_variant,
            topic: nextRule.topic_required ? current.topic : '',
            actualAssociatedHours: '',
            requiredOrApproved: nextRule.payment_basis === 'direct_hour' ? current.requiredOrApproved : false,
            classificationOverride: '',
            overrideReason: '',
        }));
    };

    const addWorkItem = (event) => {
        event.preventDefault();
        const selectedCourseId = itemDraft.courseId || courses[0]?.id || null;
        if (activityRule?.course_required && !selectedCourseId) {
            setError('Add a course before recording this work.');
            return;
        }
        if (activityRule?.topic_required && !itemDraft.topic.trim()) {
            setError('Enter a topic or teaching week for this work.');
            return;
        }
        const id = newId('work');
        const hours = Number(itemDraft.hours);
        const kind = isComposite ? 'activity' : 'direct_hours';
        const occasionId = itemDraft.existingOccasionId || id;
        const payload = {
            id,
            kind,
            date: itemDraft.date,
            occasion_id: occasionId,
            course_id: selectedCourseId,
            topic: itemDraft.topic.trim() || null,
            activity: itemDraft.activity,
            variant: itemDraft.variant,
            delivered_quantity: isComposite ? hours : null,
            actual_hours: isComposite ? null : hours,
            actual_associated_hours: isComposite && itemDraft.actualAssociatedHours !== ''
                ? Number(itemDraft.actualAssociatedHours)
                : null,
            required_or_approved: isComposite ? false : itemDraft.requiredOrApproved,
            classification_override: itemDraft.classificationOverride || null,
            override_reason: itemDraft.classificationOverride ? itemDraft.overrideReason.trim() : null,
        };
        setWorkItems((current) => [...current, { id, date: itemDraft.date, payload }]);
        setError('');
        setItemDraft((current) => ({
            ...initialItem(current.date),
            courseId: current.courseId,
            activity: current.activity,
            variant: activityRule.default_variant,
        }));
    };

    const removeWorkItem = (id) => setWorkItems((current) => current.filter((item) => item.id !== id));
    const removeCourse = (id) => {
        setCourses((current) => current.filter((course) => course.id !== id));
        setWorkItems((current) => current.filter((item) => item.payload.course_id !== id));
    };

    const startEntryForDate = (date) => {
        setItemDraft((current) => ({ ...current, date, existingOccasionId: '' }));
        formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    return (
        <>
            <section className="academic-intro panel">
                <div>
                    <p className="section-kicker">Activity-paid work</p>
                    <h1>QUT Sessional Academic Staff</h1>
                    <p>Record delivered activities and required direct hours. Dates drive repeat classification; clock times are not needed.</p>
                </div>
                <label className="academic-period-control">
                    Fortnight starts
                    <input
                        type="date"
                        value={periodStart}
                        onChange={(event) => {
                            setPeriodStart(event.target.value);
                            setItemDraft((current) => ({ ...current, date: event.target.value, existingOccasionId: '' }));
                        }}
                    />
                    <span>Monday to Sunday, two weeks</span>
                </label>
            </section>

            <section className="academic-setup-grid">
                <section className="academic-courses panel">
                    <div className="academic-section-heading">
                        <div><p className="section-kicker">Courses taught</p><h2>Add your courses</h2></div>
                        <span>{courses.length} added</span>
                    </div>
                    <form onSubmit={addCourse} className="academic-course-form">
                        <label>Course code<input value={courseDraft.code} onChange={(event) => setCourseDraft({ ...courseDraft, code: event.target.value })} placeholder="e.g. LLB101" /></label>
                        <label>Course name<input value={courseDraft.name} onChange={(event) => setCourseDraft({ ...courseDraft, name: event.target.value })} placeholder="Optional" /></label>
                        <label>Rate basis for this course<select value={courseDraft.eligibility} onChange={(event) => setCourseDraft({ ...courseDraft, eligibility: event.target.value })}>{Object.entries(ruleset?.eligibility || {}).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><span>This is based on your qualification or coordination duties, not the course level.</span></label>
                        <button className="academic-primary-button" type="submit">Add course</button>
                    </form>
                    <div className="academic-course-list">
                        {courses.length === 0 && <p className="academic-empty-copy">Add a course before recording teaching or marking.</p>}
                        {courses.map((course) => <div className="academic-course-chip" key={course.id}><div><strong>{course.code}</strong><span>{ruleset?.eligibility?.[course.eligibility] || course.eligibility}</span></div><button type="button" onClick={() => removeCourse(course.id)} aria-label={`Remove ${course.code}`}>×</button></div>)}
                    </div>
                </section>

                <section className="academic-entry panel" ref={formRef}>
                    <div className="academic-section-heading">
                        <div><p className="section-kicker">New work item</p><h2>{isComposite ? 'Teaching activity' : 'Direct hours'}</h2></div>
                        <span className={`academic-basis-badge ${isComposite ? 'is-activity' : 'is-direct'}`}>{isComposite ? 'Activity rate' : 'Hourly rate'}</span>
                    </div>
                    <form onSubmit={addWorkItem} className="academic-item-form" noValidate>
                        <label>Date<input required type="date" min={periodStart} max={periodEnd} value={itemDraft.date} onChange={(event) => setItemDraft({ ...itemDraft, date: event.target.value, existingOccasionId: '' })} /></label>
                        <label>Course taught<select required={activityRule?.course_required} value={itemDraft.courseId} onChange={(event) => setItemDraft({ ...itemDraft, courseId: event.target.value, topic: '' })}><option value="">No course</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.code}{course.name ? ` — ${course.name}` : ''}</option>)}</select></label>
                        <label>Work type<select value={itemDraft.activity} onChange={(event) => selectActivity(event.target.value)}>{Object.entries(ruleset?.activities || {}).map(([value, activity]) => <option value={value} key={value}>{activity.label}</option>)}</select></label>
                        <label>Variant<select value={itemDraft.variant} onChange={(event) => setItemDraft({ ...itemDraft, variant: event.target.value })}>{Object.entries(variants).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
                        {(activityRule?.topic_required || itemDraft.topic) && <label className="academic-wide-field">Topic or teaching week<input required={activityRule?.topic_required} list={knownTopics.length ? 'academic-topic-options' : undefined} value={itemDraft.topic} onChange={(event) => setItemDraft({ ...itemDraft, topic: event.target.value })} placeholder="e.g. Week 3 - Negligence" />{knownTopics.length > 0 && <><datalist id="academic-topic-options">{knownTopics.map((topic) => <option value={topic} key={topic} />)}</datalist><span>Previously used topics for this course appear as suggestions.</span></>}</label>}
                        <label>{activityRule?.quantity_label || 'Hours'}<input required type="number" min="0.01" max="24" step="0.25" value={itemDraft.hours} onChange={(event) => setItemDraft({ ...itemDraft, hours: event.target.value })} />{activityRule?.quantity_help && <span>{activityRule.quantity_help}</span>}</label>
                        {isComposite && <label>Associated work actually done<input type="number" min="0" max="200" step="0.25" value={itemDraft.actualAssociatedHours} onChange={(event) => setItemDraft({ ...itemDraft, actualAssociatedHours: event.target.value })} placeholder="Optional" /><span>Preparation, consultation or related work outside the delivered activity.</span></label>}
                        {sameDateOccasions.length > 0 && <label>Was this part of the same work occasion?<select value={itemDraft.existingOccasionId} onChange={(event) => setItemDraft({ ...itemDraft, existingOccasionId: event.target.value })}><option value="">No — treat it as a separate occasion</option>{sameDateOccasions.map((occasion) => <option value={occasion.id} key={occasion.id}>Yes — same occasion as {occasion.label}</option>)}</select><span>This only affects the two-hour minimum-engagement review.</span></label>}
                        {activityRule?.repeatable && <label>Repeat classification<select value={itemDraft.classificationOverride} onChange={(event) => setItemDraft({ ...itemDraft, classificationOverride: event.target.value })}><option value="">Automatic</option><option value="original">Override: original</option><option value="repeat">Override: repeat</option></select></label>}
                        {itemDraft.classificationOverride && <label className="academic-wide-field">Override reason<input required value={itemDraft.overrideReason} onChange={(event) => setItemDraft({ ...itemDraft, overrideReason: event.target.value })} /></label>}
                        {!isComposite && <label className="academic-confirmation"><input type="checkbox" checked={itemDraft.requiredOrApproved} onChange={(event) => setItemDraft({ ...itemDraft, requiredOrApproved: event.target.checked })} /><span>These hours were required or approved.</span></label>}
                        <button className="academic-primary-button academic-add-item" type="submit" disabled={!ruleset || courses.length === 0 && activityRule?.course_required}>Add to fortnight</button>
                    </form>
                </section>
            </section>

            {error && <p className="academic-error panel" role="alert">{error}</p>}

            <section className="academic-calendar panel" aria-label="Academic work fortnight">
                {[0, 1].map((week) => <div className="academic-week" key={week}>
                    <div className="academic-week-heading"><span>Week {week + 1}</span><strong>{periodDates[week * 7]} – {periodDates[week * 7 + 6]}</strong></div>
                    <div className="academic-days">
                        {periodDates.slice(week * 7, week * 7 + 7).map((date) => {
                            const dateItems = visibleItems.filter((item) => item.date === date);
                            return <article className={`academic-day ${dateItems.length ? 'has-work' : ''}`} key={date}>
                                <header><div><span>{parseDate(date).toLocaleDateString('en-AU', { weekday: 'short' })}</span><strong>{parseDate(date).getDate()}</strong></div><button type="button" onClick={() => startEntryForDate(date)}>+ Add</button></header>
                                {dateItems.length === 0 ? <p>No work entered</p> : <div className="academic-day-items">{dateItems.map((item) => {
                                    const line = resultsById[item.id];
                                    const course = courses.find((value) => value.id === item.payload.course_id);
                                    return <div className="academic-day-item" key={item.id}>
                                        <div className="academic-day-item-top"><span>{course?.code || 'General'}</span><button type="button" onClick={() => removeWorkItem(item.id)} aria-label="Remove work item">×</button></div>
                                        <strong>{line?.classification_label || ruleset?.activities?.[item.payload.activity]?.label}</strong>
                                        <small>{item.payload.topic || ruleset?.activities?.[item.payload.activity]?.variants?.[item.payload.variant] || ''}</small>
                                        <div className="academic-item-metrics"><span>{line ? Number(line.quantity).toFixed(2) : item.payload.delivered_quantity || item.payload.actual_hours} hrs</span><b>{line ? formatCurrency(line.pay) : 'Calculating'}</b></div>
                                        {line?.final_classification === 'repeat' && <em>Repeat</em>}
                                    </div>;
                                })}</div>}
                            </article>;
                        })}
                    </div>
                </div>)}
            </section>

            <section className="academic-summary panel">
                <div className="academic-total"><p className="section-kicker">Expected gross pay</p><strong>{formatCurrency(result?.total_pay || 0)}</strong><span>Before tax, superannuation and deductions</span></div>
                <div className="academic-summary-metrics">
                    <div><span>Activity pay</span><strong>{formatCurrency(result?.activity_pay || 0)}</strong><small>{result?.delivered_hours || 0} delivered hrs</small></div>
                    <div><span>Direct-hours pay</span><strong>{formatCurrency(result?.direct_hours_pay || 0)}</strong><small>{result?.direct_hours || 0} paid hrs</small></div>
                    <div><span>Incorporated time</span><strong>{result?.incorporated_hours || 0} hrs</strong><small>{result?.actual_associated_hours || 0} actual entered</small></div>
                </div>
                {(result?.review_warnings || []).length > 0 && <div className="academic-review"><h3>Review these items</h3><ul>{result.review_warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div>}
            </section>
        </>
    );
}
