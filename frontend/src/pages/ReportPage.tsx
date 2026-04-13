import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDashboard } from '../context/DashboardContext';
import { getStudents } from '../services/api';
import type { Student } from '../types';
import './ReportPage.css';

function getRiskBadgeClass(level: string) {
  if (level === 'HIGH') return 'badge-high';
  if (level === 'MEDIUM') return 'badge-medium';
  return 'badge-low';
}

function getRiskLabel(level: string) {
  if (level === 'HIGH') return 'Cao';
  if (level === 'MEDIUM') return 'Trung bình';
  return 'Thấp';
}

export default function ReportPage() {
  const navigate = useNavigate();
  const { selectedCourse, statistics, dashboardSummary, isLoadingStatistics } = useDashboard();

  const [highRiskStudents, setHighRiskStudents] = useState<Student[]>([]);
  const [isLoadingStudents, setIsLoadingStudents] = useState(false);

  const fetchHighRiskStudents = useCallback(async () => {
    if (!selectedCourse) return;
    setIsLoadingStudents(true);
    try {
      const res = await getStudents(selectedCourse.course_id, 'HIGH', 'risk_score', 'desc', 1, 200);
      setHighRiskStudents(res.students);
    } finally {
      setIsLoadingStudents(false);
    }
  }, [selectedCourse]);

  useEffect(() => {
    fetchHighRiskStudents();
  }, [fetchHighRiskStudents]);

  if (!selectedCourse) {
    return (
      <div className="report-no-course">
        <span>📚</span>
        <h3>Chưa chọn khóa học</h3>
        <p>Vui lòng chọn khóa học trước khi xem báo cáo.</p>
        <button className="btn-back" onClick={() => navigate('/')}>Quay lại Tổng quan</button>
      </div>
    );
  }

  const stats = statistics;
  const summary = dashboardSummary;
  const generatedAt = new Date().toLocaleString('vi-VN');
  const courseName = selectedCourse.course_name || selectedCourse.course_id;

  const totalStudents = stats?.total_students ?? 0;
  const highRisk = stats?.high_risk_count ?? 0;
  const mediumRisk = stats?.medium_risk_count ?? 0;
  const lowRisk = stats?.low_risk_count ?? 0;
  const completed = stats?.completed_count ?? 0;
  const inProgress = stats?.in_progress_count ?? 0;
  const notPassed = stats?.not_passed_count ?? 0;
  const avgRisk = Number(stats?.avg_risk_score ?? 0).toFixed(1);
  const avgGrade = Number(stats?.avg_grade ?? 0).toFixed(1);
  const avgCompletion = Number(stats?.avg_completion_rate ?? 0).toFixed(1);

  const pct = (val: number) =>
    totalStudents > 0 ? ((val / totalStudents) * 100).toFixed(1) : '0';

  return (
    <div className="report-page">
      {/* Toolbar (hidden when printing) */}
      <div className="report-toolbar no-print">
        <button className="btn-back" onClick={() => navigate('/')}>
          ← Quay lại
        </button>
        <div className="toolbar-right">
          <button className="btn-print" onClick={() => window.print()}>
            🖨️ In báo cáo
          </button>
        </div>
      </div>

      {/* Report Document */}
      <div className="report-doc">
        {/* Header */}
        <div className="report-header">
          <div className="report-header-left">
            <div className="report-logo">📊</div>
            <div>
              <h1 className="report-title">Báo Cáo Tổng Quan</h1>
              <div className="report-subtitle">Hệ thống cảnh báo sớm nguy cơ bỏ học</div>
            </div>
          </div>
          <div className="report-header-right">
            <div className="report-meta-item">
              <span className="meta-label">Khóa học</span>
              <span className="meta-value">{courseName}</span>
            </div>
            <div className="report-meta-item">
              <span className="meta-label">ID khóa học</span>
              <span className="meta-value">{selectedCourse.course_id}</span>
            </div>
            <div className="report-meta-item">
              <span className="meta-label">Ngày tạo</span>
              <span className="meta-value">{generatedAt}</span>
            </div>
          </div>
        </div>

        <div className="report-divider" />

        {/* Section 1: Tổng quan thống kê */}
        <section className="report-section">
          <h2 className="section-title">
            <span className="section-icon">📈</span>
            Tổng Quan Thống Kê
          </h2>

          {isLoadingStatistics ? (
            <div className="report-loading">Đang tải dữ liệu...</div>
          ) : (
            <>
              {/* Summary cards */}
              <div className="summary-cards">
                <div className="summary-card card-blue">
                  <div className="summary-card-value">{totalStudents}</div>
                  <div className="summary-card-label">Tổng sinh viên</div>
                </div>
                <div className="summary-card card-green">
                  <div className="summary-card-value">{completed}</div>
                  <div className="summary-card-label">Đã hoàn thành</div>
                  <div className="summary-card-pct">{pct(completed)}%</div>
                </div>
                <div className="summary-card card-yellow">
                  <div className="summary-card-value">{inProgress}</div>
                  <div className="summary-card-label">Đang học</div>
                  <div className="summary-card-pct">{pct(inProgress)}%</div>
                </div>
                <div className="summary-card card-gray">
                  <div className="summary-card-value">{notPassed}</div>
                  <div className="summary-card-label">Chưa đạt</div>
                  <div className="summary-card-pct">{pct(notPassed)}%</div>
                </div>
              </div>

              {/* Avg metrics */}
              <div className="avg-metrics-row">
                <div className="avg-metric">
                  <span className="avg-metric-icon">📊</span>
                  <div className="avg-metric-info">
                    <span className="avg-metric-label">Điểm rủi ro trung bình</span>
                    <span className={`avg-metric-value ${Number(avgRisk) > 50 ? 'text-danger' : 'text-success'}`}>
                      {avgRisk}%
                    </span>
                  </div>
                </div>
                <div className="avg-metric">
                  <span className="avg-metric-icon">📝</span>
                  <div className="avg-metric-info">
                    <span className="avg-metric-label">Điểm trung bình</span>
                    <span className={`avg-metric-value ${Number(avgGrade) < 50 ? 'text-danger' : 'text-success'}`}>
                      {avgGrade}%
                    </span>
                  </div>
                </div>
                <div className="avg-metric">
                  <span className="avg-metric-icon">📈</span>
                  <div className="avg-metric-info">
                    <span className="avg-metric-label">Tiến độ hoàn thành trung bình</span>
                    <span className={`avg-metric-value ${Number(avgCompletion) < 50 ? 'text-danger' : 'text-success'}`}>
                      {avgCompletion}%
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </section>

        <div className="report-divider" />

        {/* Section 2: Phân phối rủi ro */}
        <section className="report-section">
          <h2 className="section-title">
            <span className="section-icon">🎯</span>
            Phân Phối Mức Độ Rủi Ro
          </h2>

          <div className="risk-distribution">
            <div className="risk-bar-group">
              <div className="risk-bar-item">
                <div className="risk-bar-header">
                  <span className="risk-badge badge-high">Cao</span>
                  <span className="risk-bar-count">{highRisk} sinh viên</span>
                  <span className="risk-bar-pct">{pct(highRisk)}%</span>
                </div>
                <div className="risk-bar-track">
                  <div
                    className="risk-bar-fill fill-high"
                    style={{ width: `${pct(highRisk)}%` }}
                  />
                </div>
              </div>

              <div className="risk-bar-item">
                <div className="risk-bar-header">
                  <span className="risk-badge badge-medium">Trung bình</span>
                  <span className="risk-bar-count">{mediumRisk} sinh viên</span>
                  <span className="risk-bar-pct">{pct(mediumRisk)}%</span>
                </div>
                <div className="risk-bar-track">
                  <div
                    className="risk-bar-fill fill-medium"
                    style={{ width: `${pct(mediumRisk)}%` }}
                  />
                </div>
              </div>

              <div className="risk-bar-item">
                <div className="risk-bar-header">
                  <span className="risk-badge badge-low">Thấp</span>
                  <span className="risk-bar-count">{lowRisk} sinh viên</span>
                  <span className="risk-bar-pct">{pct(lowRisk)}%</span>
                </div>
                <div className="risk-bar-track">
                  <div
                    className="risk-bar-fill fill-low"
                    style={{ width: `${pct(lowRisk)}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="risk-summary-box">
              <div className="risk-summary-title">Tóm tắt</div>
              <div className="risk-summary-row">
                <span>Sinh viên cần can thiệp ngay:</span>
                <strong className="text-danger">{highRisk} ({pct(highRisk)}%)</strong>
              </div>
              <div className="risk-summary-row">
                <span>Sinh viên cần theo dõi:</span>
                <strong className="text-warning">{mediumRisk} ({pct(mediumRisk)}%)</strong>
              </div>
              <div className="risk-summary-row">
                <span>Sinh viên ổn định:</span>
                <strong className="text-success">{lowRisk} ({pct(lowRisk)}%)</strong>
              </div>
            </div>
          </div>
        </section>

        <div className="report-divider" />

        {/* Section 3: Danh sách sinh viên nguy cơ cao */}
        <section className="report-section">
          <h2 className="section-title">
            <span className="section-icon">🚨</span>
            Danh Sách Sinh Viên Nguy Cơ Cao
            <span className="section-count">{highRiskStudents.length} sinh viên</span>
          </h2>

          {isLoadingStudents ? (
            <div className="report-loading">Đang tải danh sách sinh viên...</div>
          ) : highRiskStudents.length === 0 ? (
            <div className="report-empty">Không có sinh viên nguy cơ cao.</div>
          ) : (
            <table className="report-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Họ tên</th>
                  <th>Email</th>
                  <th>Mức rủi ro</th>
                  <th>Điểm rủi ro</th>
                  <th>Điểm TB (%)</th>
                  <th>Tiến độ (%)</th>
                  <th>Ngày vắng (ngày)</th>
                </tr>
              </thead>
              <tbody>
                {highRiskStudents.map((s, idx) => (
                  <tr key={s.user_id}>
                    <td className="td-idx">{idx + 1}</td>
                    <td className="td-name">{s.full_name || s.username || `#${s.user_id}`}</td>
                    <td className="td-email">{s.email}</td>
                    <td>
                      <span className={`risk-badge ${getRiskBadgeClass(s.risk_level)}`}>
                        {getRiskLabel(s.risk_level)}
                      </span>
                    </td>
                    <td className="td-score text-danger">
                      {(s.fail_risk_score * 100).toFixed(1)}%
                    </td>
                    <td className={Number(s.h5p_avg_score) < 50 ? 'text-danger' : ''}>
                      {Number(s.h5p_avg_score ?? 0).toFixed(1)}
                    </td>
                    <td className={Number(s.mooc_completion_rate) < 50 ? 'text-danger' : ''}>
                      {Number(s.mooc_completion_rate).toFixed(1)}
                    </td>
                    <td className={s.days_since_last_activity > 14 ? 'text-danger' : ''}>
                      {s.days_since_last_activity ?? '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        {/* Section 4: Nhiệm vụ can thiệp hôm nay */}
        {summary && summary.today_tasks.length > 0 && (
          <>
            <div className="report-divider" />
            <section className="report-section">
              <h2 className="section-title">
                <span className="section-icon">📋</span>
                Nhiệm Vụ Can Thiệp Ưu Tiên
                <span className="section-count">{summary.today_tasks.length} sinh viên</span>
              </h2>
              <table className="report-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Họ tên</th>
                    <th>Email</th>
                    <th>Mức độ khẩn cấp</th>
                    <th>Điểm rủi ro</th>
                    <th>Lý do</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.today_tasks.map((task, idx) => (
                    <tr key={task.user_id}>
                      <td className="td-idx">{idx + 1}</td>
                      <td className="td-name">{task.full_name}</td>
                      <td className="td-email">{task.email}</td>
                      <td>
                        <span className={`urgency-badge urgency-${task.urgency}`}>
                          {task.urgency === 'critical' ? 'Khẩn cấp' : task.urgency === 'high' ? 'Cao' : 'Trung bình'}
                        </span>
                      </td>
                      <td className="text-danger">
                        {(task.fail_risk_score * 100).toFixed(1)}%
                      </td>
                      <td className="td-reason">{task.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </>
        )}

        {/* Footer */}
        <div className="report-footer">
          <span>Được tạo bởi Teacher Dashboard • Early Warning System</span>
          <span>{generatedAt}</span>
        </div>
      </div>
    </div>
  );
}
