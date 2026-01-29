import { useDashboard } from '../../context/DashboardContext';
import './RiskChart.css';

export function RiskDistributionChart() {
    const { statistics, isLoadingStatistics } = useDashboard();

    if (isLoadingStatistics || !statistics) {
        return (
            <div className="risk-chart-container loading">
                <div className="skeleton-chart"></div>
            </div>
        );
    }

    const total = statistics.total_students;
    const highPercent = (statistics.high_risk_count / total) * 100;
    const mediumPercent = (statistics.medium_risk_count / total) * 100;
    const lowPercent = (statistics.low_risk_count / total) * 100;

    // Donut chart segments
    const segments = [
        { label: 'Cao', value: statistics.high_risk_count, percent: highPercent, color: '#ef4444', offset: 0 },
        { label: 'Trung bình', value: statistics.medium_risk_count, percent: mediumPercent, color: '#f59e0b', offset: highPercent },
        { label: 'Thấp', value: statistics.low_risk_count, percent: lowPercent, color: '#10b981', offset: highPercent + mediumPercent },
    ];

    return (
        <div className="risk-chart-container">
            <div className="chart-header">
                <h3 className="chart-title">
                    <span className="title-icon">📊</span>
                    Phân Bố Nguy Cơ
                </h3>
                <span className="chart-subtitle">Tổng quan tình trạng học viên</span>
            </div>

            <div className="chart-content">
                {/* Donut Chart */}
                <div className="donut-chart-wrapper">
                    <svg className="donut-chart" viewBox="0 0 100 100">
                        {segments.map((seg, index) => {
                            const circumference = 2 * Math.PI * 35;
                            const strokeDasharray = `${(seg.percent / 100) * circumference} ${circumference}`;
                            const strokeDashoffset = -((seg.offset / 100) * circumference);

                            return (
                                <circle
                                    key={seg.label}
                                    className={`donut-segment segment-${index}`}
                                    cx="50"
                                    cy="50"
                                    r="35"
                                    fill="none"
                                    stroke={seg.color}
                                    strokeWidth="15"
                                    strokeDasharray={strokeDasharray}
                                    strokeDashoffset={strokeDashoffset}
                                    transform="rotate(-90 50 50)"
                                    style={{ animationDelay: `${index * 0.2}s` }}
                                />
                            );
                        })}
                        {/* Center circle for donut effect */}
                        <circle cx="50" cy="50" r="25" fill="white" />
                    </svg>
                    <div className="donut-center">
                        <span className="center-value">{total}</span>
                        <span className="center-label">Tổng SV</span>
                    </div>
                </div>

                {/* Legend */}
                <div className="chart-legend">
                    {segments.map((seg) => (
                        <div key={seg.label} className="legend-item">
                            <div className="legend-color" style={{ backgroundColor: seg.color }}></div>
                            <div className="legend-info">
                                <span className="legend-label">{seg.label}</span>
                                <span className="legend-value">{seg.value}</span>
                            </div>
                            <span className="legend-percent">{seg.percent.toFixed(1)}%</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Progress Bars */}
            <div className="risk-bars">
                <div className="bar-group bar-high">
                    <div className="bar-header">
                        <span className="bar-label">🚨 Nguy cơ cao (≥70%)</span>
                        <span className="bar-value">{statistics.high_risk_count} SV</span>
                    </div>
                    <div className="bar-track">
                        <div
                            className="bar-fill"
                            style={{
                                width: `${highPercent}%`,
                                background: 'linear-gradient(90deg, #ef4444, #f87171)'
                            }}
                        ></div>
                    </div>
                </div>

                <div className="bar-group bar-medium">
                    <div className="bar-header">
                        <span className="bar-label">⚠️ Nguy cơ TB (40-70%)</span>
                        <span className="bar-value">{statistics.medium_risk_count} SV</span>
                    </div>
                    <div className="bar-track">
                        <div
                            className="bar-fill"
                            style={{
                                width: `${mediumPercent}%`,
                                background: 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                            }}
                        ></div>
                    </div>
                </div>

                <div className="bar-group bar-low">
                    <div className="bar-header">
                        <span className="bar-label">✅ Nguy cơ thấp (&lt;40%)</span>
                        <span className="bar-value">{statistics.low_risk_count} SV</span>
                    </div>
                    <div className="bar-track">
                        <div
                            className="bar-fill"
                            style={{
                                width: `${lowPercent}%`,
                                background: 'linear-gradient(90deg, #10b981, #34d399)'
                            }}
                        ></div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default RiskDistributionChart;
