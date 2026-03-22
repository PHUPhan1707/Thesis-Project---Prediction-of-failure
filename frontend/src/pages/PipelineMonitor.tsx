import { useCallback, useEffect, useRef, useState } from 'react';
import './PipelineMonitor.css';

/* ── Types ───────────────────────────────────────────────── */

interface StepState {
    step: number;
    name: string;
    status: 'pending' | 'running' | 'completed' | 'error';
    detail: string;
}

interface LogEntry {
    id: number;
    message: string;
    level: string;
    timestamp: string;
}

interface ProgressState {
    step: number;
    current: number;
    total: number;
    percent: number;
    label: string;
}

interface PipelineSummary {
    courses_discovered: number;
    courses_fetched: number;
    students_featured: number;
    courses_trained: Array<{
        base_name: string;
        model_name: string;
        accuracy: number;
        f1_score: number;
        auc_roc: number;
        student_count: number;
    }>;
    courses_predicted: Array<{
        base_name: string;
        predicted_count: number;
        high_risk_count: number;
    }>;
    elapsed_seconds: number;
    errors: string[];
}

interface LocalCourse {
    course_id: string;
    course_name: string | null;
    student_count: number;
}

/* ── API ─────────────────────────────────────────────────── */

function getApiBase() {
    const origin =
        (import.meta.env.VITE_API_URL as string | undefined) ||
        'http://localhost:5000';
    return `${origin.replace(/\/$/, '')}/api/pipeline`;
}

/* ── Component ───────────────────────────────────────────── */

const STEP_NAMES = [
    'Discover khóa học',
    'Fetch dữ liệu từ MOOC',
    'Feature Engineering',
    'Training Model',
    'Prediction',
];

