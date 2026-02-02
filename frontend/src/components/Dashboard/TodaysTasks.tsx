import { useNavigate } from 'react-router-dom';
import type { TodayTask } from '../../types';
import './TodaysTasks.css';

interface TodaysTasksProps {
    tasks: TodayTask[];
    isLoading?: boolean;
}

export function TodaysTasks({ tasks, isLoading }: TodaysTasksProps) {
    const navigate = useNavigate();

    if (isLoading) {
        return (
            <div className="todays-tasks loading">
                <div className="tasks-header">
                    <span className="header-icon">📋</span>
                    <h3>Việc Cần Làm Hôm Nay</h3>
                </div>
                <div className="tasks-skeleton">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="task-skeleton-item">
                            <div className="skeleton-avatar"></div>
                            <div className="skeleton-content">
                                <div className="skeleton-name"></div>
                                <div className="skeleton-reason"></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    const handleViewStudent = (userId: number) => {
        navigate(`/student/${userId}`);
    };

    const handleEmailStudent = (email: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (email) {
            window.location.href = `mailto:${email}?subject=Hỗ trợ học tập`;
        }
    };

    const urgencyConfig = {
        critical: { color: 'red', label: 'Khẩn cấp', icon: '🚨' },
        high: { color: 'orange', label: 'Cao', icon: '⚠️' },
        medium: { color: 'yellow', label: 'Trung bình', icon: '📌' },
    };

    return (
        <div className="todays-tasks">
            <div className="tasks-header">
                <div className="header-left">
                    <span className="header-icon">📋</span>
                    <h3>Việc Cần Làm Hôm Nay</h3>
                </div>
                {tasks.length > 0 && (
                    <span className="task-count">{tasks.length}</span>
                )}
            </div>

            <div className="tasks-list">
                {tasks.length === 0 ? (
                    <div className="no-tasks">
                        <span className="no-tasks-icon">🎉</span>
                        <p>Không có việc cần làm hôm nay!</p>
                        <span className="no-tasks-hint">Tất cả sinh viên đang ổn định</span>
                    </div>
                ) : (
                    tasks.slice(0, 5).map((task) => {
                        const config = urgencyConfig[task.urgency];
                        return (
                            <div
                                key={task.user_id}
                                className={`task-item task-${config.color}`}
                                onClick={() => handleViewStudent(task.user_id)}
                            >
                                <div className={`task-avatar avatar-${config.color}`}>
                                    {task.full_name?.split(' ').slice(-1)[0]?.[0] || 'S'}
                                </div>
                                <div className="task-content">
                                    <div className="task-name">{task.full_name}</div>
                                    <div className="task-reason">
                                        <span className="urgency-icon">{config.icon}</span>
                                        {task.reason}
                                    </div>
                                </div>
                                <div className="task-actions">
                                    <span className={`risk-badge badge-${config.color}`}>
                                        {task.fail_risk_score.toFixed(0)}%
                                    </span>
                                    <button
                                        className="action-btn email-btn"
                                        onClick={(e) => handleEmailStudent(task.email, e)}
                                        title="Gửi email"
                                    >
                                        📧
                                    </button>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {tasks.length > 5 && (
                <button
                    className="view-all-btn"
                    onClick={() => navigate('/details')}
                >
                    Xem tất cả ({tasks.length}) →
                </button>
            )}
        </div>
    );
}

export default TodaysTasks;
