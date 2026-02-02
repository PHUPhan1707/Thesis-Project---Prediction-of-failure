import type {
  CoursesResponse,
  DashboardSummaryResponse,
  InterventionRequest,
  InterventionResponse,
  RiskLevel,
  SortBy,
  SortOrder,
  StatisticsResponse,
  StudentDetailResponse,
  StudentsResponse,
} from '../types';

function getApiBaseUrl() {
  // Expected: VITE_API_URL=http://localhost:5000 (see docs)
  const origin = (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:5000';
  return `${origin.replace(/\/$/, '')}/api`;
}

const API_BASE_URL = getApiBaseUrl();

// Generic fetch wrapper with error handling
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('An unknown error occurred');
  }
}

// Health check
export async function checkHealth(): Promise<{ status: string; timestamp: string; service: string }> {
  return fetchAPI('/health');
}

// Get all courses
export async function getCourses(): Promise<CoursesResponse> {
  return fetchAPI('/courses');
}

// Get students for a course with optional filters
export async function getStudents(
  courseId: string,
  riskLevel?: RiskLevel,
  sortBy: SortBy = 'risk_score',
  order: SortOrder = 'desc'
): Promise<StudentsResponse> {
  const params = new URLSearchParams();
  
  if (riskLevel && riskLevel !== 'ALL') {
    params.append('risk_level', riskLevel);
  }
  params.append('sort_by', sortBy);
  params.append('order', order);

  const queryString = params.toString();
  const encodedCourseId = encodeURIComponent(courseId);
  
  return fetchAPI(`/students/${encodedCourseId}?${queryString}`);
}

// Get student detail
export async function getStudentDetail(
  userId: number,
  courseId: string
): Promise<StudentDetailResponse> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/student/${userId}/${encodedCourseId}`);
}

// Get course statistics
export async function getCourseStatistics(courseId: string): Promise<StatisticsResponse> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/statistics/${encodedCourseId}`);
}

// Record intervention
export async function recordIntervention(
  userId: number,
  courseId: string,
  intervention: InterventionRequest
): Promise<InterventionResponse> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/interventions/${userId}/${encodedCourseId}`, {
    method: 'POST',
    body: JSON.stringify(intervention),
  });
}

// Get Dashboard Summary (NEW)
export async function getDashboardSummary(courseId: string): Promise<DashboardSummaryResponse> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/dashboard-summary/${encodedCourseId}`);
}

// Get Urgent Students (NEW)
export async function getUrgentStudents(courseId: string): Promise<StudentsResponse> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/students/${encodedCourseId}/urgent`);
}

// Export all API functions
export const api = {
  checkHealth,
  getCourses,
  getStudents,
  getStudentDetail,
  getCourseStatistics,
  recordIntervention,
  getDashboardSummary,
  getUrgentStudents,
};

export default api;

