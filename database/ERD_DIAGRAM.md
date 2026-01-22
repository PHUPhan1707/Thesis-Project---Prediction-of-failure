# Database Schema - ERD Diagram

## Database Structure với MOOC Export APIs

```mermaid
erDiagram
    %% Core Tables
    enrollments ||--o{ mooc_grades : "has grades"
    enrollments ||--o{ mooc_progress : "has progress"
    enrollments ||--o{ mooc_discussions : "has discussions"
    enrollments ||--o{ h5p_scores_summary : "has H5P scores"
    enrollments ||--o{ video_progress_summary : "has video progress"
    enrollments ||--o{ dashboard_summary : "has dashboard"
    enrollments ||--o{ raw_data : "aggregates to"
    
    %% H5P Detail Tables
    h5p_scores ||--|| h5p_scores_summary : "summarizes"
    video_progress ||--|| video_progress_summary : "summarizes"
    
    %% Raw Data Aggregation
    mooc_grades ||--|| raw_data : "feeds into"
    mooc_progress ||--|| raw_data : "feeds into"
    mooc_discussions ||--|| raw_data : "feeds into"
    h5p_scores_summary ||--|| raw_data : "feeds into"
    video_progress_summary ||--|| raw_data : "feeds into"
    dashboard_summary ||--|| raw_data : "feeds into"
    
    enrollments {
        bigint id PK
        varchar course_id
        int user_id
        varchar username
        varchar email
        varchar full_name
        int enrollment_id UK
        varchar mode
        boolean is_active
        datetime created
        json all_attributes
    }
    
    mooc_grades {
        bigint id PK
        int user_id
        varchar course_id
        decimal percent_grade
        decimal grade_percentage
        varchar letter_grade
        boolean is_passed
        datetime fetched_at
    }
    
    mooc_progress {
        bigint id PK
        int user_id
        varchar course_id
        int total_blocks
        int completed_blocks
        decimal progress_percent
        varchar current_chapter "NEW"
        varchar current_section "NEW"
        varchar current_unit "NEW"
        decimal completion_rate "NEW"
        datetime last_activity
    }
    
    mooc_discussions {
        bigint id PK
        int user_id
        varchar course_id
        int threads_count
        int comments_count
        int total_interactions
        int questions_count
        int total_upvotes
        datetime fetched_at
    }
    
    h5p_scores {
        bigint id PK
        int user_id
        varchar course_id
        int content_id
        varchar content_title
        int score
        int max_score
        decimal percentage
    }
    
    h5p_scores_summary {
        bigint id PK
        int user_id
        varchar course_id
        int total_contents
        int completed_contents
        int total_score
        int total_max_score
        decimal overall_percentage
    }
    
    video_progress {
        bigint id PK
        int user_id
        varchar course_id
        int content_id
        varchar content_title
        decimal progress_percent
        int current_time
        int duration
        varchar status
    }
    
    video_progress_summary {
        bigint id PK
        int user_id
        varchar course_id
        int total_videos
        int completed_videos
        int in_progress_videos
        int total_duration
        int total_watched_time
    }
    
    dashboard_summary {
        bigint id PK
        int user_id
        varchar course_id
        decimal overall_completion
        int total_items
        int completed_items
        int h5p_total_contents
        int video_total_videos
    }
    
    raw_data {
        bigint id PK
        int user_id
        varchar course_id
        datetime enrollment_date
        decimal mooc_grade_percentage "NEW"
        varchar mooc_letter_grade "NEW"
        boolean mooc_is_passed "NEW"
        decimal progress_percent
        varchar current_chapter "NEW"
        varchar current_section "NEW"
        varchar current_unit "NEW"
        decimal mooc_completion_rate "NEW"
        int h5p_total_contents
        int video_total_videos
        int discussion_threads_count "NEW"
        int discussion_comments_count "NEW"
        int discussion_total_interactions "NEW"
        boolean is_dropout
        decimal dropout_risk_score
    }
```

## API to Table Mapping

### H5P APIs → Tables

