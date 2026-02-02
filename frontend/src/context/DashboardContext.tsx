import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type {
    Course,
    CourseStatistics,
    DashboardSummary,
    RiskLevel,
    Student,
    StudentDetail,
    StudentFilters,
} from '../types';
import api from '../services/api';

interface DashboardContextType {
    // State
    courses: Course[];
    selectedCourse: Course | null;
    students: Student[];
    selectedStudent: StudentDetail | null;
    statistics: CourseStatistics | null;
    dashboardSummary: DashboardSummary | null;
    filters: StudentFilters;

    // Loading states
    isLoadingCourses: boolean;
    isLoadingStudents: boolean;
    isLoadingStudentDetail: boolean;
    isLoadingStatistics: boolean;
    isLoadingDashboardSummary: boolean;

    // Error states
    error: string | null;

    // Actions
    setSelectedCourse: (course: Course | null) => void;
    setSelectedStudent: (student: StudentDetail | null) => void;
    setFilters: (filters: Partial<StudentFilters>) => void;
    refreshData: () => Promise<void>;
    loadStudentDetail: (userId: number) => Promise<void>;
    loadDashboardSummary: () => Promise<void>;
    closeStudentDetail: () => void;
}

const defaultFilters: StudentFilters = {
    riskLevel: 'ALL',
    sortBy: 'risk_score',
    order: 'desc',
    searchQuery: '',
};

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

