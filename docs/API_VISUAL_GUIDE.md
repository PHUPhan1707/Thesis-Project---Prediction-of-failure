# 📊 API Data Flow Visualization

## Current vs Future State

```mermaid
graph TB
    subgraph "CURRENT - Course-Level Only"
        API1[Advanced Stats API]
        API1 -->|Course avg: 75.5| DB1[(course_stats_benchmarks)]
        DB1 -->|Calculate relative| MODEL1[Model V4: 83.64% recall]
    end
    
    subgraph "FUTURE - Per-User Data"
        API2A[Activity Stats API]
        API2B[Assessments API]
        API2C[Progress Weekly API]
        
        API2A -->|User 1: streak=12, consistency=0.75| DB2A[(activity_stats)]
        API2B -->|User 1: attempts=2.1, improvement=10%| DB2B[(assessment_details)]
        API2C -->|User 1: velocity declining| DB2C[(progress_tracking)]
        
        DB2A --> FEATURES[30+ Behavioral Features]
        DB2B --> FEATURES
        DB2C --> FEATURES
        
        FEATURES --> MODEL2[Model V5: 89-92% recall]
    end
    
    style MODEL2 fill:#90EE90
    style MODEL1 fill:#FFE4B5
```

## Data Collection Flow

```mermaid
sequenceDiagram
    participant ML as ML Pipeline
    participant API as MOOC API
    participant DB as Database
    participant Model as CatBoost Model
    
    Note over ML,Model: For each student (921 total)
    
    ML->>API: GET /students/{user_id}/activity-stats/
    API-->>ML: problem_improvement: 10.5%, consistency: 0.75
    
    ML->>API: GET /students/{user_id}/assessments/
    API-->>ML: avg_attempts: 2.1, pass_rate: 83%
    
    ML->>API: GET /students/{user_id}/progress-weekly/
    API-->>ML: velocity_trend: "declining"
    
    ML->>DB: Store in activity_stats, assessment_details
    ML->>DB: Aggregate into raw_data
    
    DB-->>ML: Load features (95 columns)
    ML->>Model: Train with behavioral features
    Model-->>ML: Predictions (89-92% recall)
```

## Feature Impact Analysis

```mermaid
graph LR
    subgraph "High Impact Features"
        F1[problem_improvement_rate]
        F2[activity_consistency]
        F3[velocity_trend]
        F4[longest_streak]
    end
    
    subgraph "Medium Impact Features"
        F5[avg_attempts_to_pass]
        F6[late_night_ratio]
        F7[first_vs_best_gap]
    end
    
    F1 -->|Importance: 15-20| RECALL[+5-8% Recall]
    F2 -->|Importance: 10-15| RECALL
    F3 -->|Importance: 12-18| RECALL
    F4 -->|Importance: 8-12| RECALL
    
    F5 -->|Importance: 6-10| PRECISION[+1-3% Precision]
    F6 -->|Importance: 4-8| PRECISION
    F7 -->|Importance: 5-9| PRECISION
    
    RECALL --> IMPACT[45-75 more students caught]
    PRECISION --> IMPACT
    
    style IMPACT fill:#FFD700,stroke:#333,stroke-width:4px
```

## API Implementation Priority

```mermaid
gantt
    title API Development Timeline
    dateFormat YYYY-MM-DD
    section Phase 1
    Activity Stats API           :a1, 2026-02-01, 14d
    Progress Weekly API          :a2, 2026-02-08, 14d
    Database Schema             :a3, 2026-02-01, 7d
    Testing Phase 1             :a4, 2026-02-15, 7d
    
    section Phase 2
    Assessments API             :b1, 2026-02-22, 10d
    Time Pattern Features       :b2, 2026-02-25, 7d
    Testing Phase 2             :b3, 2026-03-04, 5d
    
    section Deployment
    ML Model V5 Training        :c1, 2026-03-09, 3d
    Production Deployment       :c2, 2026-03-12, 2d
```

## Expected Student Risk Detection

```mermaid
pie title Model V4 (Current) - 235 High Risk
    "Correctly Identified" : 197
    "Missed (False Negative)" : 38
    
pie title Model V5 (Future) - 280 High Risk
    "Correctly Identified" : 252
    "Missed (False Negative)" : 3
```

**Improvement:** 55 more students caught! (197 → 252)

---

## Key Metrics Summary

| Metric | Current (V4) | Future (V5) | Change |
|--------|-------------|-------------|---------|
| **Recall** | 83.64% | **89-92%** | **+5-8%** |
| **Students Caught** | 197/235 | **252-280/280** | **+55-83** |
| **False Negatives** | 38 | **3-8** | **-30-35** |
| **Features Used** | 82 | **110+** | +28 |
| **Top Feature** | current_chapter (19.42) | **velocity_trend (18-22)** | New! |

---

## Database Schema Additions

```sql
-- New tables needed
CREATE TABLE activity_stats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    problem_attempts INT,
    problem_improvement_rate DECIMAL(5,2),
    activity_consistency DECIMAL(5,4),
    longest_streak INT,
    late_night_ratio DECIMAL(5,4),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_course (user_id, course_id)
);

CREATE TABLE assessment_details (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    avg_attempts_to_pass DECIMAL(5,2),
    first_attempt_avg DECIMAL(5,2),
    best_attempt_avg DECIMAL(5,2),
    pass_rate DECIMAL(5,2),
    INDEX idx_user_course (user_id, course_id)
);

CREATE TABLE progress_tracking (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    week_number INT,
    velocity DECIMAL(5,2),
    velocity_trend ENUM('improving', 'stable', 'declining'),
    is_on_track BOOLEAN,
    INDEX idx_user_course_week (user_id, course_id, week_number)
);
```
