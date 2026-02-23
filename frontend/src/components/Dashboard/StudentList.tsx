import { useNavigate } from 'react-router-dom';
import { useDashboard } from '../../context/DashboardContext';
import { StudentListSkeleton } from '../LoadingSkeleton';
import type { Student } from '../../types';
import './StudentList.css';

export function StudentList() {
    const { students, isLoadingStudents, error } = useDashboard();
    const navigate = useNavigate();

    if (error) {
        return (
            <div className="student-list-error">
                <span className="error-icon">⚠️</span>
                <span className="error-text">{error}</span>
            </div>
        );
    }

    if (isLoadingStudents) {
        return <StudentListSkeleton count={8} />;
    }

    if (students.length === 0) {
        return (
            <div className="student-list-empty">
                <span className="empty-icon">📭</span>
                <h4>Không tìm thấy sinh viên</h4>
                <p>Thử thay đổi bộ lọc hoặc tìm kiếm khác</p>
            </div>
        );
    }

    return (
        <div className="student-list">
            {students.map((student, index) => (
                <StudentCard
                    key={student.user_id}
                    student={student}
                    index={index}
                    onClick={() => navigate(`/student/${student.user_id}`)}
                />
            ))}
        </div>
    );
}

interface StudentCardProps {
    student: Student;
    index: number;
    onClick: () => void;
}

function StudentCard({ student, index, onClick }: StudentCardProps) {
    const riskLevelConfig = {
        HIGH: { color: 'red', label: 'Cao', icon: '🚨' },
        MEDIUM: { color: 'yellow', label: 'Trung bình', icon: '⚠️' },
        LOW: { color: 'green', label: 'Thấp', icon: '✅' },
    };

    const completionConfig = {
        completed: { color: 'completed', label: 'Đã hoàn thành', icon: '🎓' },
        not_passed: { color: 'not-passed', label: 'Chưa đạt', icon: '📝' },
        in_progress: { color: 'in-progress', label: 'Đang học', icon: '📚' },
    };

    const config = riskLevelConfig[student.risk_level] || riskLevelConfig.LOW;

    // Check completion status with fallback to mooc_is_passed
    // Handle both boolean (true/false) and int (1/0) from backend
    const isCompleted = student.completion_status === 'completed' ||
        student.mooc_is_passed === true ||
        student.mooc_is_passed === 1;

    const completionStatus = student.completion_status ||
        (student.mooc_is_passed === true || student.mooc_is_passed === 1 ? 'completed' :
            student.mooc_is_passed === false || student.mooc_is_passed === 0 ? 'not_passed' : 'in_progress');
    const completionCfg = completionConfig[completionStatus] || completionConfig.in_progress;

    // Generate avatar initials
    const getInitials = (name: string | null | undefined) => {
        if (!name) return 'SV';
        return name
            .split(' ')
            .map((n) => n[0])
            .slice(-2)
            .join('')
            .toUpperCase();
    };

    // Format days since last activity
    const formatLastActivity = (days: number | null | undefined) => {
        if (days === null || days === undefined) return 'N/A';
        if (days === 0) return 'Hôm nay';
        if (days === 1) return 'Hôm qua';
        if (days < 7) return `${days} ngày trước`;
        if (days < 30) return `${Math.floor(days / 7)} tuần trước`;
        return `${Math.floor(days / 30)} tháng trước`;
    };

    const formatPercent = (value: unknown) => {
        const n = Number(value);
        if (!Number.isFinite(n)) return 'N/A';
        return `${n.toFixed(1)}%`;
    };

    return (
        <div
            className={`student-card ${isCompleted ? 'completed' : `risk-${config.color}`}`}
            style={{ animationDelay: `${index * 0.05}s` }}
            onClick={onClick}
        >
            <div className="card-left">
                <div className={`student-avatar ${isCompleted ? 'avatar-completed' : `avatar-${config.color}`}`}>
                    {getInitials(student.full_name)}
                </div>
                <div className="student-info">
                    <h4 className="student-name">
                        {student.full_name || 'Chưa có tên'}
                        {isCompleted && <span className="completed-badge-inline">🎓</span>}
                    </h4>
                    <span className="student-email">{student.email || 'N/A'}</span>
                    <span className="student-id">ID: {student.user_id}</span>
                </div>
            </div>

            <div className="card-center">
                <div className="metric-group">
                    {!isCompleted && (
                        <div className="metric">
                            <span className="metric-label">Điểm rủi ro</span>
                            <span className={`metric-value risk-value-${config.color}`}>
                                {formatPercent(student.fail_risk_score)}
                            </span>
                        </div>
                    )}
                    <div className="metric">
                        <span className="metric-label">Điểm TB</span>
                        <span className="metric-value">
                            {formatPercent(student.mooc_grade_percentage)}
                        </span>
                    </div>
                    <div className="metric">
                        <span className="metric-label">Tiến độ</span>
                        <span className="metric-value">
                            {formatPercent(student.mooc_completion_rate)}
                        </span>
                    </div>
                </div>
            </div>

            <div className="card-right">
                {isCompleted ? (
                    <div className="completion-badge badge-completed">
                        <span className="badge-icon">{completionCfg.icon}</span>
                        <span className="badge-text">{completionCfg.label}</span>
                    </div>
                ) : (
                    <div className={`risk-badge badge-${config.color}`}>
                        <span className="badge-icon">{config.icon}</span>
                        <span className="badge-text">{config.label}</span>
                    </div>
                )}
                <span className="last-activity">
                    {formatLastActivity(student.days_since_last_activity)}
                </span>
                <button className="view-detail-btn">
                    Xem chi tiết →
                </button>
            </div>
        </div>
    );
}

export default StudentList;