function toNumber(value: unknown, fallback = 0): number {
    if (value === null || value === undefined) return fallback;
    const n = typeof value === 'number' ? value : Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function toInt(value: unknown, fallback = 0): number {
    const n = toNumber(value, fallback);
    return Number.isFinite(n) ? Math.trunc(n) : fallback;
}

function normalizeCourseStatistics(raw: any): CourseStatistics {
    return {
        total_students: toInt(raw?.total_students),
        avg_risk_score: toNumber(raw?.avg_risk_score),
        avg_grade: toNumber(raw?.avg_grade),
        avg_completion_rate: toNumber(raw?.avg_completion_rate),
        high_risk_count: toInt(raw?.high_risk_count),
        medium_risk_count: toInt(raw?.medium_risk_count),
        low_risk_count: toInt(raw?.low_risk_count),
        completed_count: toInt(raw?.completed_count),
        not_passed_count: toInt(raw?.not_passed_count),
        in_progress_count: toInt(raw?.in_progress_count),
    };
}

export function DashboardProvider({ children }: { children: ReactNode }) {
    // State
    const [courses, setCourses] = useState<Course[]>([]);
    const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
    const [students, setStudents] = useState<Student[]>([]);
    const [selectedStudent, setSelectedStudent] = useState<StudentDetail | null>(null);
    const [statistics, setStatistics] = useState<CourseStatistics | null>(null);
    const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
    const [filters, setFiltersState] = useState<StudentFilters>(defaultFilters);

    // Loading states
    const [isLoadingCourses, setIsLoadingCourses] = useState(true);
    const [isLoadingStudents, setIsLoadingStudents] = useState(false);
    const [isLoadingStudentDetail, setIsLoadingStudentDetail] = useState(false);
    const [isLoadingStatistics, setIsLoadingStatistics] = useState(false);
    const [isLoadingDashboardSummary, setIsLoadingDashboardSummary] = useState(false);

    // Error state
    const [error, setError] = useState<string | null>(null);

    // Load courses on mount
    useEffect(() => {
        const loadCourses = async () => {
            try {
                setIsLoadingCourses(true);
                setError(null);
                const response = await api.getCourses();
                setCourses(response.courses);

                // Auto-select first course if available
                if (response.courses.length > 0) {
                    setSelectedCourse(response.courses[0]);
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load courses');
            } finally {
                setIsLoadingCourses(false);
            }
        };

        loadCourses();
    }, []);

    // Load students and statistics when course or filters change
    useEffect(() => {
        if (!selectedCourse) {
            setStudents([]);
            setStatistics(null);
            return;
        }

        const loadData = async () => {
            try {
                setIsLoadingStudents(true);
                setIsLoadingStatistics(true);
                setError(null);

                // Load students and statistics in parallel
                const [studentsResponse, statsResponse] = await Promise.all([
                    api.getStudents(
                        selectedCourse.course_id,
                        filters.riskLevel === 'ALL' ? undefined : filters.riskLevel as RiskLevel,
                        filters.sortBy,
                        filters.order
                    ),
                    api.getCourseStatistics(selectedCourse.course_id),
                ]);

                // Filter locally by search query if provided
                let filteredStudents = studentsResponse.students;
                if (filters.searchQuery) {
                    const query = filters.searchQuery.toLowerCase();
                    filteredStudents = filteredStudents.filter(
                        (s) =>
                            s.full_name?.toLowerCase().includes(query) ||
                            s.email?.toLowerCase().includes(query) ||
                            s.user_id.toString().includes(query)
                    );
                }

                setStudents(filteredStudents);
                setStatistics(normalizeCourseStatistics(statsResponse.statistics));
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load data');
            } finally {
                setIsLoadingStudents(false);
                setIsLoadingStatistics(false);
            }
        };

        loadData();
    }, [selectedCourse, filters.riskLevel, filters.sortBy, filters.order, filters.searchQuery]);

    // Load student detail
    const loadStudentDetail = useCallback(async (userId: number) => {
        if (!selectedCourse) return;

        try {
            setIsLoadingStudentDetail(true);
            setError(null);
            const detail = await api.getStudentDetail(userId, selectedCourse.course_id);
            setSelectedStudent(detail);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load student detail');
        } finally {
            setIsLoadingStudentDetail(false);
        }
    }, [selectedCourse]);

    // Close student detail modal
    const closeStudentDetail = useCallback(() => {
        setSelectedStudent(null);
    }, []);

    // Update filters
    const setFilters = useCallback((newFilters: Partial<StudentFilters>) => {
        setFiltersState((prev) => ({ ...prev, ...newFilters }));
    }, []);

    // Refresh all data
    const refreshData = useCallback(async () => {
        if (!selectedCourse) return;

        try {
            setIsLoadingStudents(true);
            setIsLoadingStatistics(true);
            setError(null);

            const [studentsResponse, statsResponse] = await Promise.all([
                api.getStudents(
                    selectedCourse.course_id,
                    filters.riskLevel === 'ALL' ? undefined : filters.riskLevel as RiskLevel,
                    filters.sortBy,
                    filters.order
                ),
                api.getCourseStatistics(selectedCourse.course_id),
            ]);

            setStudents(studentsResponse.students);
            setStatistics(normalizeCourseStatistics(statsResponse.statistics));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to refresh data');
        } finally {
            setIsLoadingStudents(false);
            setIsLoadingStatistics(false);
        }
    }, [selectedCourse, filters]);

    // Load dashboard summary
    const loadDashboardSummary = useCallback(async () => {
        if (!selectedCourse) return;

        try {
            setIsLoadingDashboardSummary(true);
            const summary = await api.getDashboardSummary(selectedCourse.course_id);
            setDashboardSummary(summary);
        } catch (err) {
            console.error('Failed to load dashboard summary:', err);
        } finally {
            setIsLoadingDashboardSummary(false);
        }
    }, [selectedCourse]);

    const value: DashboardContextType = {
        courses,
        selectedCourse,
        students,
        selectedStudent,
        statistics,
        dashboardSummary,
        filters,
        isLoadingCourses,
        isLoadingStudents,
        isLoadingStudentDetail,
        isLoadingStatistics,
        isLoadingDashboardSummary,
        error,
        setSelectedCourse,
        setSelectedStudent,
        setFilters,
        refreshData,
        loadStudentDetail,
        loadDashboardSummary,
        closeStudentDetail,
    };

    return (
        <DashboardContext.Provider value={value}>
            {children}
        </DashboardContext.Provider>
    );
}

export function useDashboard() {
    const context = useContext(DashboardContext);
    if (context === undefined) {
        throw new Error('useDashboard must be used within a DashboardProvider');
    }
    return context;
}

export default DashboardContext;
