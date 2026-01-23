/**
 * API Service Layer
 * Handles all HTTP requests to the backend API
 */
import axios, { AxiosInstance } from 'axios';
import type {
  Course,
  Student,
  StudentDetail,
  CourseStatistics,
  StudentFilters,
  CoursesResponse,
  StudentsResponse,
  StatisticsResponse,
  InterventionResponse,
  InterventionAction
} from '../types';

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================================
// API Service Functions
// ============================================================

/**
 * Health check endpoint
 */
export const healthCheck = async (): Promise<any> => {
  const response = await apiClient.get('/api/health');
  return response.data;
};

/**
 * Get list of available courses
 */
export const getCourses = async (): Promise<Course[]> => {
  const response = await apiClient.get<CoursesResponse>('/api/courses');
  return response.data.courses;
};

/**
 * Get students for a specific course with optional filters
 */
export const getStudents = async (
  courseId: string,
  filters?: StudentFilters
): Promise<Student[]> => {
  const params = new URLSearchParams();
  
  if (filters?.risk_level && filters.risk_level !== 'ALL') {
    params.append('risk_level', filters.risk_level);
  }
  
  if (filters?.sort_by) {
    params.append('sort_by', filters.sort_by);
  }
  
  if (filters?.order) {
    params.append('order', filters.order);
  }
  
  const response = await apiClient.get<StudentsResponse>(
    `/api/students/${encodeURIComponent(courseId)}`,
    { params }
  );
  
  return response.data.students;
};

/**
 * Get detailed information for a specific student
 */
export const getStudentDetail = async (
  userId: number,
  courseId: string
): Promise<StudentDetail> => {
  const response = await apiClient.get<StudentDetail>(
    `/api/student/${userId}/${encodeURIComponent(courseId)}`
  );
  return response.data;
};

/**
 * Get course statistics
 */
export const getCourseStatistics = async (
  courseId: string
): Promise<CourseStatistics> => {
  const response = await apiClient.get<StatisticsResponse>(
    `/api/statistics/${encodeURIComponent(courseId)}`
  );
  return response.data.statistics;
};

/**
 * Record an intervention action
 */
export const recordIntervention = async (
  intervention: InterventionAction
): Promise<InterventionResponse> => {
  const { user_id, course_id, action, notes } = intervention;
  const response = await apiClient.post<InterventionResponse>(
    `/api/interventions/${user_id}/${encodeURIComponent(course_id)}`,
    { action, notes }
  );
  return response.data;
};

/**
 * Export students to CSV (client-side conversion)
 */
export const exportStudentsToCSV = (students: Student[], filename: string = 'students.csv'): void => {
  if (students.length === 0) return;
  
  // CSV headers
  const headers = [
    'User ID',
    'Name',
    'Email',
    'Risk Level',
    'Risk Score',
    'Grade (%)',
    'Completion Rate (%)',
    'Days Since Last Activity',
    'Video Completion (%)',
    'Quiz Avg Score',
    'Discussion Interactions'
  ];
  
  // CSV rows
  const rows = students.map(student => [
    student.user_id,
    student.full_name || 'N/A',
    student.email || 'N/A',
    student.risk_level,
    student.fail_risk_score?.toFixed(2) || '0',
    student.mooc_grade_percentage?.toFixed(2) || '0',
    student.mooc_completion_rate?.toFixed(2) || '0',
    student.days_since_last_activity || '0',
    student.video_completion_rate?.toFixed(2) || '0',
    student.quiz_avg_score?.toFixed(2) || '0',
    student.discussion_total_interactions || '0'
  ]);
  
  // Combine headers and rows
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n');
  
  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export default {
  healthCheck,
  getCourses,
  getStudents,
  getStudentDetail,
  getCourseStatistics,
  recordIntervention,
  exportStudentsToCSV,
};
