import type {
  CoursesResponse,
  DashboardSummaryResponse,
  InterventionRequest,
  InterventionResponse,
  RiskLevel,
  ShapExplanation,
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

// Generic fetch wrapper with retry + exponential backoff
async function fetchAPI<T>(endpoint: string, options?: RequestInit, retries = 3): Promise<T> {
  const delays = [0, 400, 1200]; // ms before each attempt

  for (let attempt = 0; attempt < retries; attempt++) {
    if (attempt > 0) {
      await new Promise(r => setTimeout(r, delays[attempt]));
    }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const err = new Error(errorData.error || `HTTP error! status: ${response.status}`);
        // Don't retry on client errors (4xx) except 429 Too Many Requests
        const status = response.status;
        if (status >= 400 && status < 500 && status !== 429) throw err;
        if (attempt === retries - 1) throw err;
        continue;
      }

      return await response.json();
    } catch (error) {
      if (attempt === retries - 1) {
        throw error instanceof Error ? error : new Error('An unknown error occurred');
      }
    }
  }

  throw new Error('Max retries exceeded');
}

// Health check
export async function checkHealth(): Promise<{ status: string; timestamp: string; service: string }> {
  return fetchAPI('/health');
}

// Get all courses
export async function getCourses(): Promise<CoursesResponse> {
  return fetchAPI('/courses');
}

// Get students for a course with optional filters and pagination
export async function getStudents(
  courseId: string,
  riskLevel?: RiskLevel,
  sortBy: SortBy = 'risk_score',
  order: SortOrder = 'desc',
  page: number = 1,
  limit: number = 50
): Promise<StudentsResponse> {
  const params = new URLSearchParams();

  if (riskLevel && riskLevel !== 'ALL') {
    params.append('risk_level', riskLevel);
  }
  params.append('sort_by', sortBy);
  params.append('order', order);
  params.append('page', page.toString());
  params.append('limit', limit.toString());

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

// H5P Analytics APIs (NEW)
export async function getH5PLowPerformance(
  courseId: string,
  limit: number = 10,
  minStudents: number = 3
): Promise<any> {
  const encodedCourseId = encodeURIComponent(courseId);
  const params = new URLSearchParams({
    limit: limit.toString(),
    min_students: minStudents.toString(),
  });
  const url = `/h5p-analytics/${encodedCourseId}/low-performance?${params}`;
  console.log('[API] Calling H5P API:', {
    courseId,
    encodedCourseId,
    fullUrl: `${API_BASE_URL}${url}`
  });
  return fetchAPI(url);
}

export async function getH5PContentDetail(courseId: string, contentId: number): Promise<any> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/h5p-analytics/${encodedCourseId}/content/${contentId}`);
}

export async function getH5PStudentPerformance(courseId: string, userId: number): Promise<any> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/h5p-analytics/${encodedCourseId}/student/${userId}`);
}

// Get SHAP explanation for a student
export async function getStudentExplanation(
  userId: number,
  courseId: string
): Promise<ShapExplanation> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/student/${userId}/${encodedCourseId}/explain`);
}

// Preview bulk email recipients count
export async function previewEmailRecipients(courseId: string, target: string): Promise<{ total: number; has_email: number }> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/email/preview/${encodedCourseId}?target=${target}`);
}

// Get list of recipient emails to build mailto link
export async function getEmailRecipients(courseId: string, target: string): Promise<{ emails: string[]; total: number }> {
  const encodedCourseId = encodeURIComponent(courseId);
  return fetchAPI(`/email/recipients/${encodedCourseId}?target=${target}`);
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
  getH5PLowPerformance,
  getH5PContentDetail,
  getH5PStudentPerformance,
  getStudentExplanation,
  previewEmailRecipients,
  getEmailRecipients,
};

export default api;

