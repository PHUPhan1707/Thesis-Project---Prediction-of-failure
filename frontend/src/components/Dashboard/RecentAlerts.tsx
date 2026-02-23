import { useNavigate } from 'react-router-dom';
import { CardSkeleton } from '../LoadingSkeleton';
import type { RecentAlert } from '../../types';
import './RecentAlerts.css';

interface RecentAlertsProps {
    alerts: RecentAlert[];
    isLoading?: boolean;
}

export function RecentAlerts({ alerts, isLoading }: RecentAlertsProps) {
    const navigate = useNavigate();

    if (isLoading) {
        return (
            <div className="recent-alerts loading">
                <div className="alerts-header">
                    <span className="header-icon">🔔</span>
                    <h3>Cảnh Báo Gần Đây</h3>
                </div>
                <CardSkeleton />
                <CardSkeleton />
            </div>
        );
    }

    const handleViewStudent = (userId: number) => {
        navigate(`/student/${userId}`);
    };

    const getRelativeTime = (dateString: string): string => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffHours / 24);

        if (diffDays > 0) {
            return `${diffDays} ngày trước`;
        } else if (diffHours > 0) {
            return `${diffHours} giờ trước`;
        } else {
            return 'Vừa xong';
        }
    };

    const alertConfig = {
        risk_increase: { icon: '📈', color: 'red', label: 'Rủi ro tăng' },
        inactive: { icon: '😴', color: 'orange', label: 'Không hoạt động' },
        low_progress: { icon: '📉', color: 'yellow', label: 'Tiến độ thấp' },
    };

    return (
        <div className="recent-alerts">
            <div className="alerts-header">
                <div className="header-left">
                    <span className="header-icon">🔔</span>
                    <h3>Cảnh Báo Gần Đây</h3>
                </div>
                {alerts.length > 0 && (
                    <span className="alert-count">{alerts.length}</span>
                )}
            </div>

            <div className="alerts-timeline">
                {alerts.length === 0 ? (
                    <div className="no-alerts">
                        <span className="no-alerts-icon">✨</span>
                        <p>Không có cảnh báo mới</p>
                    </div>
                ) : (
                    alerts.slice(0, 6).map((alert) => {
                        const config = alertConfig[alert.alert_type];
                        return (
                            <div
                                key={alert.id}
                                className={`alert-item alert-${config.color}`}
                                onClick={() => handleViewStudent(alert.user_id)}
                            >
                                <div className="alert-timeline-dot">
                                    <span className={`dot dot-${config.color}`}></span>
                                </div>
                                <div className="alert-content">
                                    <div className="alert-icon">{config.icon}</div>
                                    <div className="alert-details">
                                        <div className="alert-name">{alert.full_name}</div>
                                        <div className="alert-message">{alert.message}</div>
                                    </div>
                                    <div className="alert-time">
                                        {getRelativeTime(alert.created_at)}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default RecentAlerts;
