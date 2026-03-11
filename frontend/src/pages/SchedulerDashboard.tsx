import { useCallback, useEffect, useState } from 'react';
import './SchedulerDashboard.css';

/* ── Types ────────────────────────────────────────────────── */

interface CourseGroup {
    base_name: string;
    status: 'active' | 'waiting' | 'no_data';
    course_count: number;
    course_ids: string[];
    labeled_students: number;
    min_required: number;
    model_name: string | null;
    new_since_last_train: number;
    retrain_threshold: number;
    last_train_at: string | null;
}

interface SchedulerStatus {
    scheduler_enabled: boolean;
    interval_days: number;
    groups: CourseGroup[];
    total_groups: number;
}

interface HistoryRecord {
    id: number;
    base_name: string;
    course_ids: string;
    model_name: string | null;
    action: string;
    labeled_student_count: number | null;
    predicted_student_count: number | null;
    accuracy: number | null;
    f1_score: number | null;
    auc_roc: number | null;
    status: string;
    message: string | null;
    started_at: string;
    completed_at: string | null;
}

/* ── API helpers ──────────────────────────────────────────── */

function getApiBase() {
    const origin =
        (import.meta.env.VITE_API_URL as string | undefined) ||
        'http://localhost:5000';
    return `${origin.replace(/\/$/, '')}/api/scheduler`;
}

async function fetchSchedulerStatus(): Promise<SchedulerStatus> {
    const r = await fetch(`${getApiBase()}/status`);
    if (!r.ok) throw new Error(`Status: ${r.status}`);
    return r.json();
}

async function fetchSchedulerHistory(): Promise<{ history: HistoryRecord[] }> {
    const r = await fetch(`${getApiBase()}/history?limit=30`);
    if (!r.ok) throw new Error(`Status: ${r.status}`);
    return r.json();
}

