/**
 * Dashboard Overview Page
 * Displays statistics and risk distribution
 */
import React, { useEffect, useState } from 'react';
import { Users, AlertCircle, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { useDashboard } from '../context/DashboardContext';
import { getCourseStatistics, getStudents } from '../services/api';
import type { CourseStatistics, Student } from '../types';
import StatsCard from '../components/StatsCard';
import RiskBadge from '../components/RiskBadge';
import './Dashboard.css';

const Dashboard: React.FC = () => {
    const { selectedCourse } = useDashboard();
    const [statistics, setStatistics] = useState<CourseStatistics | null>(null);
    const [topRiskStudents, setTopRiskStudents] = useState<Student[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!selectedCourse) return;

        const fetchData = async () => {
            try {
                setLoading(true);

                // Fetch statistics
                const stats = await getCourseStatistics(selectedCourse);
                setStatistics(stats);

                // Fetch top 5 high-risk students
                const students = await getStudents(selectedCourse, {
                    risk_level: 'HIGH',
                    sort_by: 'risk_score',
                    order: 'desc'
                });
                setTopRiskStudents(students.slice(0, 5));

            } catch (error) {
                console.error('Failed to fetch dashboard data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [selectedCourse]);

    if (loading || !statistics) {
        return (
            <div className="dashboard-loading">
                <div className="loading-spinner"></div>
                <p>Đang tải dữ liệu...</p>
            </div>
        );
    }

    // Prepare data for pie chart
    const chartData = [
        { name: 'Nguy cơ cao', value: statistics.high_risk_count, color: '#ef4444' },
        { name: 'Nguy cơ trung bình', value: statistics.medium_risk_count, color: '#f59e0b' },
        { name: 'Nguy cơ thấp', value: statistics.low_risk_count, color: '#10b981' },
    ];

    return (
        <div className="dashboard-page">
            <div className="dashboard-header">
                <h1 className="page-title">Tổng Quan</h1>
                <p className="page-subtitle">
                    Theo dõi tiến độ và cảnh báo sớm học viên có nguy cơ học yếu/bỏ học
                </p>
            </div>

            {/* Statistics Grid */}
            <div className="stats-grid">
                <StatsCard
                    icon={Users}
                    title="Tổng số học viên"
                    value={statistics.total_students}
                    description={`Điểm trung bình: ${statistics.avg_grade.toFixed(1)}%`}
                    color="primary"
                />

                <StatsCard
                    icon={AlertCircle}
                    title="Nguy cơ cao"
                    value={statistics.high_risk_count}
                    description={`${statistics.high_risk_percentage.toFixed(1)}% tổng số học viên`}
                    color="danger"
                />

                <StatsCard
                    icon={AlertTriangle}
                    title="Nguy cơ trung bình"
                    value={statistics.medium_risk_count}
                    description={`${statistics.medium_risk_percentage.toFixed(1)}% tổng số học viên`}
                    color="warning"
                />

                <StatsCard
                    icon={CheckCircle}
                    title="Nguy cơ thấp"
                    value={statistics.low_risk_count}
                    description={`${statistics.low_risk_percentage.toFixed(1)}% tổng số học viên`}
                    color="success"
                />
            </div>

            {/* Charts and Alerts Section */}
            <div className="dashboard-content-grid">
                {/* Risk Distribution Chart */}
                <div className="dashboard-card">
                    <h2 className="card-title">Phân Bố Nguy Cơ</h2>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={chartData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Recent High-Risk Alerts */}
                <div className="dashboard-card">
                    <h2 className="card-title">Cảnh Báo Ưu Tiên</h2>
                    <p className="card-subtitle">5 học viên có nguy cơ cao nhất</p>

                    {topRiskStudents.length === 0 ? (
                        <div className="empty-state">
                            <CheckCircle className="empty-icon" />
                            <p>Không có học viên nguy cơ cao</p>
                        </div>
                    ) : (
                        <div className="alert-list">
                            {topRiskStudents.map((student) => (
                                <div key={student.user_id} className="alert-item">
                                    <div className="alert-info">
                                        <p className="alert-name">{student.full_name || student.email}</p>
                                        <p className="alert-details">
                                            Điểm: {student.mooc_grade_percentage?.toFixed(1)}% |
                                            Hoàn thành: {student.mooc_completion_rate?.toFixed(1)}%
                                        </p>
                                    </div>
                                    <RiskBadge
                                        level={student.risk_level}
                                        score={student.fail_risk_score}
                                        size="small"
                                        showScore
                                    />
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Additional Stats */}
            <div className="additional-stats">
                <div className="stat-item">
                    <TrendingUp className="stat-icon" />
                    <div className="stat-content">
                        <span className="stat-label">Hoàn thành trung bình</span>
                        <span className="stat-value">{statistics.avg_completion_rate.toFixed(1)}%</span>
                    </div>
                </div>

                <div className="stat-item">
                    <AlertCircle className="stat-icon inactive" />
                    <div className="stat-content">
                        <span className="stat-label">Học viên không hoạt động &gt; 7 ngày</span>
                        <span className="stat-value">{statistics.inactive_students}</span>
                    </div>
                </div>

                <div className="stat-item">
                    <AlertTriangle className="stat-icon failing" />
                    <div className="stat-content">
                        <span className="stat-label">Học viên điểm dưới 40%</span>
                        <span className="stat-value">{statistics.failing_students}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
