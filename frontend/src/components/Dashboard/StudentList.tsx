import { useNavigate } from 'react-router-dom';
import { useDashboard } from '../../context/DashboardContext';
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
        return (
            <div className="student-list loading">
                {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="student-card skeleton">
                        <div className="skeleton-avatar"></div>
                        <div className="skeleton-content">
                            <div className="skeleton-line wide"></div>
                            <div className="skeleton-line medium"></div>
                            <div className="skeleton-line short"></div>
                        </div>
                    </div>
                ))}
            </div>
        );
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

    const config = riskLevelConfig[student.risk_level] || riskLevelConfig.LOW;

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
            className={`student-card risk-${config.color}`}
            style={{ animationDelay: `${index * 0.05}s` }}
            onClick={onClick}
        >
            <div className="card-left">
                <div className={`student-avatar avatar-${config.color}`}>
                    {getInitials(student.full_name)}
                </div>
                <div className="student-info">
                    <h4 className="student-name">{student.full_name || 'Chưa có tên'}</h4>
                    <span className="student-email">{student.email || 'N/A'}</span>
                    <span className="student-id">ID: {student.user_id}</span>
                </div>
            </div>

            <div className="card-center">
                <div className="metric-group">
                    <div className="metric">
                        <span className="metric-label">Điểm rủi ro</span>
                        <span className={`metric-value risk-value-${config.color}`}>
                            {formatPercent(student.fail_risk_score)}
                        </span>
                    </div>
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
                <div className={`risk-badge badge-${config.color}`}>
                    <span className="badge-icon">{config.icon}</span>
                    <span className="badge-text">{config.label}</span>
                </div>
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
