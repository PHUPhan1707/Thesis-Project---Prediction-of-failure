import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import './PipelineLayout.css';

interface MOOCCourse {
    id: string;
    display_name: string;
    display_number_with_default: string;
    display_org_with_default: string;
}

interface LocalCourse {
    course_id: string;
    student_count: number;
    course_name?: string;
}

interface AuthStatus {
    configured: boolean;
    authenticated: boolean;
    email: string | null;
    authenticated_at: string | null;
}

function getApiBase() {
    const origin =
        (import.meta.env.VITE_API_URL as string | undefined) ||
        'http://localhost:5000';
    return origin.replace(/\/$/, '');
}

export default function PipelineLayout() {
    const [moocCourses, setMoocCourses] = useState<MOOCCourse[]>([]);
    const [localCourses, setLocalCourses] = useState<LocalCourse[]>([]);
    const [auth, setAuth] = useState<AuthStatus | null>(null);
    const [loadingMooc, setLoadingMooc] = useState(false);
    const [loggingIn, setLoggingIn] = useState(false);
    const [search, setSearch] = useState('');
    const [sidebarTab, setSidebarTab] = useState<'mooc' | 'local'>('local');

    const [sortBy, setSortBy] = useState<'name' | 'students' | 'status'>('name');

    useEffect(() => {
        fetchLocalCourses();
        fetchPipelineStatus();
    }, []);

    async function fetchLocalCourses() {
        try {
            const r = await fetch(`${getApiBase()}/api/pipeline/local-courses`);
            if (!r.ok) return;
            const data = await r.json();
            setLocalCourses(data.courses || []);
        } catch { /* ignore */ }
    }

    async function fetchPipelineStatus() {
        try {
            const r = await fetch(`${getApiBase()}/api/pipeline/status`);
            if (!r.ok) return;
            const data = await r.json();
            if (data.mooc_auth) setAuth(data.mooc_auth);
        } catch { /* ignore */ }
    }

    async function fetchMoocCourses() {
        setLoadingMooc(true);
        try {
            const r = await fetch(
                'https://mooc.vnuhcm.edu.vn/api/custom/v1/course-details/all/',
            );
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            const data = await r.json();
            const courses = data.data || data.courses || data || [];
            console.log('[Pipeline] MOOC courses loaded:', courses.length);
            setMoocCourses(Array.isArray(courses) ? courses : []);
            setSidebarTab('mooc');
        } catch (err) {
            console.error('[Pipeline] Failed to fetch MOOC courses:', err);
            setMoocCourses([]);
        } finally {
            setLoadingMooc(false);
        }
    }

    async function handleLoginMOOC() {
        setLoggingIn(true);
        try {
            const r = await fetch(`${getApiBase()}/api/pipeline/login-mooc`, {
                method: 'POST',
            });
            const data = await r.json();
            if (data.status) setAuth(data.status);
        } catch { /* ignore */ }
        finally { setLoggingIn(false); }
    }

    const localStudentMap = new Map(
        localCourses.map((c) => [c.course_id, c.student_count]),
    );

    const filteredMooc = moocCourses.filter(
        (c) =>
            c.display_name.toLowerCase().includes(search.toLowerCase()) ||
            c.id.toLowerCase().includes(search.toLowerCase()),
    );

    const filteredLocal = localCourses.filter((c) =>
        c.course_id.toLowerCase().includes(search.toLowerCase()) ||
        (c.course_name || '').toLowerCase().includes(search.toLowerCase()),
    );

    let sortedLocal = [...filteredLocal];
    if (sortBy === 'name') {
        sortedLocal.sort((a, b) => (a.course_name || a.course_id).localeCompare(b.course_name || b.course_id));
    } else if (sortBy === 'students') {
        sortedLocal.sort((a, b) => b.student_count - a.student_count);
    } else if (sortBy === 'status') {
        // Tất cả local đều có dữ liệu
        sortedLocal.sort((a, b) => b.student_count - a.student_count);
    }

    let sortedMooc = [...filteredMooc];
    if (sortBy === 'name') {
        sortedMooc.sort((a, b) => a.display_name.localeCompare(b.display_name));
    } else if (sortBy === 'students') {
        sortedMooc.sort((a, b) => {
            const countA = localStudentMap.get(a.id) || 0;
            const countB = localStudentMap.get(b.id) || 0;
            return countB - countA;
        });
    } else if (sortBy === 'status') {
        sortedMooc.sort((a, b) => {
            const hasA = localStudentMap.has(a.id) ? 1 : 0;
            const hasB = localStudentMap.has(b.id) ? 1 : 0;
            if (hasA !== hasB) return hasB - hasA; // synced first
            const countA = localStudentMap.get(a.id) || 0;
            const countB = localStudentMap.get(b.id) || 0;
            return countB - countA;
        });
    }

    const totalLocalStudents = localCourses.reduce(
        (sum, c) => sum + c.student_count,
        0,
    );

    return (
        <div className="pipeline-shell">
            {/* ── Sidebar ── */}
            <aside className="pipeline-sidebar">
                <div className="ps-brand">
                    <NavLink to="/" className="ps-back-link">
                        <span className="ps-back-arrow">←</span>
                        <span>Dashboard</span>
                    </NavLink>
                    <div className="ps-brand-main">
                        <div className="ps-brand-icon">🔬</div>
                        <div className="ps-brand-text">
                            <div className="ps-brand-title">Pipeline</div>
                            <div className="ps-brand-sub">ML Operations</div>
                        </div>
                    </div>
                </div>

                {/* Auth status */}
                <div className="ps-auth-section">
                    <div
                        className={`ps-auth-badge ${auth?.authenticated ? 'ps-auth-ok' : auth?.configured ? 'ps-auth-warn' : 'ps-auth-none'}`}
                    >
                        <span className="ps-auth-dot" />
                        <span>
                            {auth?.authenticated
                                ? `MOOC: ${auth.email}`
                                : auth?.configured
                                  ? 'Chưa đăng nhập'
                                  : 'Chưa cấu hình'}
                        </span>
                    </div>
                    {auth && !auth.authenticated && auth.configured && (
                        <button
                            className="ps-btn-login"
                            onClick={handleLoginMOOC}
                            disabled={loggingIn}
                        >
                            {loggingIn ? 'Đang login...' : 'Đăng nhập MOOC'}
                        </button>
                    )}
                </div>

                {/* Stats bar */}
                <div className="ps-stats-bar">
                    <div className="ps-stat">
                        <span className="ps-stat-value">{localCourses.length}</span>
                        <span className="ps-stat-label">Khóa học</span>
                    </div>
                    <div className="ps-stat-divider" />
                    <div className="ps-stat">
                        <span className="ps-stat-value">{totalLocalStudents.toLocaleString()}</span>
                        <span className="ps-stat-label">Sinh viên</span>
                    </div>
                    <div className="ps-stat-divider" />
                    <div className="ps-stat">
                        <span className="ps-stat-value">{moocCourses.length || '—'}</span>
                        <span className="ps-stat-label">MOOC</span>
                    </div>
                </div>

                {/* Tabs */}
                <div className="ps-tabs">
                    <button
                        className={`ps-tab ${sidebarTab === 'local' ? 'ps-tab-active' : ''}`}
                        onClick={() => setSidebarTab('local')}
                    >
                        Dữ liệu local ({localCourses.length})
                    </button>
                    <button
                        className={`ps-tab ${sidebarTab === 'mooc' ? 'ps-tab-active' : ''}`}
                        onClick={() => {
                            setSidebarTab('mooc');
                            if (moocCourses.length === 0) fetchMoocCourses();
                        }}
                    >
                        MOOC ({moocCourses.length || '...'})
                    </button>
                </div>

                {/* Filter and Sort bar */}
                <div className="ps-filter-bar">
                    <div className="ps-search">
                        <input
                            type="text"
                            placeholder="Tìm khóa học..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <select 
                        className="ps-sort-select" 
                        value={sortBy} 
                        onChange={(e) => setSortBy(e.target.value as any)}
                    >
                        <option value="name">A-Z</option>
                        <option value="students">Nhiều SV nhất</option>
                        <option value="status">Trạng thái (Có dữ liệu)</option>
                    </select>
                </div>

                {/* Course list (Limited to ~4 items height) */}
                <div className="ps-course-list" style={{ maxHeight: '330px', flex: 'none' }}>
                    {sidebarTab === 'local' ? (
                        sortedLocal.length > 0 ? (
                            sortedLocal.map((c) => (
                                <div key={c.course_id} className="ps-course-card">
                                    <div className="ps-course-name">
                                        {c.course_name || c.course_id.split(':').pop()?.replace(/\+/g, ' / ')}
                                    </div>
                                    <div className="ps-course-meta">
                                        <span className="ps-course-id">{c.course_id}</span>
                                    </div>
                                    <div className="ps-course-badge-row">
                                        <span className="ps-badge ps-badge-students">
                                            {c.student_count} sinh viên
                                        </span>
                                        <span className="ps-badge ps-badge-ready">Có dữ liệu</span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="ps-empty">
                                Chưa có khóa học nào.
                            </div>
                        )
                    ) : loadingMooc ? (
                        <div className="ps-loading-courses">
                            <div className="ps-spinner" />
                            <span>Đang tải từ MOOC...</span>
                        </div>
                    ) : sortedMooc.length > 0 ? (
                        sortedMooc.map((c) => {
                            const localCount = localStudentMap.get(c.id);
                            return (
                                <div key={c.id} className="ps-course-card">
                                    <div className="ps-course-name">{c.display_name}</div>
                                    <div className="ps-course-meta">
                                        <span className="ps-course-org">
                                            {c.display_org_with_default}
                                        </span>
                                        <span className="ps-dot">·</span>
                                        <span className="ps-course-num">
                                            {c.display_number_with_default}
                                        </span>
                                    </div>
                                    <div className="ps-course-badge-row">
                                        {localCount != null ? (
                                            <>
                                                <span className="ps-badge ps-badge-students">
                                                    {localCount} SV
                                                </span>
                                                <span className="ps-badge ps-badge-synced">
                                                    Đã sync
                                                </span>
                                            </>
                                        ) : (
                                            <span className="ps-badge ps-badge-new">
                                                Chưa fetch
                                            </span>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    ) : (
                        <div className="ps-empty">
                            <button
                                className="ps-btn-fetch"
                                onClick={fetchMoocCourses}
                                disabled={loadingMooc}
                            >
                                Tải danh sách
                            </button>
                        </div>
                    )}
                </div>

                <div className="ps-sidebar-footer">
                    <div className="ps-footer-chip">Pipeline • ML Operations</div>
                </div>
            </aside>

            {/* ── Main content ── */}
            <div className="pipeline-main">
                <header className="pipeline-topbar">
                    <div className="pt-left" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                        <div>
                            <h1 className="pt-title">Pipeline Operations</h1>
                            <span className="pt-subtitle">
                                Quản lý quy trình ML tự động
                            </span>
                        </div>
                        <nav className="pt-nav" style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-secondary)', padding: '0.3rem', borderRadius: '10px', marginLeft: '1rem', border: '1px solid var(--border-color)' }}>
                            <NavLink 
                                to="/pipeline" 
                                end
                                className={({ isActive }) => `pt-nav-link ${isActive ? 'active' : ''}`}
                                style={({ isActive }) => ({
                                    padding: '0.5rem 1rem',
                                    borderRadius: '8px',
                                    textDecoration: 'none',
                                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                                    background: isActive ? 'var(--bg-primary)' : 'transparent',
                                    fontWeight: isActive ? 600 : 500,
                                    boxShadow: isActive ? '0 2px 4px rgba(0,0,0,0.05)' : 'none',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                })}
                            >
                                🚀 Manual Run
                            </NavLink>
                            <NavLink 
                                to="/pipeline/scheduler" 
                                className={({ isActive }) => `pt-nav-link ${isActive ? 'active' : ''}`}
                                style={({ isActive }) => ({
                                    padding: '0.5rem 1rem',
                                    borderRadius: '8px',
                                    textDecoration: 'none',
                                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                                    background: isActive ? 'var(--bg-primary)' : 'transparent',
                                    fontWeight: isActive ? 600 : 500,
                                    boxShadow: isActive ? '0 2px 4px rgba(0,0,0,0.05)' : 'none',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                })}
                            >
                                🤖 Auto Scheduler
                            </NavLink>
                        </nav>
                    </div>
                    <div className="pt-right">
                        <ThemeToggle />
                    </div>
                </header>

                <main className="pipeline-content">
                    <Outlet />
                </main>

                <footer className="pipeline-footer">
                    <p>© 2025 Dropout Prediction System — ML Pipeline Operations</p>
                </footer>
            </div>
        </div>
    );
}
