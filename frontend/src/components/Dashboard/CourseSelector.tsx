import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDashboard } from '../../context/DashboardContext';
import './CourseSelector.css';

export function CourseSelector() {
    const { courses, selectedCourse, setSelectedCourse, isLoadingCourses } = useDashboard();
    const navigate = useNavigate();
    const location = useLocation();

    const [searchTerm, setSearchTerm] = useState('');
    const [isExpanded, setIsExpanded] = useState(!selectedCourse);

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

    const handleCourseChange = (course: Course) => {
        if (location.pathname.includes('/student/')) {
            navigate('/details');
        }
        setSelectedCourse(course);
        setIsExpanded(false);
    };

    const getDisplayName = (course: Course) => {
        if (course.course_name) return course.course_name;
        const parts = course.course_id.split(':');
        if (parts.length > 1) {
            return parts[1].split('+').slice(0, 2).join(' / ');
        }
        return course.course_id;
    };

    const getCourseTerm = (courseId: string) => {
        const parts = courseId.split(':');
        if (parts.length > 1) {
            const info = parts[1].split('+');
            return info[2] || '';
        }
        return '';
    };

    const filteredCourses = courses.filter((course) => {
        const name = getDisplayName(course).toLowerCase();
        const id = course.course_id.toLowerCase();
        const term = getCourseTerm(course.course_id).toLowerCase();
        const query = searchTerm.toLowerCase();
        return name.includes(query) || id.includes(query) || term.includes(query);
    });

    if (!isExpanded && selectedCourse) {
        const term = getCourseTerm(selectedCourse.course_id);
        return (
            <div className="course-selector-container">
                <div className="selector-header">
                    <span className="selector-icon">📚</span>
                    <span className="selector-label">Khóa học đang xem:</span>
                    <button className="btn-change-course" onClick={() => setIsExpanded(true)}>
                        <span>Đổi khóa học</span>
                        <span className="btn-icon">↓</span>
                    </button>
                </div>
                <div className="selected-course-display">
                    <div className="course-card selected compact">
                        <div className="course-icon">🎓</div>
                        <div className="course-info">
                            <span className="course-code">{getDisplayName(selectedCourse)}</span>
                            {term && <span className="course-term">{term}</span>}
                            <span className="course-students">{selectedCourse.student_count} sinh viên</span>
                        </div>
                        <span className="selected-check">✓</span>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="course-selector-container">
            <div className="selector-header">
                <span className="selector-icon">📚</span>
                <span className="selector-label">Chọn khóa học:</span>
                {selectedCourse && (
                    <button className="btn-collapse" onClick={() => setIsExpanded(false)}>
                        Thu gọn ↑
                    </button>
                )}
            </div>
            <div className="course-search">
                <span className="search-icon">🔍</span>
                <input
                    type="text"
                    placeholder="Tìm kiếm khóa học..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input"
                />
                {searchTerm && (
                    <button className="search-clear" onClick={() => setSearchTerm('')}>
                        ✕
                    </button>
                )}
            </div>
            <div className="course-cards">
                {filteredCourses.length === 0 ? (
                    <div className="no-results">
                        <span>Không tìm thấy khóa học phù hợp</span>
                    </div>
                ) : (
                    filteredCourses.map((course) => {
                        const isSelected = selectedCourse?.course_id === course.course_id;
                        const term = getCourseTerm(course.course_id);

                        return (
                            <button
                                key={course.course_id}
                                className={`course-card ${isSelected ? 'selected' : ''}`}
                                onClick={() => handleCourseChange(course)}
                            >
                                <div className="course-icon">🎓</div>
                                <div className="course-info">
                                    <span className="course-code">{getDisplayName(course)}</span>
                                    {term && <span className="course-term">{term}</span>}
                                    <span className="course-students">{course.student_count} sinh viên</span>
                                </div>
                                {isSelected && <span className="selected-check">✓</span>}
                            </button>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default CourseSelector;
