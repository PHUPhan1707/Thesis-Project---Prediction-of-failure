import { useDashboard } from '../../context/DashboardContext';
import type { RiskLevel, CompletionFilter } from '../../types';
import { exportStudentsToCSV } from '../../services/exportCsv';
import './StudentFilters.css';

export function StudentFilters() {
    const { filters, setFilters, students, isLoadingStudents, selectedCourse } = useDashboard();

    const riskLevelOptions: { value: RiskLevel; label: string; icon: string; color: string }[] = [
        { value: 'ALL', label: 'Tất cả', icon: '📋', color: 'default' },
        { value: 'HIGH', label: 'Cao', icon: '🚨', color: 'red' },
        { value: 'MEDIUM', label: 'Trung bình', icon: '⚠️', color: 'yellow' },
        { value: 'LOW', label: 'Thấp', icon: '✅', color: 'green' },
    ];

    const completionOptions: { value: CompletionFilter; label: string; icon: string }[] = [
        { value: 'not_completed', label: 'Chưa hoàn thành', icon: '📚' },
        { value: 'completed', label: 'Đã hoàn thành', icon: '🎓' },
        { value: 'ALL', label: 'Tất cả', icon: '📋' },
    ];

    const sortOptions = [
        { value: 'risk_score', label: 'Điểm rủi ro' },
        { value: 'name', label: 'Tên' },
        { value: 'grade', label: 'Điểm số' },
        { value: 'last_activity', label: 'Hoạt động gần nhất' },
    ];

    return (
        <div className="student-filters">
            <div className="filters-header">
                <h3 className="filters-title">
                    <span className="title-icon">👥</span>
                    Danh Sách Học Viên Cần Quan Tâm
                </h3>
                <div className="filters-header-actions">
                    <span className="student-count-badge">
                        {isLoadingStudents ? '...' : students.length} sinh viên
                    </span>
                    <button
                        className="export-btn"
                        disabled={isLoadingStudents || students.length === 0}
                        onClick={() =>
                            exportStudentsToCSV(students, { courseId: selectedCourse?.course_id })
                        }
                        title="Xuất danh sách hiện tại ra CSV"
                    >
                        ⬇️ Export CSV
                    </button>
                </div>
            </div>

            <div className="filters-row">
                {/* Completion Status Filter */}
                <div className="completion-filter">
                    <label className="filter-label">Trạng thái:</label>
                    <div className="completion-buttons">
                        {completionOptions.map((option) => (
                            <button
                                key={option.value}
                                className={`completion-btn ${filters.completionFilter === option.value ? 'active' : ''}`}
                                onClick={() => setFilters({ completionFilter: option.value })}
                            >
                                <span className="btn-icon">{option.icon}</span>
                                <span className="btn-label">{option.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Risk Level Tabs */}
                <div className="risk-tabs">
                    {riskLevelOptions.map((option) => (
                        <button
                            key={option.value}
                            className={`risk-tab risk-tab-${option.color} ${filters.riskLevel === option.value ? 'active' : ''
                                }`}
                            onClick={() => setFilters({ riskLevel: option.value })}
                        >
                            <span className="tab-icon">{option.icon}</span>
                            <span className="tab-label">{option.label}</span>
                        </button>
                    ))}
                </div>

                {/* Search & Sort */}
                <div className="filters-controls">
                    <div className="search-input-wrapper">
                        <span className="search-icon">🔍</span>
                        <input
                            type="text"
                            className="search-input"
                            placeholder="Tìm kiếm theo tên, email..."
                            value={filters.searchQuery}
                            onChange={(e) => setFilters({ searchQuery: e.target.value })}
                        />
                        {filters.searchQuery && (
                            <button
                                className="clear-search"
                                onClick={() => setFilters({ searchQuery: '' })}
                            >
                                ✕
                            </button>
                        )}
                    </div>

                    <div className="sort-controls">
                        <select
                            className="sort-select"
                            value={filters.sortBy}
                            onChange={(e) => setFilters({ sortBy: e.target.value as any })}
                        >
                            {sortOptions.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>

                        <button
                            className={`sort-order-btn ${filters.order}`}
                            onClick={() =>
                                setFilters({ order: filters.order === 'asc' ? 'desc' : 'asc' })
                            }
                            title={filters.order === 'asc' ? 'Tăng dần' : 'Giảm dần'}
                        >
                            {filters.order === 'asc' ? '↑' : '↓'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default StudentFilters;
