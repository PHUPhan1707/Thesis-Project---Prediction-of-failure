import { useLocation, useNavigate } from 'react-router-dom';
import { useDashboard } from '../../context/DashboardContext';
import './CourseSelector.css';

export function CourseSelector() {
    const { courses, selectedCourse, setSelectedCourse, isLoadingCourses } = useDashboard();
    const navigate = useNavigate();
    const location = useLocation();

    if (isLoadingCourses) {
        return (
            <div className="course-selector loading">
                <div className="selector-skeleton"></div>
            </div>
        );
    }

    if (courses.length === 0) {
        return (
            <div className="course-selector empty">
                <span className="empty-icon">📚</span>
                <span>Không có khóa học</span>
            </div>
        );
    }

    // Parse course name from course_id
    const parseCourseNames = (courseId: string) => {
        const parts = courseId.split(':');
        if (parts.length > 1) {
            const courseInfo = parts[1].split('+');
            return {
                institution: courseInfo[0] || 'Unknown',
                code: courseInfo[1] || 'Unknown',
                term: courseInfo[2] || 'Unknown',
            };
        }
        return { institution: 'Unknown', code: courseId, term: 'Unknown' };
    };

    // Handle course change (redirect if on student detail page)
    const handleCourseChange = (course: Course) => {
        // If currently viewing a student detail page, redirect to main dashboard
        if (location.pathname.includes('/student/')) {
            navigate('/details');
        }
        setSelectedCourse(course);
    };

    return (
        <div className="course-selector-container">
            <div className="selector-header">
                <span className="selector-icon">📚</span>
                <span className="selector-label">Chọn khóa học:</span>
            </div>
            <div className="course-cards">
                {courses.map((course) => {
                    const parsed = parseCourseNames(course.course_id);
                    const isSelected = selectedCourse?.course_id === course.course_id;

                    return (
                        <button
                            key={course.course_id}
                            className={`course-card ${isSelected ? 'selected' : ''}`}
                            onClick={() => handleCourseChange(course)}
                        >
                            <div className="course-icon">🎓</div>
                            <div className="course-info">
                                <span className="course-code">{parsed.code}</span>
                                <span className="course-term">{parsed.term}</span>
                                <span className="course-students">{course.student_count} sinh viên</span>
                            </div>
                            {isSelected && <span className="selected-check">✓</span>}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

export default CourseSelector;