| API Endpoint | Target Tables |
|-------------|---------------|
| `/scores/{user_id}/{course_id}` | `h5p_scores`, `h5p_scores_summary` |
| `/video-progress/{user_id}/{course_id}` | `video_progress`, `video_progress_summary` |
| `/dashboard/{user_id}/{course_id}` | `dashboard_summary` |

### MOOC APIs → Tables

| API Endpoint | Target Tables |
|-------------|---------------|
| `/course-enrollments-attributes/{course_id}/` | `enrollments` |
| `/export/student-grades/{course_id}/` | **`mooc_grades`** ⭐ NEW |
| `/export/student-progress/{course_id}/` | **`mooc_progress`** (updated) ⭐ |
| `/export/student-discussions/{course_id}/` | **`mooc_discussions`** ⭐ NEW |
| `/export/complete-student-data/{course_id}/` | All tables above (aggregate) |

### Data Flow

```
┌─────────────────┐
│  MOOC APIs      │
│  - Enrollments  │
│  - Grades       │──┐
│  - Progress     │  │
│  - Discussions  │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │
│  H5P APIs       │  │         ┌──────────────────┐
│  - Scores       │──┼────────▶│  Detail Tables   │
│  - Video        │  │         │  (mooc_grades,   │
│  - Dashboard    │  │         │   mooc_progress, │
└─────────────────┘  │         │   h5p_scores,    │
                     │         │   etc.)          │
                     │         └──────────────────┘
                     │                 │
                     │                 │
                     │                 ▼
                     │         ┌──────────────────┐
                     │         │  Summary Tables  │
                     └────────▶│  (h5p_summary,   │
                               │   video_summary) │
                               └──────────────────┘
                                       │
                                       │ Aggregate
                                       ▼
                               ┌──────────────────┐
                               │   raw_data       │
                               │  (ML Features)   │
                               └──────────────────┘
```

## Key Relationships

1. **One-to-One**: `(user_id, course_id)` is unique across all main tables
   - Each user has exactly one grade record per course
   - Each user has exactly one progress record per course
   - Etc.

2. **One-to-Many**: 
   - `enrollments` → `h5p_scores` (one user has many H5P content scores)
   - `enrollments` → `video_progress` (one user has many video progress records)

3. **Many-to-One Aggregation**:
   - Many detail tables → One `raw_data` record per user per course
   - Features are calculated and aggregated from all source tables

## Indexes Strategy

### Primary Indexes (Performance Critical)
- `(user_id, course_id)` - UNIQUE on all main tables
- `course_id` - For querying all students in a course
- `user_id` - For querying all courses for a student

### Secondary Indexes (Analytics)
- `grade_percentage`, `completion_rate` - For ranking/filtering
- `total_interactions` - For finding top contributors
- `fetched_at` - For data freshness queries
- `is_passed`, `is_dropout` - For classification queries

## Storage Estimates

Assuming:
- 1,000 students per course
- 10 courses
- Total: 10,000 records

### Table Sizes (Estimated)

| Table | Records | Est. Size per Record | Total Size |
|-------|---------|---------------------|------------|
| `enrollments` | 10,000 | 2 KB | ~20 MB |
| `mooc_grades` | 10,000 | 0.5 KB | ~5 MB |
| `mooc_progress` | 10,000 | 1 KB | ~10 MB |
| `mooc_discussions` | 10,000 | 0.5 KB | ~5 MB |
| `h5p_scores` | 100,000 | 0.3 KB | ~30 MB |
| `h5p_scores_summary` | 10,000 | 0.5 KB | ~5 MB |
| `video_progress` | 50,000 | 0.3 KB | ~15 MB |
| `video_progress_summary` | 10,000 | 0.5 KB | ~5 MB |
| `dashboard_summary` | 10,000 | 1 KB | ~10 MB |
| `raw_data` | 10,000 | 2 KB | ~20 MB |
| **TOTAL** | | | **~125 MB** |

Very manageable size for MySQL/MariaDB.
