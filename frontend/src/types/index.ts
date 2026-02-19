// Student types
export type CompletionStatus = 'completed' | 'not_passed' | 'in_progress';

export interface Student {
  user_id: number;
  email: string;
  full_name: string;
  username?: string;
  mssv?: string;
  fail_risk_score: number;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  mooc_grade_percentage: number;
  mooc_completion_rate: number;
  days_since_last_activity: number;
  mooc_is_passed?: boolean | number | null;  // Can be boolean (true/false) or int (1/0) from MySQL
  completion_status?: CompletionStatus;
}

export interface StudentDetail extends Student {
  video_completion_rate?: number;
  quiz_avg_score?: number;
  discussion_threads_count?: number;
  suggestions: Suggestion[];
}

export interface Suggestion {
  icon: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

// Course types
export interface Course {
  course_id: string;
  student_count: number;
}

// Statistics types
export interface CourseStatistics {
  total_students: number;
  avg_risk_score: number;
  avg_grade: number;
  avg_completion_rate: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  // Completion status stats
  completed_count: number;
  not_passed_count: number;
  in_progress_count: number;
}

// API Response types
export interface CoursesResponse {
  courses: Course[];
  total: number;
}

export interface StudentsResponse {
  students: Student[];
  total: number;
  course_id: string;
}

export interface StatisticsResponse {
  course_id: string;
  statistics: CourseStatistics;
}

export interface StudentDetailResponse extends StudentDetail {}

// Intervention types
export interface InterventionRequest {
  action: string;
  notes: string;
}

export interface InterventionResponse {
  success: boolean;
  message: string;
  user_id: number;
  course_id: string;
  action: string;
}

// Filter types
export type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'ALL';
export type CompletionFilter = 'ALL' | 'completed' | 'not_completed';
export type SortBy = 'risk_score' | 'name' | 'grade' | 'last_activity';
export type SortOrder = 'asc' | 'desc';

export interface StudentFilters {
  riskLevel: RiskLevel;
  completionFilter: CompletionFilter;
  sortBy: SortBy;
  order: SortOrder;
  searchQuery: string;
}

// Dashboard Summary types (NEW)
export interface TodayTask {
  user_id: number;
  full_name: string;
  email: string;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  fail_risk_score: number;
  reason: string;
  urgency: 'critical' | 'high' | 'medium';
}

export interface RecentAlert {
  id: number;
  user_id: number;
  full_name: string;
  alert_type: 'risk_increase' | 'inactive' | 'low_progress';
  message: string;
  created_at: string;
}

export interface QuickStats {
  new_high_risk_count: number;
  inactive_students_count: number;
  intervention_pending: number;
}

export interface DashboardSummary {
  course_id: string;
  today_tasks: TodayTask[];
  recent_alerts: RecentAlert[];
  quick_stats: QuickStats;
}

export interface DashboardSummaryResponse extends DashboardSummary {}

// SHAP Explanation types
export interface ShapFactor {
  feature: string;
  label_vi: string;
  shap_value: number;
  feature_value: number | string | null;
}

export interface ShapExplanation {
  user_id: number;
  course_id: string;
  fail_risk_score: number;
  base_value: number;
  risk_factors: ShapFactor[];
  protective_factors: ShapFactor[];
}

