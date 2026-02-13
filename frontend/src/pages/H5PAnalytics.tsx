import { useDashboard } from '../context/DashboardContext';
import H5PPerformance from '../components/Dashboard/H5PPerformance';
import './H5PAnalytics.css';

export default function H5PAnalytics() {
    const { selectedCourse } = useDashboard();

    if (!selectedCourse) {
        return (
            <div className="no-course-selected">
                <span className="no-course-icon">📚</span>
                <h3>Chọn một khóa học để bắt đầu</h3>
                <p>Vui lòng chọn khóa học từ danh sách bên trên để xem phân tích H5P</p>
            </div>
        );
    }

    return (
        <div className="h5p-analytics-page">
            {/* Page Header */}
            <div className="page-header">
                <div className="header-content">
                    <h1 className="page-title">
                        <span className="page-icon">📚</span>
                        Phân tích H5P
                    </h1>
                    <p className="page-description">
                        Phân tích chi tiết hiệu suất học tập qua các bài tập H5P
                    </p>
                </div>
            </div>

            {/* Main Content */}
            <div className="page-content">
                <H5PPerformance />
            </div>
        </div>
    );
}
