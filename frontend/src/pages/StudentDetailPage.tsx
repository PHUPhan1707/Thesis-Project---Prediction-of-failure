import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDashboard } from '../context/DashboardContext';
import api from '../services/api';
import { ShapExplanationChart } from '../components/Dashboard/ShapExplanation';
import type { StudentDetail } from '../types';
import './StudentDetailPage.css';

export default function StudentDetailPage() {
    const { userId } = useParams<{ userId: string }>();
    const navigate = useNavigate();
    const { selectedCourse } = useDashboard();
    const [student, setStudent] = useState<StudentDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadStudent = async () => {
            if (!userId || !selectedCourse) return;

            try {
                setIsLoading(true);
                setError(null);
                const detail = await api.getStudentDetail(parseInt(userId), selectedCourse.course_id);
                setStudent(detail);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load student');
            } finally {
                setIsLoading(false);
            }
        };

        loadStudent();
    }, [userId, selectedCourse]);

    const riskLevelConfig = {
        HIGH: { color: 'red', label: 'Nguy cơ cao', icon: '🚨' },
        MEDIUM: { color: 'yellow', label: 'Nguy cơ TB', icon: '⚠️' },
        LOW: { color: 'green', label: 'Nguy cơ thấp', icon: '✅' },
    };

    const handleBack = () => {
        navigate('/details');
    };

    const handleEmail = () => {
        if (student?.email) {
            window.location.href = `mailto:${student.email}?subject=Hỗ trợ học tập - ${selectedCourse?.course_id || ''}`;
        }
    };

    const handlePhone = () => {
        alert('Tính năng gọi điện sẽ được tích hợp sau');
    };

    const handleMessage = () => {
        alert('Tính năng nhắn tin sẽ được tích hợp sau');
    };

    if (!selectedCourse) {
        return (
            <div className="student-detail-page">
                <div className="no-course-message">
                    <span className="icon">📚</span>
                    <h3>Chưa chọn khóa học</h3>
                    <p>Vui lòng quay lại và chọn một khóa học</p>
                    <button className="back-btn" onClick={() => navigate('/')}>
                        ← Quay lại
                    </button>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="student-detail-page">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <span>Đang tải thông tin sinh viên...</span>
                </div>
            </div>
        );
    }

    if (error || !student) {
        return (
            <div className="student-detail-page">
                <div className="error-container">
                    <span className="error-icon">⚠️</span>
                    <h3>Lỗi tải dữ liệu</h3>
                    <p>{error || 'Không tìm thấy sinh viên'}</p>
                    <button className="back-btn" onClick={handleBack}>
                        ← Quay lại
                    </button>
                </div>
            </div>
        );
    }

    const config = riskLevelConfig[student.risk_level] || riskLevelConfig.LOW;

    const getInitials = (name: string | null | undefined) => {
        if (!name) return 'SV';
        return name.split(' ').slice(-2).map(n => n[0]).join('').toUpperCase();
    };

    return (
        <div className="student-detail-page">
            {/* Header */}
            <header className="detail-header">
                <button className="back-btn" onClick={handleBack}>
                    ← Quay lại danh sách
                </button>
                <div className="header-student-info">
                    <div className={`header-avatar avatar-${config.color}`}>
                        {getInitials(student.full_name)}
                    </div>
                    <div className="header-text">
                        <h1>{student.full_name || 'Chưa có tên'}</h1>
                        <span className="header-email">{student.email}</span>
                    </div>
                    <div className={`header-risk-badge badge-${config.color}`}>
                        <span>{config.icon}</span>
                        <span>{config.label}</span>
                        <span className="risk-score">{student.fail_risk_score?.toFixed(1)}%</span>
                    </div>
                </div>
            </header>

            {/* Main Content Grid */}
            <main className="detail-main">
                {/* Left Column */}
                <div className="left-column">
                    <section className="overview-section">
                        <div className="section-header">
                            <span className="section-icon">📊</span>
                            <h2>Tổng Quan</h2>
                        </div>

                        <div className="overview-grid">
                            {/* Risk Score Card */}
                            <div className="metric-card highlight">
                                <div className="metric-header">
                                    <span className="metric-icon">📈</span>
                                    <span>Điểm Rủi Ro</span>
                                </div>
                                <div className={`metric-value value-${config.color}`}>
                                    {student.fail_risk_score?.toFixed(1) || 'N/A'}%
                                </div>
                                <div className="metric-bar">
                                    <div
                                        className={`bar-fill fill-${config.color}`}
                                        style={{ width: `${student.fail_risk_score || 0}%` }}
                                    ></div>
                                </div>
                            </div>

                            {/* Grade Card */}
                            <div className="metric-card">
                                <div className="metric-header">
                                    <span className="metric-icon">📝</span>
                                    <span>Điểm Trung Bình</span>
                                </div>
                                <div className="metric-value">
                                    {student.mooc_grade_percentage?.toFixed(1) || 'N/A'}%
                                </div>
                                <div className="metric-bar">
                                    <div
                                        className="bar-fill fill-blue"
                                        style={{ width: `${student.mooc_grade_percentage || 0}%` }}
                                    ></div>
                                </div>
                            </div>

                            {/* Progress Card */}
                            <div className="metric-card">
                                <div className="metric-header">
                                    <span className="metric-icon">📚</span>
                                    <span>Tiến Độ Học</span>
                                </div>
                                <div className="metric-value">
                                    {student.mooc_completion_rate?.toFixed(1) || 'N/A'}%
                                </div>
                                <div className="metric-bar">
                                    <div
                                        className="bar-fill fill-purple"
                                        style={{ width: `${student.mooc_completion_rate || 0}%` }}
                                    ></div>
                                </div>
                            </div>

                            {/* Last Activity Card */}
                            <div className="metric-card">
                                <div className="metric-header">
                                    <span className="metric-icon">📅</span>
                                    <span>Hoạt Động Cuối</span>
                                </div>
                                <div className="metric-value">
                                    {student.days_since_last_activity || 0} ngày
                                </div>
                                <span className="metric-note">trước</span>
                            </div>
                        </div>

                        {/* Additional Info */}
                        <div className="additional-info">
                            <h3>Thông tin bổ sung</h3>
                            <div className="info-grid">
                                <div className="info-item">
                                    <span className="info-label">🎬 Video hoàn thành</span>
                                    <span className="info-value">{student.video_completion_rate?.toFixed(1) || 'N/A'}%</span>
                                </div>
                                <div className="info-item">
                                    <span className="info-label">📝 Quiz TB</span>
                                    <span className="info-value">{student.quiz_avg_score?.toFixed(1) || 'N/A'}%</span>
                                </div>
                                <div className="info-item">
                                    <span className="info-label">💬 Tương tác Forum</span>
                                    <span className="info-value">{student.discussion_threads_count || 0} bài</span>
                                </div>
                                <div className="info-item">
                                    <span className="info-label">🆔 User ID</span>
                                    <span className="info-value">{student.user_id}</span>
                                </div>
                                {student.mssv && (
                                    <div className="info-item">
                                        <span className="info-label">🎓 MSSV</span>
                                        <span className="info-value">{student.mssv}</span>
                                    </div>
                                )}
                                {student.username && (
                                    <div className="info-item">
                                        <span className="info-label">👤 Username</span>
                                        <span className="info-value">@{student.username}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </section>

                    {/* SHAP Analysis Section - below overview */}
                    <section className="shap-analysis-section">
                        <div className="section-header">
                            <span className="section-icon">🧠</span>
                            <h2>Phân Tích AI</h2>
                        </div>
                        <ShapExplanationChart
                            userId={student.user_id}
                            courseId={selectedCourse.course_id}
                        />
                    </section>
                </div>

                {/* Right Column */}
                <aside className="right-column">
                    {/* Suggestions Section */}
                    <section className="suggestions-section">
                        <div className="section-header">
                            <span className="section-icon">💡</span>
                            <h2>Gợi Ý Can Thiệp</h2>
                            {student.suggestions && student.suggestions.length > 0 && (
                                <span className="count-badge">{student.suggestions.length}</span>
                            )}
                        </div>

                        <div className="suggestions-list">
                            {student.suggestions && student.suggestions.length > 0 ? (
                                student.suggestions.map((suggestion, index) => (
                                    <div
                                        key={index}
                                        className={`suggestion-card priority-${suggestion.priority}`}
                                    >
                                        <span className="suggestion-icon">{suggestion.icon}</span>
                                        <div className="suggestion-content">
                                            <h4>{suggestion.title}</h4>
                                            <p>{suggestion.description}</p>
                                        </div>
                                        <span className={`priority-tag priority-${suggestion.priority}`}>
                                            {suggestion.priority === 'high' && 'Quan trọng'}
                                            {suggestion.priority === 'medium' && 'Trung bình'}
                                            {suggestion.priority === 'low' && 'Thấp'}
                                        </span>
                                    </div>
                                ))
                            ) : (
                                <div className="no-suggestions">
                                    <span className="icon">✨</span>
                                    <p>Không có gợi ý đặc biệt</p>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Action Buttons Section */}
                    <section className="actions-section">
                        <div className="section-header">
                            <span className="section-icon">🎯</span>
                            <h2>Hành Động</h2>
                        </div>

                        <div className="action-buttons">
                            <button className="action-btn email-btn" onClick={handleEmail}>
                                <span className="btn-icon">📧</span>
                                <span className="btn-text">Gửi Email</span>
                            </button>
                            <button className="action-btn phone-btn" onClick={handlePhone}>
                                <span className="btn-icon">📞</span>
                                <span className="btn-text">Điện Thoại</span>
                            </button>
                            <button className="action-btn message-btn" onClick={handleMessage}>
                                <span className="btn-icon">💬</span>
                                <span className="btn-text">Nhắn Tin</span>
                            </button>
                        </div>
                    </section>
                </aside>
            </main>
        </div>
    );
}
