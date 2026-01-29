import { useDashboard } from '../../context/DashboardContext';
import './Header.css';

export function Header() {
    const { selectedCourse, statistics, refreshData, isLoadingStudents } = useDashboard();

    const handleRefresh = async () => {
        await refreshData();
    };

    return (
        <header className="dashboard-header">
            <div className="header-left">
                <div className="header-logo">
                    <span className="logo-icon">📊</span>
                    <div className="logo-text">
                        <h1>Teacher Dashboard</h1>
                        <span className="logo-subtitle">Open edX Analytics Platform</span>
                    </div>
                </div>
            </div>

            <div className="header-center">
                {selectedCourse && (
                    <div className="course-info">
                        <span className="course-label">Khóa học đang xem:</span>
                        <span className="course-name">{selectedCourse.course_id.split(':').pop()}</span>
                        {statistics && (
                            <span className="student-count">
                                {statistics.total_students} sinh viên
                            </span>
                        )}
                    </div>
                )}
            </div>

            <div className="header-right">
                <button
                    className={`refresh-btn ${isLoadingStudents ? 'loading' : ''}`}
                    onClick={handleRefresh}
                    disabled={isLoadingStudents}
                >
                    <span className="refresh-icon">🔄</span>
                    {isLoadingStudents ? 'Đang tải...' : 'Làm mới'}
                </button>

                <div className="header-user">
                    <div className="user-avatar">👤</div>
                    <div className="user-info">
                        <span className="user-name">Giảng viên</span>
                        <span className="user-role">Instructor</span>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;
