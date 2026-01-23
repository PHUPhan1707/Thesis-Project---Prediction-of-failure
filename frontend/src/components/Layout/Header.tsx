/**
 * Header Component
 * Displays course selector and user info
 */
import React from 'react';
import { ChevronDown, BookOpen } from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import './Header.css';

const Header: React.FC = () => {
    const { courses, selectedCourse, setSelectedCourse } = useDashboard();

    const handleCourseChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSelectedCourse(e.target.value);
    };

    return (
        <header className="header">
            <div className="header-content">
                <div className="header-left">
                    <div className="course-selector-wrapper">
                        <BookOpen className="course-selector-icon" />
                        <select
                            className="course-selector"
                            value={selectedCourse || ''}
                            onChange={handleCourseChange}
                        >
                            {courses.length === 0 ? (
                                <option value="">Không có khóa học</option>
                            ) : (
                                courses.map((course) => (
                                    <option key={course.course_id} value={course.course_id}>
                                        {course.course_id} ({course.student_count} học viên)
                                    </option>
                                ))
                            )}
                        </select>
                        <ChevronDown className="course-selector-chevron" />
                    </div>
                </div>

                <div className="header-right">
                    <div className="user-info">
                        <div className="user-avatar">
                            GV
                        </div>
                        <div className="user-details">
                            <span className="user-name">Giảng viên</span>
                            <span className="user-role">Teacher</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