export default function PipelineMonitor() {
    const [steps, setSteps] = useState<StepState[]>(
        STEP_NAMES.map((name, i) => ({
            step: i + 1,
            name,
            status: 'pending',
            detail: '',
        })),
    );
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [progress, setProgress] = useState<ProgressState | null>(null);
    const [running, setRunning] = useState(false);
    const [summary, setSummary] = useState<PipelineSummary | null>(null);
    const [loading, setLoading] = useState(true);

    // Selective fetch modal state
    const [showSelectModal, setShowSelectModal] = useState(false);
    const [localCourses, setLocalCourses] = useState<LocalCourse[]>([]);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [loadingCourses, setLoadingCourses] = useState(false);

    const logRef = useRef<HTMLDivElement>(null);
    const eventSourceRef = useRef<EventSource | null>(null);
    const logIdRef = useRef(0);

    const addLog = useCallback(
        (message: string, level = 'info', timestamp = '') => {
            logIdRef.current += 1;
            setLogs((prev) => [
                ...prev,
                {
                    id: logIdRef.current,
                    message,
                    level,
                    timestamp: timestamp || new Date().toLocaleTimeString('vi-VN'),
                },
            ]);
        },
        [],
    );

    const loadStatus = useCallback(async () => {
        try {
            const r = await fetch(`${getApiBase()}/status`);
            if (!r.ok) throw new Error(`Status ${r.status}`);
            const data = await r.json();
            setRunning(data.running);
            if (data.summary) setSummary(data.summary);
        } catch {
            /* ignore on initial load */
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadStatus();
    }, [loadStatus]);

    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [logs]);

    const connectSSE = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        const es = new EventSource(`${getApiBase()}/stream`);
        eventSourceRef.current = es;

        es.addEventListener('log', (e) => {
            const d = JSON.parse(e.data);
            addLog(d.message, d.level, d.timestamp);
        });

        es.addEventListener('step_update', (e) => {
            const d = JSON.parse(e.data);
            setSteps((prev) =>
                prev.map((s) =>
                    s.step === d.step
                        ? { ...s, status: d.status, detail: d.detail }
                        : s,
                ),
            );
        });

        es.addEventListener('progress', (e) => {
            const d = JSON.parse(e.data);
            setProgress({
                step: d.step,
                current: d.current,
                total: d.total,
                percent: d.percent,
                label: d.label,
            });
        });

        es.addEventListener('pipeline_start', () => {
            setRunning(true);
            setSummary(null);
            setSteps(
                STEP_NAMES.map((name, i) => ({
                    step: i + 1,
                    name,
                    status: 'pending',
                    detail: '',
                })),
            );
        });

        es.addEventListener('done', (e) => {
            const d = JSON.parse(e.data);
            setSummary(d.summary);
            setRunning(false);
            setProgress(null);
            es.close();
        });

        es.onerror = () => {
            es.close();
        };
    }, [addLog]);

    const resetState = () => {
        setLogs([]);
        setSummary(null);
        setProgress(null);
        setSteps(
            STEP_NAMES.map((name, i) => ({
                step: i + 1,
                name,
                status: 'pending',
                detail: '',
            })),
        );
    };

    const handleStart = async () => {
        try {
            resetState();
            const r = await fetch(`${getApiBase()}/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            });
            const data = await r.json();
            if (data.success) {
                setRunning(true);
                setTimeout(connectSSE, 300);
            } else {
                addLog(data.message || 'Không thể bắt đầu pipeline', 'error');
            }
        } catch (e: any) {
            addLog(`Lỗi: ${e.message}`, 'error');
        }
    };

    const handleStop = async () => {
        try {
            await fetch(`${getApiBase()}/stop`, { method: 'POST' });
            addLog('Đã gửi lệnh dừng...', 'warning');
        } catch (e: any) {
            addLog(`Lỗi dừng: ${e.message}`, 'error');
        }
    };

    // ── Selective Fetch ──────────────────────────────────────

    const openSelectModal = async () => {
        setShowSelectModal(true);
        setSelectedIds(new Set());
        setLoadingCourses(true);
        try {
            const r = await fetch(`${getApiBase()}/local-courses`);
            const data = await r.json();
            setLocalCourses(data.courses || []);
        } catch {
            setLocalCourses([]);
        } finally {
            setLoadingCourses(false);
        }
    };

    const toggleCourse = (id: string) => {
        setSelectedIds((prev) => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    };

    const toggleAll = () => {
        if (selectedIds.size === localCourses.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(localCourses.map((c) => c.course_id)));
        }
    };

    const handleFetchSelected = async () => {
        if (selectedIds.size === 0) return;
        setShowSelectModal(false);
        resetState();
        try {
            const r = await fetch(`${getApiBase()}/fetch-selected`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ course_ids: Array.from(selectedIds) }),
            });
            const data = await r.json();
            if (data.success) {
                setRunning(true);
                setTimeout(connectSSE, 300);
            } else {
                addLog(data.message || 'Không thể fetch', 'error');
            }
        } catch (e: any) {
            addLog(`Lỗi: ${e.message}`, 'error');
        }
    };

    const getDisplayName = (c: LocalCourse) =>
        c.course_name || c.course_id.split(':')[1]?.split('+').slice(0, 2).join(' / ') || c.course_id;

    /* ── Render ───────────────────────────────────────────── */

    if (loading) {
        return (
            <div className="pipeline-page">
                <div className="pipeline-loading">
                    <div className="loading-spinner" />
                    <p>Đang tải...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="pipeline-page">
            {/* Controls */}
            <div className="pipeline-controls">
                <button
                    className="btn-pipeline btn-start"
                    onClick={handleStart}
                    disabled={running}
                >
                    {running ? '⏳ Đang chạy...' : '▶ Chạy Full Pipeline'}
                </button>
                <button
                    className="btn-pipeline btn-select-fetch"
                    onClick={openSelectModal}
                    disabled={running}
                    title="Chọn khóa học cụ thể để fetch data"
                >
                    ⚡ Fetch có chọn lọc
                </button>
                <button
                    className="btn-pipeline btn-stop"
                    onClick={handleStop}
                    disabled={!running}
                >
                    ⏹ Dừng
                </button>
                <button
                    className="btn-pipeline btn-refresh"
                    onClick={loadStatus}
                >
                    🔄 Refresh
                </button>
                <span className={`run-badge ${running ? 'badge-running' : 'badge-idle'}`}>
                    {running ? '⏳ Đang chạy' : '⏸ Sẵn sàng'}
                </span>
            </div>

            {/* Stepper */}
            <div className="pipeline-stepper">
                {steps.map((s, i) => (
                    <div key={s.step} className={`step-item step-${s.status}`}>
                        <div className="step-connector-line">
                            {i > 0 && <div className={`connector connector-${steps[i - 1].status}`} />}
                        </div>
                        <div className="step-circle">
                            {s.status === 'completed' ? (
                                '✓'
                            ) : s.status === 'running' ? (
                                <span className="step-spinner" />
                            ) : s.status === 'error' ? (
                                '✕'
                            ) : (
                                s.step
                            )}
                        </div>
                        <div className="step-info">
                            <div className="step-name">{s.name}</div>
                            {s.detail && <div className="step-detail">{s.detail}</div>}
                            {progress && progress.step === s.step && s.status === 'running' && (
                                <div className="step-progress">
                                    <div className="progress-bar-track">
                                        <div
                                            className="progress-bar-fill"
                                            style={{ width: `${progress.percent}%` }}
                                        />
                                    </div>
                                    <span className="progress-label">
                                        {progress.current}/{progress.total} — {progress.label}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Live Logs */}
            <div className="pipeline-logs-section">
                <div className="logs-header">
                    <h3>📜 Live Logs</h3>
                    <span className="logs-count">{logs.length} dòng</span>
                </div>
                <div className="logs-terminal" ref={logRef}>
                    {logs.length === 0 ? (
                        <div className="logs-empty">
                            Nhấn "▶ Chạy Full Pipeline" hoặc "⚡ Fetch có chọn lọc" để bắt đầu...
                        </div>
                    ) : (
                        logs.map((log) => (
                            <div key={log.id} className={`log-line log-${log.level}`}>
                                <span className="log-time">{log.timestamp}</span>
                                <span className="log-msg">{log.message}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Summary */}
            {summary && (
                <div className="pipeline-summary">
                    <h3>📊 Kết quả Pipeline</h3>
                    <div className="summary-grid">
                        <div className="summary-card">
                            <div className="summary-value">{summary.courses_discovered}</div>
                            <div className="summary-label">Khóa học phát hiện</div>
                        </div>
                        <div className="summary-card">
                            <div className="summary-value">{summary.courses_fetched}</div>
                            <div className="summary-label">Khóa học đã fetch</div>
                        </div>
                        <div className="summary-card">
                            <div className="summary-value">{summary.students_featured}</div>
                            <div className="summary-label">Student features</div>
                        </div>
                        <div className="summary-card">
                            <div className="summary-value">{summary.courses_trained.length}</div>
                            <div className="summary-label">Nhóm đã train</div>
                        </div>
                        <div className="summary-card">
                            <div className="summary-value">
                                {summary.courses_predicted.reduce(
                                    (s, p) => s + p.predicted_count,
                                    0,
                                )}
                            </div>
                            <div className="summary-label">SV đã predict</div>
                        </div>
                        <div className="summary-card">
                            <div className="summary-value">{summary.elapsed_seconds}s</div>
                            <div className="summary-label">Thời gian</div>
                        </div>
                    </div>

                    {summary.courses_trained.length > 0 && (
                        <div className="summary-details">
                            <h4>Kết quả Training</h4>
                            <table className="summary-table">
                                <thead>
                                    <tr>
                                        <th>Môn học</th>
                                        <th>Model</th>
                                        <th>SV</th>
                                        <th>Accuracy</th>
                                        <th>F1</th>
                                        <th>AUC</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {summary.courses_trained.map((t) => (
                                        <tr key={t.model_name}>
                                            <td>{t.base_name}</td>
                                            <td className="model-tag">{t.model_name}</td>
                                            <td>{t.student_count}</td>
                                            <td>{(t.accuracy * 100).toFixed(1)}%</td>
                                            <td>{(t.f1_score * 100).toFixed(1)}%</td>
                                            <td>{(t.auc_roc * 100).toFixed(1)}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {summary.errors.length > 0 && (
                        <div className="summary-errors">
                            <h4>Lỗi</h4>
                            {summary.errors.map((err, i) => (
                                <div key={i} className="error-item">
                                    {err}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* ── Selective Fetch Modal ─────────────────────── */}
            {showSelectModal && (
                <div className="select-modal-overlay" onClick={() => setShowSelectModal(false)}>
                    <div className="select-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="select-modal-header">
                            <div>
                                <h3>⚡ Fetch có chọn lọc</h3>
                                <p className="select-modal-desc">
                                    Chọn khóa học muốn fetch grades &amp; features. Chỉ Step 2+3 được chạy.
                                </p>
                            </div>
                            <button className="select-modal-close" onClick={() => setShowSelectModal(false)}>✕</button>
                        </div>

                        <div className="select-modal-actions-top">
                            <button className="btn-select-all" onClick={toggleAll}>
                                {selectedIds.size === localCourses.length ? '☐ Bỏ chọn tất cả' : '☑ Chọn tất cả'}
                            </button>
                            <span className="select-count-info">
                                Đã chọn: <strong>{selectedIds.size}</strong> / {localCourses.length} khóa học
                            </span>
                        </div>

                        <div className="select-modal-list">
                            {loadingCourses ? (
                                <div className="select-loading">
                                    <div className="loading-spinner" />
                                    <span>Đang tải danh sách...</span>
                                </div>
                            ) : localCourses.length === 0 ? (
                                <div className="select-empty">Không tìm thấy khóa học nào trong DB.</div>
                            ) : (
                                localCourses.map((course) => {
                                    const checked = selectedIds.has(course.course_id);
                                    return (
                                        <label
                                            key={course.course_id}
                                            className={`course-select-row ${checked ? 'selected' : ''}`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={checked}
                                                onChange={() => toggleCourse(course.course_id)}
                                                className="course-checkbox"
                                            />
                                            <div className="course-select-info">
                                                <span className="course-select-name">
                                                    {getDisplayName(course)}
                                                </span>
                                                <span className="course-select-meta">
                                                    <span className="meta-id">{course.course_id.split(':')[1]?.split('+').slice(0,2).join('+')||course.course_id}</span>
                                                    <span className="meta-count">👥 {course.student_count} SV</span>
                                                </span>
                                            </div>
                                        </label>
                                    );
                                })
                            )}
                        </div>

                        <div className="select-modal-footer">
                            <button className="btn-pipeline btn-refresh" onClick={() => setShowSelectModal(false)}>
                                Hủy
                            </button>
                            <button
                                className="btn-pipeline btn-fetch-confirm"
                                onClick={handleFetchSelected}
                                disabled={selectedIds.size === 0}
                            >
                                ⚡ Fetch {selectedIds.size > 0 ? `${selectedIds.size} khóa học` : ''}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
