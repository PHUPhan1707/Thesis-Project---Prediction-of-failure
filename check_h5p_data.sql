-- ============================================================
-- SQL Queries để kiểm tra dữ liệu H5P trong database
-- ============================================================

-- 1. Kiểm tra có dữ liệu H5P không
SELECT COUNT(*) as total_records,
       COUNT(DISTINCT course_id) as total_courses,
       COUNT(DISTINCT user_id) as total_users,
       COUNT(DISTINCT content_id) as total_contents
FROM h5p_scores;

-- 2. Xem danh sách courses có dữ liệu H5P
SELECT course_id,
       COUNT(DISTINCT user_id) as total_students,
       COUNT(DISTINCT content_id) as total_contents,
       COUNT(*) as total_records
FROM h5p_scores
GROUP BY course_id
ORDER BY total_records DESC;

-- 3. Xem mẫu dữ liệu H5P (10 records đầu)
SELECT user_id,
       course_id,
       content_id,
       content_title,
       folder_name,
       score,
       max_score,
       percentage,
       opened,
       finished,
       time_spent,
       FROM_UNIXTIME(opened) as opened_time,
       FROM_UNIXTIME(finished) as finished_time
FROM h5p_scores
LIMIT 10;

-- 4. Top 10 bài H5P có điểm trung bình thấp nhất (cần ít nhất 5 SV làm)
SELECT content_id,
       content_title,
       folder_name,
       COUNT(DISTINCT user_id) as total_students,
       COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) as completed_students,
       ROUND(COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) * 100.0 / COUNT(DISTINCT user_id), 2) as completion_rate,
       ROUND(AVG(percentage), 2) as avg_score,
       MIN(percentage) as min_score,
       MAX(percentage) as max_score
FROM h5p_scores
WHERE course_id = 'YOUR_COURSE_ID_HERE'  -- Thay YOUR_COURSE_ID_HERE bằng course_id thực tế
GROUP BY content_id, content_title, folder_name
HAVING total_students >= 5
ORDER BY avg_score ASC
LIMIT 10;

-- 5. Phân bố điểm của một bài H5P cụ thể
SELECT 
    CASE 
        WHEN percentage >= 90 THEN '90-100 (Excellent)'
        WHEN percentage >= 80 THEN '80-89 (Good)'
        WHEN percentage >= 70 THEN '70-79 (Average)'
        WHEN percentage >= 50 THEN '50-69 (Below Average)'
        WHEN percentage > 0 THEN '1-49 (Poor)'
        ELSE '0 (Not Attempted)'
    END as score_range,
    COUNT(*) as student_count
FROM h5p_scores
WHERE course_id = 'YOUR_COURSE_ID_HERE'  -- Thay YOUR_COURSE_ID_HERE
  AND content_id = 123  -- Thay 123 bằng content_id thực tế
GROUP BY score_range
ORDER BY MIN(percentage) DESC;

-- 6. Sinh viên có điểm H5P thấp nhất trong khóa học
SELECT h.user_id,
       e.full_name,
       e.email,
       e.mssv,
       COUNT(DISTINCT h.content_id) as total_contents_attempted,
       ROUND(AVG(h.percentage), 2) as avg_score,
       COUNT(DISTINCT CASE WHEN h.finished > 0 THEN h.content_id END) as completed_contents
FROM h5p_scores h
LEFT JOIN enrollments e ON h.user_id = e.user_id AND h.course_id = e.course_id
WHERE h.course_id = 'YOUR_COURSE_ID_HERE'  -- Thay YOUR_COURSE_ID_HERE
GROUP BY h.user_id, e.full_name, e.email, e.mssv
HAVING completed_contents > 0
ORDER BY avg_score ASC
LIMIT 10;

