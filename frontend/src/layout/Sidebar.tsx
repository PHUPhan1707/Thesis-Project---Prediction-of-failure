import { NavLink } from 'react-router-dom';
import './Sidebar.css';

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">📊</div>
        <div className="brand-text">
          <div className="brand-title">Teacher Dashboard</div>
          <div className="brand-subtitle">Early Warning</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🏠</span>
          <span className="nav-label">Tổng quan</span>
        </NavLink>

        <NavLink to="/h5p-analytics" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">📚</span>
          <span className="nav-label">Phân tích H5P</span>
        </NavLink>

        <NavLink to="/details" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">👥</span>
          <span className="nav-label">Chi tiết</span>
        </NavLink>



        <NavLink to="/pipeline" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🔬</span>
          <span className="nav-label">Pipeline Monitor</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="footer-chip">Open edX • Analytics</div>
      </div>
    </aside>
  );
}

export default Sidebar;


