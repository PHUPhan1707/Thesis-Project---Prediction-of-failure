import { useState } from 'react';
import { useDashboard } from '../../context/DashboardContext';
import api from '../../services/api';
import { ShapExplanationChart } from './ShapExplanation';
import './StudentDetailModal.css';

export function StudentDetailModal() {
    const { selectedStudent, selectedCourse, closeStudentDetail, isLoadingStudentDetail } = useDashboard();
    const [activeTab, setActiveTab] = useState<'overview' | 'suggestions' | 'shap' | 'intervention'>('overview');
    const [interventionNote, setInterventionNote] = useState('');
    const [selectedAction, setSelectedAction] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitSuccess, setSubmitSuccess] = useState(false);

    if (!selectedStudent && !isLoadingStudentDetail) {
        return null;
    }

    const handleOverlayClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            closeStudentDetail();
        }
    };

    const handleSubmitIntervention = async () => {
        if (!selectedStudent || !selectedCourse || !selectedAction) return;

        try {
            setIsSubmitting(true);
            await api.recordIntervention(selectedStudent.user_id, selectedCourse.course_id, {
                action: selectedAction,
                notes: interventionNote,
            });
            setSubmitSuccess(true);
            setTimeout(() => {
                setSubmitSuccess(false);
                setSelectedAction('');
                setInterventionNote('');
            }, 3000);
        } catch (error) {
            console.error('Failed to record intervention:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const riskLevelConfig = {
        HIGH: { color: 'red', label: 'Nguy cơ cao', icon: '🚨', description: 'Cần can thiệp ngay lập tức' },
        MEDIUM: { color: 'yellow', label: 'Nguy cơ TB', icon: '⚠️', description: 'Cần theo dõi và hỗ trợ' },
        LOW: { color: 'green', label: 'Nguy cơ thấp', icon: '✅', description: 'Đang học tốt' },
    };

    const interventionActions = [
        { value: 'email_sent', label: '📧 Gửi email nhắc nhở', priority: 'high' },
        { value: 'phone_call', label: '📞 Gọi điện thoại', priority: 'high' },
        { value: 'meeting_scheduled', label: '📅 Hẹn gặp trực tiếp', priority: 'medium' },
        { value: 'extra_resources', label: '📚 Gửi tài liệu bổ trợ', priority: 'medium' },
        { value: 'peer_support', label: '👥 Kết nối với bạn học', priority: 'low' },
        { value: 'deadline_extension', label: '⏰ Gia hạn deadline', priority: 'medium' },
        { value: 'note_only', label: '📝 Ghi chú theo dõi', priority: 'low' },
    ];

    if (isLoadingStudentDetail) {
        return (
            <div className="modal-overlay" onClick={handleOverlayClick}>
                <div className="modal-content loading">
                    <div className="modal-loading">
                        <div className="loading-spinner"></div>
                        <span>Đang tải thông tin...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (!selectedStudent) return null;

    const config = riskLevelConfig[selectedStudent.risk_level] || riskLevelConfig.LOW;

    return (
        <div className="modal-overlay" onClick={handleOverlayClick}>
            <div className="modal-content">
                {/* Modal Header */}
                <div className={`modal-header header-${config.color}`}>
                    <button className="close-btn" onClick={closeStudentDetail}>✕</button>

                    <div className="student-profile">
                        <div className={`profile-avatar avatar-${config.color}`}>
                            {selectedStudent.full_name
                                ?.split(' ')
                                .slice(-2)
                                .map(n => n[0])
                                .join('')
                                .toUpperCase() || 'SV'}
                        </div>
                        <div className="profile-info">
                            <h2 className="profile-name">{selectedStudent.full_name || 'Chưa có tên'}</h2>
                            <span className="profile-email">{selectedStudent.email}</span>
                            <div className="profile-details">
                                <span className="detail-item">ID: {selectedStudent.user_id}</span>
                                {selectedStudent.mssv && <span className="detail-item">MSSV: {selectedStudent.mssv}</span>}
                                {selectedStudent.username && <span className="detail-item">@{selectedStudent.username}</span>}
                            </div>
                        </div>
                    </div>

                    <div className={`risk-status status-${config.color}`}>
                        <span className="status-icon">{config.icon}</span>
                        <div className="status-info">
                            <span className="status-label">{config.label}</span>
                            <span className="status-score">{selectedStudent.fail_risk_score?.toFixed(1)}%</span>
                        </div>
                    </div>
                </div>

                {/* Modal Tabs */}
                <div className="modal-tabs">
                    <button
                        className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
                        onClick={() => setActiveTab('overview')}
                    >
                        <span className="tab-icon">📊</span>
                        Tổng quan
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'suggestions' ? 'active' : ''}`}
                        onClick={() => setActiveTab('suggestions')}
                    >
                        <span className="tab-icon">💡</span>
                        Gợi ý can thiệp
                        {selectedStudent.suggestions?.length > 0 && (
                            <span className="tab-badge">{selectedStudent.suggestions.length}</span>
                        )}
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'shap' ? 'active' : ''}`}
                        onClick={() => setActiveTab('shap')}
                    >
                        <span className="tab-icon">🧠</span>
                        Phan tich AI
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'intervention' ? 'active' : ''}`}
                        onClick={() => setActiveTab('intervention')}
                    >
                        <span className="tab-icon">✍️</span>
                        Ghi nhận
                    </button>
                </div>

                {/* Modal Body */}
                <div className="modal-body">
                    {/* Overview Tab */}
                    {activeTab === 'overview' && (
                        <div className="tab-content overview-tab">
                            <div className="metrics-grid">
                                <div className="metric-card">
                                    <div className="metric-header">
                                        <span className="metric-icon">📈</span>
                                        <span className="metric-title">Điểm Rủi Ro</span>
                                    </div>
                                    <div className={`metric-value-large value-${config.color}`}>
                                        {selectedStudent.fail_risk_score?.toFixed(1) || 'N/A'}%
                                    </div>
                                    <div className="metric-bar">
                                        <div
                                            className={`bar-fill fill-${config.color}`}
                                            style={{ width: `${selectedStudent.fail_risk_score || 0}%` }}
                                        ></div>
                                    </div>
                                </div>

                                <div className="metric-card">
                                    <div className="metric-header">
                                        <span className="metric-icon">📝</span>
                                        <span className="metric-title">Điểm Quiz</span>
                                    </div>
                                    <div className="metric-value-large">
                                        {selectedStudent.h5p_avg_score?.toFixed(1) || 'N/A'}%
                                    </div>
                                    <div className="metric-bar">
                                        <div
                                            className="bar-fill fill-blue"
                                            style={{ width: `${selectedStudent.h5p_avg_score || 0}%` }}
                                        ></div>
                                    </div>
                                </div>

                                <div className="metric-card">
                                    <div className="metric-header">
                                        <span className="metric-icon">📚</span>
                                        <span className="metric-title">Tiến Độ Học</span>
                                    </div>
                                    <div className="metric-value-large">
                                        {selectedStudent.mooc_completion_rate?.toFixed(1) || 'N/A'}%
                                    </div>
                                    <div className="metric-bar">
                                        <div
                                            className="bar-fill fill-purple"
                                            style={{ width: `${selectedStudent.mooc_completion_rate || 0}%` }}
                                        ></div>
                                    </div>
                                </div>

                                <div className="metric-card">
                                    <div className="metric-header">
                                        <span className="metric-icon">📅</span>
                                        <span className="metric-title">Hoạt Động Cuối</span>
                                    </div>
                                    <div className="metric-value-large">
                                        {selectedStudent.days_since_last_activity || 0} ngày
                                    </div>
                                    <span className="metric-note">trước</span>
                                </div>
                            </div>

                            {/* Additional Metrics */}
                            <div className="additional-metrics">
                                <h4>Thông tin bổ sung</h4>
                                <div className="additional-grid">
                                    <div className="additional-item">
                                        <span className="additional-label">🏆 Điểm thi MOOC</span>
                                        <span className={`additional-value ${(selectedStudent.mooc_grade_percentage || 0) < 50 ? 'value-warning' : ''}`}>
                                            {selectedStudent.mooc_grade_percentage?.toFixed(1) || 'N/A'}%
                                        </span>
                                    </div>
                                    <div className="additional-item">
                                        <span className="additional-label">🎬 Video hoàn thành</span>
                                        <span className="additional-value">
                                            {selectedStudent.video_completion_rate?.toFixed(1) || 'N/A'}%
                                        </span>
                                    </div>
                                    <div className="additional-item">
                                        <span className="additional-label">💬 Tương tác Forum</span>
                                        <span className="additional-value">
                                            {selectedStudent.discussion_threads_count || 0} bài
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Suggestions Tab */}
                    {activeTab === 'suggestions' && (
                        <div className="tab-content suggestions-tab">
                            {selectedStudent.suggestions && selectedStudent.suggestions.length > 0 ? (
                                <div className="suggestions-list">
                                    {selectedStudent.suggestions.map((suggestion, index) => (
                                        <div
                                            key={index}
                                            className={`suggestion-card priority-${suggestion.priority}`}
                                            style={{ animationDelay: `${index * 0.1}s` }}
                                        >
                                            <div className="suggestion-icon">{suggestion.icon}</div>
                                            <div className="suggestion-content">
                                                <h4 className="suggestion-title">{suggestion.title}</h4>
                                                <p className="suggestion-description">{suggestion.description}</p>
                                            </div>
                                            <div className={`priority-badge priority-${suggestion.priority}`}>
                                                {suggestion.priority === 'high' && 'Quan trọng'}
                                                {suggestion.priority === 'medium' && 'Trung bình'}
                                                {suggestion.priority === 'low' && 'Thấp'}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="no-suggestions">
                                    <span className="no-suggestions-icon">💡</span>
                                    <h4>Không có gợi ý đặc biệt</h4>
                                    <p>Sinh viên này không có vấn đề cần can thiệp ngay lập tức</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* SHAP Analysis Tab */}
                    {activeTab === 'shap' && selectedStudent && selectedCourse && (
                        <div className="tab-content shap-tab">
                            <ShapExplanationChart
                                userId={selectedStudent.user_id}
                                courseId={selectedCourse.course_id}
                            />
                        </div>
                    )}

                    {/* Intervention Tab */}
                    {activeTab === 'intervention' && (
                        <div className="tab-content intervention-tab">
                            {submitSuccess ? (
                                <div className="success-message">
                                    <span className="success-icon">✅</span>
                                    <h4>Đã ghi nhận hành động can thiệp!</h4>
                                    <p>Thông tin đã được lưu vào hệ thống</p>
                                </div>
                            ) : (
                                <>
                                    <div className="intervention-form">
                                        <div className="form-group">
                                            <label className="form-label">Chọn hành động can thiệp</label>
                                            <div className="action-buttons">
                                                {interventionActions.map((action) => (
                                                    <button
                                                        key={action.value}
                                                        className={`action-btn priority-${action.priority} ${selectedAction === action.value ? 'selected' : ''
                                                            }`}
                                                        onClick={() => setSelectedAction(action.value)}
                                                    >
                                                        {action.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="form-group">
                                            <label className="form-label">Ghi chú (tùy chọn)</label>
                                            <textarea
                                                className="form-textarea"
                                                placeholder="Nhập ghi chú về hành động can thiệp..."
                                                value={interventionNote}
                                                onChange={(e) => setInterventionNote(e.target.value)}
                                                rows={4}
                                            />
                                        </div>

                                        <button
                                            className="submit-btn"
                                            onClick={handleSubmitIntervention}
                                            disabled={!selectedAction || isSubmitting}
                                        >
                                            {isSubmitting ? (
                                                <>
                                                    <span className="btn-spinner"></span>
                                                    Đang lưu...
                                                </>
                                            ) : (
                                                <>
                                                    <span className="btn-icon">💾</span>
                                                    Lưu hành động can thiệp
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default StudentDetailModal;