async function triggerScheduler(dryRun: boolean): Promise<any> {
    const r = await fetch(`${getApiBase()}/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run: dryRun }),
    });
    if (!r.ok) throw new Error(`Status: ${r.status}`);
    return r.json();
}

/* ── Component ────────────────────────────────────────────── */

export default function SchedulerDashboard() {
    const [status, setStatus] = useState<SchedulerStatus | null>(null);
    const [history, setHistory] = useState<HistoryRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [triggering, setTriggering] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'status' | 'history'>('status');

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const [st, hist] = await Promise.all([
                fetchSchedulerStatus(),
                fetchSchedulerHistory(),
            ]);
            setStatus(st);
            setHistory(hist.history);
        } catch (e: any) {
            setError(e.message || 'Không thể kết nối server');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleTrigger = async (dryRun: boolean) => {
        try {
            setTriggering(true);
            await triggerScheduler(dryRun);
            // Reload data after a short delay
            setTimeout(loadData, 2000);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setTriggering(false);
        }
    };

    /* ── Renders ──────────────────────────────────────────── */

    if (loading) {
        return (
            <div className="scheduler-page">
                <div className="scheduler-loading">
                    <div className="loading-spinner" />
                    <p>Đang tải dữ liệu scheduler...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="scheduler-page">
                <div className="scheduler-error">
                    <span className="error-icon">⚠️</span>
                    <h3>Lỗi kết nối</h3>
                    <p>{error}</p>
                    <button className="btn-retry" onClick={loadData}>
                        Thử lại
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="scheduler-page">
            {/* Header */}
            <div className="scheduler-header">
                <div className="header-info">
                    <h2>
                        <span className="header-icon">🤖</span> MLOps Scheduler
                    </h2>
                    <p className="header-desc">
                        Tự động kiểm tra, train, predict và retrain model cho các khóa học
                    </p>
                </div>
                <div className="header-actions">
                    <span
                        className={`status-badge ${status?.scheduler_enabled ? 'enabled' : 'disabled'}`}
                    >
                        {status?.scheduler_enabled ? '🟢 Đang bật' : '🔴 Đang tắt'}
                    </span>
                    <span className="interval-badge">
                        ⏰ Mỗi {status?.interval_days} ngày
                    </span>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions-bar">
                <button
                    className="btn-trigger"
                    onClick={() => handleTrigger(false)}
                    disabled={triggering}
                >
                    {triggering ? '⏳ Đang chạy...' : '🚀 Trigger ngay'}
                </button>
                <button
                    className="btn-trigger dry-run"
                    onClick={() => handleTrigger(true)}
                    disabled={triggering}
                >
                    🧪 Dry Run
                </button>
                <button className="btn-refresh" onClick={loadData}>
                    🔄 Refresh
                </button>
            </div>

            {/* Tabs */}
            <div className="scheduler-tabs">
                <button
                    className={`tab-btn ${activeTab === 'status' ? 'active' : ''}`}
                    onClick={() => setActiveTab('status')}
                >
                    📊 Trạng thái ({status?.total_groups || 0} nhóm)
                </button>
                <button
                    className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
                    onClick={() => setActiveTab('history')}
                >
                    📜 Lịch sử ({history.length})
                </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'status' ? (
                <StatusTab groups={status?.groups || []} />
            ) : (
                <HistoryTab records={history} />
            )}
        </div>
    );
}

/* ── Status Tab ────────────────────────────────────────── */

function StatusTab({ groups }: { groups: CourseGroup[] }) {
    if (groups.length === 0) {
        return (
            <div className="empty-state">
                <span className="empty-icon">📭</span>
                <h3>Chưa có khóa học nào</h3>
                <p>Hệ thống chưa phát hiện khóa học nào trong database</p>
            </div>
        );
    }

    return (
        <div className="groups-grid">
            {groups.map((g) => (
                <GroupCard key={g.base_name} group={g} />
            ))}
        </div>
    );
}

function GroupCard({ group }: { group: CourseGroup }) {
    const statusConfig: Record<string, { label: string; color: string; icon: string }> = {
        active: { label: 'Đang hoạt động', color: '#10b981', icon: '✅' },
        waiting: { label: 'Chờ dữ liệu', color: '#f59e0b', icon: '⏳' },
        no_data: { label: 'Chưa có data', color: '#6b7280', icon: '📭' },
    };
    const cfg = statusConfig[group.status] || statusConfig.no_data;
    const progress = Math.min(
        (group.labeled_students / group.min_required) * 100,
        100
    );

    return (
        <div className="group-card">
            <div className="group-card-header">
                <h3 className="group-name">{group.base_name}</h3>
                <span className="group-status" style={{ color: cfg.color }}>
                    {cfg.icon} {cfg.label}
                </span>
            </div>

            <div className="group-stats">
                <div className="stat-row">
                    <span className="stat-label">Khóa học</span>
                    <span className="stat-value">{group.course_count}</span>
                </div>
                <div className="stat-row">
                    <span className="stat-label">SV có kết quả</span>
                    <span className="stat-value">
                        {group.labeled_students.toLocaleString()} / {group.min_required.toLocaleString()}
                    </span>
                </div>
                {group.model_name && (
                    <>
                        <div className="stat-row">
                            <span className="stat-label">Model</span>
                            <span className="stat-value model-tag">{group.model_name}</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">SV mới (chưa retrain)</span>
                            <span className="stat-value">
                                +{group.new_since_last_train} / {group.retrain_threshold}
                            </span>
                        </div>
                    </>
                )}
                {group.last_train_at && (
                    <div className="stat-row">
                        <span className="stat-label">Train lần cuối</span>
                        <span className="stat-value">
                            {new Date(group.last_train_at).toLocaleDateString('vi-VN')}
                        </span>
                    </div>
                )}
            </div>

            {/* Progress bar for waiting state */}
            {group.status === 'waiting' && (
                <div className="progress-section">
                    <div className="progress-bar-bg">
                        <div
                            className="progress-bar-fill"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <span className="progress-text">{progress.toFixed(0)}%</span>
                </div>
            )}

            {/* Course IDs */}
            <div className="group-courses">
                {group.course_ids.slice(0, 3).map((cid) => (
                    <span key={cid} className="course-chip" title={cid}>
                        {cid.length > 35 ? `...${cid.slice(-30)}` : cid}
                    </span>
                ))}
                {group.course_ids.length > 3 && (
                    <span className="course-chip more">
                        +{group.course_ids.length - 3} khóa
                    </span>
                )}
            </div>
        </div>
    );
}

/* ── History Tab ───────────────────────────────────────── */

function HistoryTab({ records }: { records: HistoryRecord[] }) {
    if (records.length === 0) {
        return (
            <div className="empty-state">
                <span className="empty-icon">📜</span>
                <h3>Chưa có lịch sử</h3>
                <p>Scheduler chưa chạy lần nào. Nhấn "Trigger ngay" để bắt đầu.</p>
            </div>
        );
    }

    const actionLabels: Record<string, { label: string; icon: string }> = {
        initial_train: { label: 'Train lần đầu', icon: '🏋️' },
        retrain: { label: 'Retrain', icon: '🔄' },
        predict: { label: 'Predict', icon: '🤖' },
        check: { label: 'Kiểm tra', icon: '🔍' },
    };

    const statusColors: Record<string, string> = {
        success: '#10b981',
        failed: '#ef4444',
        skipped: '#6b7280',
    };

    return (
        <div className="history-table-wrapper">
            <table className="history-table">
                <thead>
                    <tr>
                        <th>Thời gian</th>
                        <th>Môn học</th>
                        <th>Hành động</th>
                        <th>Trạng thái</th>
                        <th>SV Train</th>
                        <th>SV Predict</th>
                        <th>Metrics</th>
                        <th>Ghi chú</th>
                    </tr>
                </thead>
                <tbody>
                    {records.map((r) => {
                        const act = actionLabels[r.action] || { label: r.action, icon: '❓' };
                        return (
                            <tr key={r.id}>
                                <td className="td-time">
                                    {r.started_at
                                        ? new Date(r.started_at).toLocaleString('vi-VN', {
                                            day: '2-digit',
                                            month: '2-digit',
                                            year: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit',
                                        })
                                        : '—'}
                                </td>
                                <td className="td-subject">{r.base_name}</td>
                                <td>
                                    <span className="action-badge">
                                        {act.icon} {act.label}
                                    </span>
                                </td>
                                <td>
                                    <span
                                        className="status-dot"
                                        style={{ color: statusColors[r.status] || '#6b7280' }}
                                    >
                                        ●
                                    </span>{' '}
                                    {r.status}
                                </td>
                                <td className="td-num">
                                    {r.labeled_student_count?.toLocaleString() ?? '—'}
                                </td>
                                <td className="td-num">
                                    {r.predicted_student_count?.toLocaleString() ?? '—'}
                                </td>
                                <td className="td-metrics">
                                    {r.accuracy != null ? (
                                        <span title={`Acc: ${(r.accuracy * 100).toFixed(1)}% | F1: ${((r.f1_score ?? 0) * 100).toFixed(1)}% | AUC: ${((r.auc_roc ?? 0) * 100).toFixed(1)}%`}>
                                            Acc {(r.accuracy * 100).toFixed(1)}%
                                        </span>
                                    ) : (
                                        '—'
                                    )}
                                </td>
                                <td className="td-msg" title={r.message ?? ''}>
                                    {r.message
                                        ? r.message.length > 50
                                            ? `${r.message.slice(0, 50)}…`
                                            : r.message
                                        : '—'}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
