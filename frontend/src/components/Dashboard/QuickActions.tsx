import type { QuickStats } from '../../types';
import './QuickActions.css';

interface QuickActionsProps {
    stats: QuickStats | null;
    onRefresh?: () => void;
    isLoading?: boolean;
}

export function QuickActions({ stats, onRefresh, isLoading }: QuickActionsProps) {
    const handleEmailAll = () => {
        alert('Tính năng gửi email hàng loạt sẽ được triển khai sau');
    };

    const handleExport = () => {
        alert('Tính năng export CSV sẽ được triển khai sau');
    };

    const handleViewReport = () => {
        alert('Tính năng xem báo cáo sẽ được triển khai sau');
    };

    return (
        <div className="quick-actions">
            <div className="actions-header">
                <span className="header-icon">⚡</span>
                <h3>Hành Động Nhanh</h3>
            </div>

            {/* Quick Stats */}
            {stats && (
                <div className="quick-stats-grid">
                    <div className="quick-stat stat-red">
                        <span className="stat-icon">🚨</span>
                        <div className="stat-info">
                            <span className="stat-value">{stats.new_high_risk_count}</span>
                            <span className="stat-label">Nguy cơ cao</span>
                        </div>
                    </div>
                    <div className="quick-stat stat-orange">
                        <span className="stat-icon">😴</span>
                        <div className="stat-info">
                            <span className="stat-value">{stats.inactive_students_count}</span>
                            <span className="stat-label">Không hoạt động</span>
                        </div>
                    </div>
                    <div className="quick-stat stat-blue">
                        <span className="stat-icon">📋</span>
                        <div className="stat-info">
                            <span className="stat-value">{stats.intervention_pending}</span>
                            <span className="stat-label">Cần can thiệp</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            <div className="action-buttons">
                <button
                    className="action-btn btn-primary"
                    onClick={handleEmailAll}
                    disabled={isLoading}
                >
                    <span className="btn-icon">📧</span>
                    <span className="btn-text">Gửi Email Nhắc Nhở</span>
                </button>

                <button
                    className="action-btn btn-secondary"
                    onClick={onRefresh}
                    disabled={isLoading}
                >
                    <span className="btn-icon">{isLoading ? '⏳' : '🔄'}</span>
                    <span className="btn-text">{isLoading ? 'Đang tải...' : 'Làm Mới Dữ Liệu'}</span>
                </button>

                <button
                    className="action-btn btn-outline"
                    onClick={handleViewReport}
                    disabled={isLoading}
                >
                    <span className="btn-icon">📊</span>
                    <span className="btn-text">Xem Báo Cáo</span>
                </button>

                <button
                    className="action-btn btn-outline"
                    onClick={handleExport}
                    disabled={isLoading}
                >
                    <span className="btn-icon">📥</span>
                    <span className="btn-text">Export CSV</span>
                </button>
            </div>
        </div>
    );
}

export default QuickActions;
