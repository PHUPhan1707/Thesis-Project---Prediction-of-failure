import { useEffect } from 'react';
import { useDashboard } from '../context/DashboardContext';
import {
  AverageMetrics,
  RiskDistributionChart,
  StatisticsCards,
  TodaysTasks,
  RecentAlerts,
  QuickActions,
  H5PPerformance
} from '../components/Dashboard';
import './Overview.css';

export default function Overview() {
  const {
    selectedCourse,
    dashboardSummary,
    isLoadingDashboardSummary,
    loadDashboardSummary,
    refreshData,
    isLoadingStatistics
  } = useDashboard();

  // Load dashboard summary when course changes
  useEffect(() => {
    if (selectedCourse) {
      loadDashboardSummary();
    }
  }, [selectedCourse, loadDashboardSummary]);

  if (!selectedCourse) {
    return (
      <div className="no-course-selected">
        <span className="no-course-icon">📚</span>
        <h3>Chọn một khóa học để bắt đầu</h3>
        <p>Vui lòng chọn khóa học từ danh sách bên trên để xem thông tin tổng quan</p>
      </div>
    );
  }

  const handleRefresh = async () => {
    await Promise.all([
      refreshData(),
      loadDashboardSummary(),
    ]);
  };

  return (
    <div className="overview">
      {/* Statistics Section */}
      <section className="section statistics-section">
        <StatisticsCards />
        <AverageMetrics />
      </section>

      {/* Main Dashboard Grid */}
      <section className="section dashboard-grid">
        {/* Left Column */}
        <div className="dashboard-column left-column">
          <TodaysTasks
            tasks={dashboardSummary?.today_tasks || []}
            isLoading={isLoadingDashboardSummary}
          />
          <RecentAlerts
            alerts={dashboardSummary?.recent_alerts || []}
            isLoading={isLoadingDashboardSummary}
          />
        </div>

        {/* Right Column */}
        <div className="dashboard-column right-column">
          <RiskDistributionChart />
          <QuickActions
            stats={dashboardSummary?.quick_stats || null}
            onRefresh={handleRefresh}
            isLoading={isLoadingDashboardSummary || isLoadingStatistics}
          />
        </div>
      </section>

      {/* H5P Performance Section */}
      <section className="section h5p-section">
        <H5PPerformance />
      </section>
    </div>
  );
}
