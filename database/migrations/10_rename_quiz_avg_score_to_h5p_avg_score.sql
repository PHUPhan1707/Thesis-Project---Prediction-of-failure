-- Migration 10: Rename quiz_avg_score → h5p_avg_score
-- Reason: quiz_avg_score was storing h5p_overall_percentage (H5P composite score
-- covering both videos and interactive exercises), not actual quiz scores.
-- The old name was misleading and could cause the model to learn wrong signals.

USE dropout_prediction_db;

-- Table: raw_data
ALTER TABLE raw_data
    CHANGE COLUMN quiz_avg_score h5p_avg_score DECIMAL(5,2) DEFAULT 0
    COMMENT 'H5P overall percentage (video + interactive exercises, not quiz only)';

-- Table: student_features
ALTER TABLE student_features
    CHANGE COLUMN quiz_avg_score h5p_avg_score DECIMAL(5,2) DEFAULT 0
    COMMENT 'H5P overall percentage (video + interactive exercises, not quiz only)';
