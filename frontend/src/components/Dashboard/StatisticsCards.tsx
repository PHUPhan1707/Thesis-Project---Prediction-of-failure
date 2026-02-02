import { useDashboard } from '../../context/DashboardContext';
import './StatisticsCards.css';

export function StatisticsCards() {
    const { statistics, isLoadingStatistics } = useDashboard();

    if (isLoadingStatistics) {
        return (
            <div className="statistics-cards loading">
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="stat-card skeleton">
                        <div className="skeleton-icon"></div>
                        <div className="skeleton-text"></div>
                        <div className="skeleton-value"></div>
                    </div>
                ))}
            </div>
        );
    }

    if (!statistics) {
        return null;
    }

    const cards = [
        {
            id: 'total',
            icon: '👥',
            label: 'Tổng sinh viên',
            value: statistics.total_students,
            color: 'blue',
            trend: null,
        },
        {
            id: 'completed',
            icon: '🎓',
            label: 'Đã hoàn thành',
            value: statistics.completed_count || 0,
            percentage: statistics.total_students > 0
                ? (((statistics.completed_count || 0) / statistics.total_students) * 100).toFixed(1)
                : '0',
            color: 'purple',
            trend: 'success',
        },
        {
            id: 'high-risk',
            icon: '🚨',
            label: 'Nguy cơ cao',
            value: statistics.high_risk_count,
            percentage: ((statistics.high_risk_count / statistics.total_students) * 100).toFixed(1),
            color: 'red',
            trend: 'warning',
        },
        {
            id: 'medium-risk',
            icon: '⚠️',
            label: 'Nguy cơ TB',
            value: statistics.medium_risk_count,
            percentage: ((statistics.medium_risk_count / statistics.total_students) * 100).toFixed(1),
            color: 'yellow',
            trend: 'caution',
        },
        {
            id: 'low-risk',
            icon: '✅',
            label: 'Nguy cơ thấp',
            value: statistics.low_risk_count,
            percentage: ((statistics.low_risk_count / statistics.total_students) * 100).toFixed(1),
            color: 'green',
            trend: 'good',
        },
    ];

    return (
        <div className="statistics-cards">
            {cards.map((card, index) => (
                <div
                    key={card.id}
                    className={`stat-card stat-card-${card.color}`}
                    style={{ animationDelay: `${index * 0.1}s` }}
                >
                    <div className="stat-card-header">
                        <span className="stat-icon">{card.icon}</span>
                        {card.trend && (
                            <span className={`stat-trend trend-${card.trend}`}>
                                {card.trend === 'warning' && '↑'}
                                {card.trend === 'caution' && '→'}
                                {card.trend === 'good' && '↓'}
                            </span>
                        )}
                    </div>
                    <div className="stat-value">{card.value}</div>
                    <div className="stat-label">{card.label}</div>
                    {card.percentage && (
                        <div className="stat-percentage">{card.percentage}% của lớp</div>
                    )}
                    <div className="stat-card-glow"></div>
                </div>
            ))}
        </div>
    );
}

export function AverageMetrics() {
    const { statistics, isLoadingStatistics } = useDashboard();

    if (isLoadingStatistics || !statistics) {
        return null;
    }

    const avgRiskScore = Number(statistics.avg_risk_score) || 0;
    const avgGrade = Number(statistics.avg_grade) || 0;
    const avgCompletionRate = Number(statistics.avg_completion_rate) || 0;

    const metrics = [
        {
            id: 'avg-risk',
            icon: '📊',
            label: 'Điểm rủi ro TB',
            value: avgRiskScore.toFixed(1),
            unit: '%',
            status: avgRiskScore > 50 ? 'warning' : 'good',
        },
        {
            id: 'avg-grade',
            icon: '📝',
            label: 'Điểm TB',
            value: avgGrade.toFixed(1),
            unit: '%',
            status: avgGrade < 50 ? 'warning' : 'good',
        },
        {
            id: 'avg-completion',
            icon: '📈',
            label: 'Tiến độ TB',
            value: avgCompletionRate.toFixed(1),
            unit: '%',
            status: avgCompletionRate < 50 ? 'warning' : 'good',
        },
    ];

    return (
        <div className="average-metrics">
            {metrics.map((metric) => (
                <div key={metric.id} className={`metric-card metric-${metric.status}`}>
                    <span className="metric-icon">{metric.icon}</span>
                    <div className="metric-content">
                        <span className="metric-label">{metric.label}</span>
                        <span className="metric-value">
                            {metric.value}{metric.unit}
                        </span>
                    </div>
                    <div className={`metric-indicator indicator-${metric.status}`}></div>
                </div>
            ))}
        </div>
    );
}

export default StatisticsCards;
