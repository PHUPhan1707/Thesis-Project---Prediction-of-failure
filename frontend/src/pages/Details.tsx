import { useDashboard } from '../context/DashboardContext';
import { StudentFilters, StudentList } from '../components/Dashboard';
import './Details.css';

export default function Details() {
  const { selectedCourse } = useDashboard();

  if (!selectedCourse) {
    return (
      <div className="no-course-selected">
        <span className="no-course-icon">📚</span>
        <h3>Chọn một khóa học để bắt đầu</h3>
        <p>Vui lòng chọn khóa học từ danh sách bên trên để xem danh sách học viên</p>
      </div>
    );
  }

  return (
    <div className="details">
      <section className="details-content">
        <StudentFilters />
        <StudentList />
      </section>
    </div>
  );
}


