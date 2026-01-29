import { useDashboard } from '../context/DashboardContext';
import { AverageMetrics, RiskDistributionChart, StatisticsCards } from '../components/Dashboard';
import './Overview.css';

export default function Overview() {
  const { selectedCourse } = useDashboard();

  if (!selectedCourse) {
    return (
      <div className="no-course-selected">
        <span className="no-course-icon">📚</span>
        <h3>Chọn một khóa học để bắt đầu</h3>
        <p>Vui lòng chọn khóa học từ danh sách bên trên để xem thông tin tổng quan</p>
      </div>
    );
  }

  return (
    <div className="overview">
      <section className="section statistics-section">
        <StatisticsCards />
        <AverageMetrics />
      </section>

      <section className="section overview-chart">
        <RiskDistributionChart />
      </section>
    </div>
  );
}


