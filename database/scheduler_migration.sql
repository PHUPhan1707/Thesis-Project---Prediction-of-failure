-- ============================================================
-- MLOps Scheduler Migration
-- Thêm bảng training_history để log lịch sử auto-train/retrain/predict
-- ============================================================
USE dropout_prediction_db;

CREATE TABLE IF NOT EXISTS training_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    base_name VARCHAR(255) NOT NULL COMMENT 'Tên môn gốc, e.g. Kinh tế vĩ mô',
    course_ids TEXT COMMENT 'Danh sách course_ids đã gộp, JSON array',
    model_name VARCHAR(100),
    action ENUM('initial_train', 'retrain', 'predict', 'check') NOT NULL,
    labeled_student_count INT COMMENT 'Số SV có is_passed (dùng cho train/retrain)',
    predicted_student_count INT COMMENT 'Số SV được predict',
    accuracy DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    auc_roc DECIMAL(5,4),
    status ENUM('success', 'failed', 'skipped') NOT NULL,
    message TEXT,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,

    INDEX idx_base_name (base_name),
    INDEX idx_action (action),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='MLOps Scheduler: lịch sử auto-train, retrain, predict runs';
