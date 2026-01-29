import { Outlet } from 'react-router-dom';
import { useDashboard } from '../context/DashboardContext';
import { CourseSelector, Header, StudentDetailModal } from '../components/Dashboard';
import { Sidebar } from './Sidebar';
import './DashboardLayout.css';

export function DashboardLayout() {
  const { error } = useDashboard();

  return (
    <div className="app-shell">
      <Sidebar />

      <div className="app-main">
        <Header />

        <main className="app-content">
          <div className="dashboard-container">
            <CourseSelector />

            {error && (
              <div className="error-banner">
                <span className="error-icon">⚠️</span>
                <span className="error-message">{error}</span>
              </div>
            )}

            <Outlet />
          </div>
        </main>

        <footer className="dashboard-footer">
          <p>© 2025 Teacher Dashboard - Open edX Analytics Platform</p>
          <p className="footer-subtitle">Hệ thống phân tích dữ liệu và hỗ trợ quyết định cho giảng viên</p>
        </footer>
      </div>

      {/* Shared modal for student detail */}
      <StudentDetailModal />
    </div>
  );
}

export default DashboardLayout;


