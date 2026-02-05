import { useEffect, useState } from 'react';
import { useDashboard } from '../../context/DashboardContext';
import { getH5PLowPerformance } from '../../services/api';
import './H5PPerformance.css';

interface H5PContent {
  content_id: number;
  content_title: string;
  folder_name: string;
  total_students: number;
  completed_students: number;
  students_not_max_score: number;
  not_max_rate: number;
  completion_rate: number;
  avg_score: number;
  avg_score_completed: number;
  min_score: number;
  max_score: number;
  avg_time_spent_minutes: number;
  difficulty_level: 'HIGH' | 'MEDIUM' | 'LOW';
  needs_attention: boolean;
}

interface H5PStatistics {
  total_contents_analyzed: number;
  avg_completion_rate: number;
  avg_score_all: number;
  high_difficulty_count: number;
  needs_attention_count: number;
}

interface H5PPerformanceData {
  success: boolean;
  course_id: string;
  statistics: H5PStatistics;
  contents: H5PContent[];
}

export default function H5PPerformance() {
  const { selectedCourse } = useDashboard();
  const [h5pData, setH5pData] = useState<H5PPerformanceData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'difficult' | 'easy'>('difficult');

  useEffect(() => {
    if (selectedCourse) {
      loadH5PData();
    }
  }, [selectedCourse]);

  const loadH5PData = async () => {
    if (!selectedCourse) return;

    console.log('[H5P] Loading H5P data for course:', selectedCourse.course_id);
    setIsLoading(true);
    setError(null);

    try {
      const data = await getH5PLowPerformance(selectedCourse.course_id, 20, 3);
      console.log('[H5P] Data received:', data);
      setH5pData(data);
    } catch (err) {
      console.error('[H5P] Error loading H5P data:', err);
      setError(err instanceof Error ? err.message : 'Không thể tải dữ liệu H5P');
    } finally {
      setIsLoading(false);
    }
  };

  const getDifficultyIcon = (level: string) => {
    switch (level) {
      case 'HIGH':
        return '🔴';
      case 'MEDIUM':
        return '🟡';
      case 'LOW':
        return '🟢';
      default:
        return '⚪';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'score-excellent';
    if (score >= 70) return 'score-good';
    if (score >= 50) return 'score-average';
    return 'score-poor';
  };

  const getCompletionColor = (rate: number) => {
    if (rate >= 80) return 'completion-high';
    if (rate >= 60) return 'completion-medium';
    return 'completion-low';
  };

  // Sort contents based on view mode
  const getDisplayContents = () => {
    if (!h5pData?.contents) return [];

    if (viewMode === 'difficult') {
      // Show difficult contents (already sorted by avg_score ASC from API)
      return h5pData.contents.slice(0, 10);
    } else {
      // Show easy contents (highest scores)
      return [...h5pData.contents]
        .sort((a, b) => b.avg_score - a.avg_score)
        .slice(0, 10);
    }
  };

  if (!selectedCourse) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="h5p-performance-card">
        <div className="card-header">
          <div className="header-content">
            <span className="card-icon">📊</span>
            <div className="header-text">
              <h3>H5P Performance</h3>
              <p>Bài tập nào làm tốt/kém nhất</p>
            </div>
          </div>
        </div>
        <div className="card-content loading">
          <div className="loading-spinner"></div>
          <p>Đang tải dữ liệu H5P...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h5p-performance-card">
        <div className="card-header">
          <div className="header-content">
            <span className="card-icon">📊</span>
            <div className="header-text">
              <h3>H5P Performance</h3>
              <p>Bài tập nào làm tốt/kém nhất</p>
            </div>
          </div>
        </div>
        <div className="card-content error">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={loadH5PData} className="retry-button">
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  if (!h5pData?.contents || h5pData.contents.length === 0) {
    return (
      <div className="h5p-performance-card">
        <div className="card-header">
          <div className="header-content">
            <span className="card-icon">📊</span>
            <div className="header-text">
              <h3>H5P Performance</h3>
              <p>Bài tập nào làm tốt/kém nhất</p>
            </div>
          </div>
        </div>
        <div className="card-content empty">
          <span className="empty-icon">📝</span>
          <p>Chưa có dữ liệu H5P cho khóa học này</p>
        </div>
      </div>
    );
  }

  const stats = h5pData.statistics;
  const displayContents = getDisplayContents();

  return (
    <div className="h5p-performance-card">
      <div className="card-header">
        <div className="header-content">
          <span className="card-icon">📊</span>
          <div className="header-text">
            <h3>H5P Performance</h3>
            <p>Bài tập nào làm tốt/kém nhất</p>
          </div>
        </div>
        <div className="view-mode-toggle">
          <button
            className={`toggle-btn ${viewMode === 'difficult' ? 'active' : ''}`}
            onClick={() => setViewMode('difficult')}
          >
            📉 Khó nhất
          </button>
          <button
            className={`toggle-btn ${viewMode === 'easy' ? 'active' : ''}`}
            onClick={() => setViewMode('easy')}
          >
            ⭐ Dễ nhất
          </button>
        </div>
      </div>

      {/* Statistics Summary */}
      <div className="h5p-statistics">
        <div className="stat-item">
          <span className="stat-label">Tổng bài phân tích</span>
          <span className="stat-value">{Number(stats.total_contents_analyzed) || 0}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Điểm TB</span>
          <span className={`stat-value ${getScoreColor(Number(stats.avg_score_all) || 0)}`}>
            {Number(stats.avg_score_all || 0).toFixed(1)}%
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Tỉ lệ hoàn thành TB</span>
          <span className={`stat-value ${getCompletionColor(Number(stats.avg_completion_rate) || 0)}`}>
            {Number(stats.avg_completion_rate || 0).toFixed(1)}%
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Bài cần chú ý</span>
          <span className="stat-value stat-highlight">
            {Number(stats.needs_attention_count) || 0}
          </span>
        </div>
      </div>

      {/* Content List */}
      <div className="h5p-content-list">
        {displayContents.map((content, index) => (
          <div
            key={content.content_id}
            className={`h5p-content-item ${content.needs_attention ? 'needs-attention' : ''}`}
          >
            <div className="content-rank">
              {index + 1}
            </div>

            <div className="content-info">
              <div className="content-title-row">
                <span className="difficulty-icon">
                  {getDifficultyIcon(content.difficulty_level)}
                </span>
                <h4 className="content-title">{content.content_title}</h4>
              </div>
              <p className="content-folder">{content.folder_name}</p>
            </div>

            <div className="content-metrics">
              <div className="metric">
                <span className="metric-label">Điểm TB</span>
                <span className={`metric-value ${getScoreColor(content.avg_score)}`}>
                  {Number(content.avg_score || 0).toFixed(1)}%
                </span>
              </div>
              <div className="metric">
                <span className="metric-label">SV không max</span>
                <span className={`metric-value ${content.not_max_rate > 70 ? 'score-poor' : content.not_max_rate > 50 ? 'score-average' : 'score-good'}`}>
                  {content.students_not_max_score}/{content.total_students}
                </span>
              </div>
              <div className="metric">
                <span className="metric-label">Hoàn thành</span>
                <span className={`metric-value ${getCompletionColor(content.completion_rate)}`}>
                  {Number(content.completion_rate || 0).toFixed(0)}%
                </span>
              </div>
            </div>

            {content.needs_attention && (
              <div className="attention-badge">
                ⚠️ Cần chú ý
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="card-footer">
        <button className="view-all-button" onClick={loadH5PData}>
          🔄 Làm mới
        </button>
      </div>
    </div>
  );
}