-- 7. Thống kê tổng quan H5P của một khóa học
SELECT 
    COUNT(DISTINCT content_id) as total_h5p_contents,
    COUNT(DISTINCT user_id) as total_students,
    COUNT(*) as total_interactions,
    COUNT(CASE WHEN finished > 0 THEN 1 END) as total_completions,
    ROUND(COUNT(CASE WHEN finished > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as overall_completion_rate,
    ROUND(AVG(percentage), 2) as avg_score_all,
    ROUND(AVG(CASE WHEN finished > 0 THEN percentage END), 2) as avg_score_completed,
    ROUND(AVG(time_spent), 0) as avg_time_spent_seconds,
    ROUND(AVG(time_spent) / 60, 1) as avg_time_spent_minutes
FROM h5p_scores
WHERE course_id = 'YOUR_COURSE_ID_HERE';  -- Thay YOUR_COURSE_ID_HERE

-- 8. Bài H5P nào nhiều sinh viên mở nhưng không hoàn thành
SELECT content_id,
       content_title,
       folder_name,
       COUNT(*) as total_opened,
       COUNT(CASE WHEN finished > 0 THEN 1 END) as total_finished,
       COUNT(CASE WHEN finished = 0 THEN 1 END) as opened_but_not_finished,
       ROUND(COUNT(CASE WHEN finished = 0 THEN 1 END) * 100.0 / COUNT(*), 2) as abandon_rate
FROM h5p_scores
WHERE course_id = 'YOUR_COURSE_ID_HERE'  -- Thay YOUR_COURSE_ID_HERE
  AND opened > 0
GROUP BY content_id, content_title, folder_name
HAVING total_opened >= 5
ORDER BY abandon_rate DESC
LIMIT 10;

-- 9. H5P performance của một sinh viên cụ thể
SELECT content_id,
       content_title,
       folder_name,
       score,
       max_score,
       percentage,
       CASE 
           WHEN percentage >= 90 THEN 'Excellent'
           WHEN percentage >= 80 THEN 'Good'
           WHEN percentage >= 50 THEN 'Needs Improvement'
           WHEN finished > 0 THEN 'Poor'
           ELSE 'Not Attempted'
       END as performance_level,
       ROUND(time_spent / 60, 1) as time_spent_minutes,
       FROM_UNIXTIME(opened) as opened_time,
       FROM_UNIXTIME(finished) as finished_time
FROM h5p_scores
WHERE course_id = 'YOUR_COURSE_ID_HERE'  -- Thay YOUR_COURSE_ID_HERE
  AND user_id = 101  -- Thay 101 bằng user_id thực tế
ORDER BY percentage ASC;

-- 10. Correlation giữa time_spent và percentage
-- (Bài nào dùng nhiều thời gian nhưng điểm vẫn thấp = bài khó)
SELECT content_id,
       content_title,
       folder_name,
       COUNT(DISTINCT user_id) as total_students,
       ROUND(AVG(percentage), 2) as avg_score,
       ROUND(AVG(time_spent) / 60, 1) as avg_time_minutes,
       ROUND(AVG(percentage) / NULLIF(AVG(time_spent) / 60, 0), 2) as score_per_minute
FROM h5p_scores
WHERE course_id = 'YOUR_COURSE_ID_HERE'  -- Thay YOUR_COURSE_ID_HERE
  AND finished > 0
  AND time_spent > 0
GROUP BY content_id, content_title, folder_name
HAVING total_students >= 5
ORDER BY score_per_minute ASC
LIMIT 10;

-- ============================================================
-- HƯỚNG DẪN SỬ DỤNG:
-- 1. Thay 'YOUR_COURSE_ID_HERE' bằng course_id thực tế của bạn
--    Ví dụ: 'course-v1:VNUHCM+FM101+2024_T1'
-- 2. Chạy query trong MySQL Workbench hoặc command line
-- 3. Xem kết quả để hiểu dữ liệu H5P của bạn
-- ============================================================

-- Lấy danh sách course_id có trong database
SELECT DISTINCT course_id 
FROM h5p_scores 
ORDER BY course_id;
