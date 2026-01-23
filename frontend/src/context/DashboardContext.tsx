/**
 * Dashboard Context
 * Provides global state for selected course and courses list
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Course, DashboardContextType } from '../types';
import { getCourses } from '../services/api';

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export const DashboardProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
    const [courses, setCourses] = useState<Course[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchCourses = async () => {
            try {
                setLoading(true);
                const data = await getCourses();
                setCourses(data);

                // Auto-select first course if available
                if (data.length > 0 && !selectedCourse) {
                    setSelectedCourse(data[0].course_id);
                }

                setError(null);
            } catch (err) {
                console.error('Failed to fetch courses:', err);
                setError('Không thể tải danh sách khóa học');
            } finally {
                setLoading(false);
            }
        };

        fetchCourses();
    }, []);

    return (
        <DashboardContext.Provider
            value={{
                selectedCourse,
                setSelectedCourse,
                courses,
                loading,
                error,
            }}
        >
            {children}
        </DashboardContext.Provider>
    );
};

export const useDashboard = (): DashboardContextType => {
    const context = useContext(DashboardContext);
    if (context === undefined) {
        throw new Error('useDashboard must be used within a DashboardProvider');
    }
    return context;
};
