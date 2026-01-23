/**
 * TypeScript Types and Interfaces for Teacher Dashboard
 */

// ============================================================
// Enums
// ============================================================

export type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type InterventionPriority = 'high' | 'medium' | 'low';

export type SortBy = 'risk_score' | 'name' | 'grade' | 'last_activity';

export type SortOrder = 'asc' | 'desc';

// ============================================================
// Student Types
// ============================================================

export interface Student {
  user_id: number;
  email: string;
  full_name: string;
  fail_risk_score: number;
  risk_level: RiskLevel;
  mooc_grade_percentage: number;
  mooc_completion_rate: number;
  days_since_last_activity: number;
  last_activity: string | null;
  video_completion_rate: number;
  quiz_avg_score: number;
  discussion_total_interactions: number;
  h5p_completion_rate: number;
}

export interface StudentDetail extends Student {
  username: string;
  mssv?: string;
  class_code?: string;
  department?: string;
  faculty?: string;
  enrollment_id: number;
  mode: string;
  is_active: boolean;
  enrollment_date: string;
  
  // Additional metrics
  enrollment_mode: string;
  weeks_since_enrollment: number;
  mooc_letter_grade?: string;
  mooc_is_passed?: boolean;
  progress_percent: number;
  current_chapter?: string;
  current_section?: string;
  current_unit?: string;
  overall_completion: number;
  completed_blocks: number;
  total_blocks: number;
  access_frequency: number;
  active_days: number;
  
  // H5P data
  h5p_total_contents: number;
  h5p_completed_contents: number;
  h5p_total_score: number;
  h5p_total_max_score: number;
  h5p_overall_percentage: number;
  h5p_total_time_spent: number;
  
  // Video data
  video_total_videos: number;
  video_completed_videos: number;
  video_in_progress_videos: number;
  video_total_duration: number;
  video_total_watched_time: number;
  video_watch_rate: number;
  
  // Quiz data
  quiz_attempts: number;
  quiz_completion_rate: number;
  
  // Discussion data
  discussion_threads_count: number;
  discussion_comments_count: number;
  discussion_questions_count: number;
  discussion_total_upvotes: number;
  
  // Predictions
  dropout_risk_score?: number;
  
  // Metadata
  extracted_at: string;
  
  // Suggestions
  suggestions: InterventionSuggestion[];
}

// ============================================================
// Course Types
// ============================================================

export interface Course {
  course_id: string;
  student_count: number;
}

export interface CourseStatistics {
  total_students: number;
  avg_risk_score: number;
  avg_grade: number;
  avg_completion_rate: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  high_risk_percentage: number;
  medium_risk_percentage: number;
  low_risk_percentage: number;
  inactive_students: number;
  failing_students: number;
}

// ============================================================
// Intervention Types
// ============================================================

export interface InterventionSuggestion {
  icon: string;
  title: string;
  description: string;
  priority: InterventionPriority;
}

export interface InterventionAction {
  user_id: number;
  course_id: string;
  action: string;
  notes?: string;
  timestamp?: string;
}

// ============================================================
// Filter and UI Types
// ============================================================

export interface StudentFilters {
  risk_level?: RiskLevel | 'ALL';
  sort_by?: SortBy;
  order?: SortOrder;
  search?: string;
}

export interface DashboardContextType {
  selectedCourse: string | null;
  setSelectedCourse: (courseId: string | null) => void;
  courses: Course[];
  loading: boolean;
  error: string | null;
}

// ============================================================
// API Response Types
// ============================================================

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface StudentsResponse {
  students: Student[];
  total: number;
  course_id: string;
}

export interface CoursesResponse {
  courses: Course[];
  total: number;
}

export interface StatisticsResponse {
  course_id: string;
  statistics: CourseStatistics;
}

export interface InterventionResponse {
  success: boolean;
  message: string;
  user_id: number;
  course_id: string;
  action: string;
}
