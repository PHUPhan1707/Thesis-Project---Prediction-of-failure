# CHƯƠNG 2
# TỔNG QUAN VỀ HỆ THỐNG VÀ CƠ SỞ LÝ THUYẾT

## 2.1. Đặc điểm dữ liệu học tập trong môi trường MOOC

Hệ thống Massive Open Online Course (MOOC) tạo ra khối lượng lớn dữ liệu hành vi học tập (learning traces), thường liên quan đến hàng trăm đến hàng nghìn người học mỗi khóa học. Khác với môi trường lớp học truyền thống, nơi dữ liệu chủ yếu bao gồm điểm số và phản hồi được ghi lại thủ công, môi trường MOOC tự động ghi nhận các bản ghi chi tiết về lịch sử truy cập, tương tác với nội dung học tập, tiến độ học tập, kết quả đánh giá và hoạt động diễn đàn thảo luận.

Trong hệ thống của đề tài này, dữ liệu học tập được thu thập từ nền tảng Open edX tích hợp với hệ thống nội dung tương tác H5P, bao gồm các nhóm dữ liệu chính sau:

### (i) Dữ liệu đăng ký và thông tin sinh viên
- Thông tin cơ bản: user_id, username, email, họ tên, MSSV
- Thông tin đăng ký: enrollment_mode (audit/verified), is_active, ngày đăng ký
- Thông tin bổ sung: lớp, khoa, ngành học (từ user attributes)

### (ii) Dữ liệu tiến độ và hoàn thành khóa học
- Tỷ lệ hoàn thành khóa học (mooc_completion_rate)
- Tiến độ tổng thể (overall_completion)
- Chương/phần/đơn vị học hiện tại (current_chapter, current_section, current_unit)
- Hoạt động gần nhất (last_activity, days_since_last_activity)

### (iii) Dữ liệu điểm số và đánh giá
- Điểm trung bình khóa học (mooc_grade_percentage)
- Kết quả đạt/không đạt (mooc_is_passed, mooc_letter_grade)
- Điểm số bài tập H5P (h5p_total_score, h5p_total_max_score, h5p_overall_percentage)
- Số lần làm bài tập và tỷ lệ hoàn thành (quiz_attempts, quiz_completion_rate)

### (iv) Dữ liệu tương tác với nội dung H5P
- Tổng số nội dung H5P và số nội dung đã hoàn thành
- Điểm số từng bài tập H5P (content_id, score, max_score, percentage)
- Trạng thái hoàn thành (opened, finished)
- Thời gian làm bài (time_spent)
- Thông tin folder/module (folder_id, folder_name)

### (v) Dữ liệu xem video bài giảng
- Tổng số video và số video đã hoàn thành
- Tiến độ xem từng video (progress_percent, current_time, duration)
- Trạng thái video (completed/in_progress/not_started)
- Tỷ lệ hoàn thành video (video_completion_rate)
- Tỷ lệ thời gian xem so với tổng thời lượng (video_watch_rate)

### (vi) Dữ liệu tương tác diễn đàn thảo luận
- Số lượng thread và comment (threads_count, comments_count)
- Tổng số tương tác (total_interactions)
- Số câu hỏi đặt ra (questions_count)
- Số upvote nhận được (total_upvotes)

Các loại dữ liệu này có một số đặc điểm chung:

**(1) Dữ liệu chuỗi thời gian:** Dữ liệu phát triển liên tục trong suốt timeline của khóa học, cho phép theo dõi sự thay đổi hành vi học tập theo thời gian.

**(2) Dữ liệu đa nguồn:** Được tạo ra bởi nhiều thành phần hệ thống khác nhau như LMS (Open edX), nền tảng nội dung tương tác (H5P), và dịch vụ thảo luận.

**(3) Dữ liệu không đồng nhất:** Thường chứa nhiễu, giá trị thiếu hoặc không nhất quán, do sự khác biệt trong hành vi người học, thiết kế khóa học và các vấn đề kỹ thuật trong thu thập log.

Do đó, việc chuẩn hóa dữ liệu, tổng hợp và ánh xạ từ nhiều API vào một mô hình dữ liệu thống nhất là các bước tiên quyết thiết yếu cho các ứng dụng phân tích học tập và cảnh báo sớm.

## 2.2. Các phương pháp phân tích dữ liệu học tập trong MOOC

Trong thập kỷ qua, dữ liệu MOOC đã được phân tích từ nhiều góc độ:

### Phân tích mô tả (Descriptive Analytics)
Tập trung vào việc tóm tắt hành vi người học, như phân bố đăng nhập, tiến độ học tập trung bình, tỷ lệ hoàn thành khóa học và tỷ lệ bỏ học theo tuần. Các phân tích này thường được trình bày qua dashboard để hỗ trợ hoạt động giám sát của giảng viên.

Trong hệ thống này, phân tích mô tả được thực hiện thông qua:
- Dashboard tổng quan (dashboard_summary) hiển thị overall_completion, total_items, completed_items
- Thống kê video (video_progress_summary) với total_videos, completed_videos, overall_progress
- Thống kê H5P (h5p_scores_summary) với total_contents, completed_contents, average_percentage

### Phân tích chẩn đoán (Diagnostic Analytics)
Nhằm xác định mối quan hệ giữa các chỉ số hành vi (như tần suất đăng nhập, tương tác video, hiệu suất quiz và tham gia diễn đàn) với kết quả học tập hoặc rủi ro bỏ học. Nhiều nghiên cứu báo cáo mối tương quan đáng kể giữa các yếu tố như tần suất truy cập, phạm vi tiến độ, điểm đánh giá trung bình và tương tác diễn đàn với mức độ rủi ro của người học.

Hệ thống này thực hiện phân tích chẩn đoán thông qua:
- **Feature engineering module** (ml/feature_engineering.py) tạo ra các derived features:
  - Engagement score: tổng hợp từ discussion, video, H5P, quiz scores
  - Activity features: activity_recency, activity_consistency, is_inactive
  - Performance features: relative_completion, is_struggling, completion_consistency
  - Interaction features: discussion_engagement_rate, video_engagement_rate
  - Time features: progress_rate, learning_pace_score, enrollment_phase

### Phân tích dự đoán (Predictive Analytics)
Liên quan đến việc xây dựng các mô hình machine learning để dự đoán, ở giai đoạn sớm, những người học có khả năng thất bại hoặc bỏ học khóa học. Các mô hình thường được sử dụng bao gồm logistic regression, decision trees, random forests, support vector machines (SVM), cũng như các mô hình chuỗi thời gian và deep learning.

Hệ thống này sử dụng **CatBoost Classifier** (gradient boosting model) để dự đoán:
- **Fail risk score** (0-100): Xác suất sinh viên sẽ không đạt khóa học
- **Risk level classification**: HIGH (≥55), MEDIUM (30-54), LOW (<30)
- **Model architecture:**
  - Input: 40+ features từ raw data và derived features
  - Categorical features: enrollment_mode, enrollment_phase
  - Training target: is_passed từ mooc_grades
  - Model file: fm101_model_v5.cbm (CatBoost binary format)

### Phân tích can thiệp (Prescriptive Analytics)
Tận dụng kết quả đánh giá rủi ro để đề xuất các hành động can thiệp có mục tiêu cho giảng viên, như gửi email nhắc nhở, đề xuất xem lại video, nhắc hoàn thành bài tập đang chờ xử lý hoặc khuyến khích tham gia diễn đàn thảo luận.

Hệ thống này cung cấp **automated intervention suggestions** dựa trên:
- Risk level và các metrics cụ thể
- Ví dụ suggestions:
  - Days inactive > 14: "Liên hệ trực tiếp" (priority: high)
  - Grade < 40%: "Hỗ trợ học tập" (priority: high)
  - Completion < 30%: "Nhắc nhở lộ trình" (priority: high)
  - No discussion + high risk: "Khuyến khích tương tác" (priority: medium)

Tất cả các phương pháp phân tích này đều yêu cầu một lớp trung gian trích xuất và chuẩn hóa dữ liệu từ nhiều API MOOC và chuyển đổi chúng thành một tập hợp các chỉ số phù hợp làm đầu vào cho các mô hình phân tích và dự đoán.

## 2.3. Các mô hình cảnh báo sớm dựa trên dữ liệu MOOC

Nghiên cứu về hệ thống cảnh báo sớm trong môi trường MOOC chủ yếu tập trung vào việc lựa chọn các chỉ số rủi ro và gán trọng số cho từng chỉ số. Các nhóm chỉ số thường được sử dụng bao gồm:

### Chỉ số truy cập hệ thống
- Tần suất đăng nhập (access_frequency)
- Số ngày hoạt động (active_days)
- Thời gian không hoạt động (days_since_last_activity, max_inactive_gap_days)
- Thời gian học tập theo tuần (weeks_since_enrollment)

### Chỉ số hiệu suất đánh giá
- Điểm số quiz và bài tập (h5p_avg_score, problem_avg_score)
- Số lần thử (quiz_attempts, problem_attempts)
- Tỷ lệ thành công (problem_success_rate, first_attempt_success_rate)
- Số bài tập gặp khó khăn (struggling_assessments_count)

### Chỉ số tiến độ học tập
- Tỷ lệ hoàn thành khóa học (mooc_completion_rate, overall_completion)
- Số đơn vị đã hoàn thành (completed_blocks)
- Tốc độ tiến độ (progress_velocity, progress_rate, learning_pace_score)
- Ước tính thời gian hoàn thành (weeks_to_complete_estimate)

### Chỉ số tương tác nội dung đa phương tiện
- Tỷ lệ hoàn thành video (video_completion_rate)
- Thời gian xem trung bình (video_watch_rate)
- Số lượt xem video (video_views)
- Tỷ lệ hoàn thành nội dung H5P (h5p_completion_rate)

### Chỉ số tham gia diễn đàn
- Số bài đăng và trả lời (threads_count, comments_count)
- Tổng số tương tác (total_interactions)
- Số câu hỏi đặt ra (questions_count)
- Mức độ tương tác diễn đàn tổng thể (discussion_engagement_rate)

### Chỉ số so sánh với khóa học (Comparative Features)
Hệ thống này bổ sung thêm các chỉ số so sánh sinh viên với trung bình khóa học:
- relative_to_course_problem_score
- relative_to_course_completion
- performance_percentile
- is_below_course_average, is_top_performer, is_bottom_performer

Các chỉ số này được tính toán từ **course_stats_benchmarks** table, lưu trữ các giá trị trung bình của khóa học như:
- activity_avg_score, assessment_avg_score
- progress_avg_completion
- total_students, active_students

## 2.4. Định vị nghiên cứu của đề tài

Trong bối cảnh này, luận văn tập trung vào việc phân tích và khai thác dữ liệu học tập trong hệ thống MOOC dựa trên nền tảng Open edX, tích hợp với hệ thống nội dung tương tác H5P. Thay vì truy cập trực tiếp các bảng cơ sở dữ liệu thô, phương pháp được đề xuất sử dụng các API có sẵn của hệ thống để thu thập dữ liệu học tập từ nhiều nguồn:

### Từ Open edX (MOOC Platform)
Các API cung cấp thống kê về hoạt động người học, tiến độ, kết quả đánh giá và tương tác video, cho phép phân tích theo thời gian về hành vi đăng nhập, mức độ hoàn thành, điểm số và tương tác video:

- **Enrollment API** (`/api/custom/v1/course-enrollments-attributes/`):
  - Danh sách sinh viên đăng ký khóa học
  - Thông tin user attributes (MSSV, lớp, khoa)
  - Enrollment mode và trạng thái active

- **Export APIs** (timeout 600s cho khóa học lớn):
  - `/api/custom/v1/export/student-grades/`: Điểm số tổng kết (grade_percentage, is_passed)
  - `/api/custom/v1/export/student-progress/`: Tiến độ học tập (completion_rate, last_activity, current_chapter/section/unit)
  - `/api/custom/v1/export/student-discussions/`: Thống kê diễn đàn (threads, comments, questions, upvotes)

- **Advanced Statistics APIs** (cho course-level benchmarks):
  - `/api/custom/v1/stats/activity/`: Thống kê hoạt động tổng quan
  - `/api/custom/v1/stats/assessment/`: Thống kê đánh giá
  - `/api/custom/v1/stats/progress/`: Thống kê tiến độ

### Từ hệ thống nội dung MOOC dựa trên H5P
Các API cung cấp điểm số nội dung tương tác, tiến độ video và module, và dữ liệu dashboard tổng hợp, cung cấp thông tin chi tiết về tương tác của người học với tài nguyên đa phương tiện và tương tác:

- **H5P Scores API** (`/wp-json/mooc/v1/scores/{user_id}/{course_id}`):
  - Điểm số từng bài tập H5P (content_id, score, max_score, percentage)
  - Trạng thái hoàn thành (opened, finished)
  - Thời gian làm bài (time_spent)
  - Summary: total_contents, completed_contents, overall_percentage

- **Video Progress API** (`/wp-json/mooc/v1/video-progress/{user_id}/{course_id}`):
  - Tiến độ từng video (content_id, progress_percent, current_time, duration)
  - Trạng thái video (completed/in_progress/not_started)
  - Summary: total_videos, completed_videos, overall_progress

- **Combined Progress API** (`/wp-json/mooc/v1/combined-progress/{user_id}/{course_id}`):
  - Tổng hợp overall_completion từ cả H5P và video
  - Thống kê tổng quan: total_items, completed_items, items_to_complete

### Kiến trúc hệ thống xử lý dữ liệu

Dựa trên chiến lược ánh xạ API được thiết kế, luận văn này phát triển một lớp trừu tượng hóa (abstraction layer) để hợp nhất các trường từ nhiều endpoint vào một tập hợp các chỉ số rủi ro thống nhất, tương ứng với tần suất truy cập hệ thống, hiệu suất đánh giá (bao gồm nội dung H5P), tiến độ học tập, tương tác video và hoạt động diễn đàn. Lớp dịch vụ này hoạt động như một cầu nối giữa dữ liệu thô của hệ thống MOOC và mô hình đánh giá rủi ro cảnh báo sớm.

#### 1. Data Collection Layer (database/fetch_mooc_h5p_data.py)
**Class MOOCH5PDataFetcher** chịu trách nhiệm:
- Fetch dữ liệu từ tất cả APIs (MOOC + H5P)
- Lưu vào các bảng normalized:
  - enrollments: Thông tin đăng ký
  - mooc_grades, mooc_progress, mooc_discussions: Dữ liệu từ MOOC Export APIs
  - h5p_scores, h5p_scores_summary: Dữ liệu H5P
  - video_progress, video_progress_summary: Dữ liệu video
  - dashboard_summary: Dữ liệu tổng hợp
  - course_stats_benchmarks: Benchmarks cho comparative features
- Hỗ trợ concurrent fetching với ThreadPoolExecutor (8 workers mặc định)
- Aggregate vào raw_data table với tất cả features

#### 2. Feature Engineering Layer (ml/feature_engineering.py)
**Class FeatureEngineer** tạo derived features:
- Engagement score (weighted average của discussion, video, H5P, quiz)
- Activity features (recency, consistency, inactive flags)
- Performance features (relative_completion, is_struggling, completion_consistency)
- Interaction features (engagement rates cho discussion/video/H5P)
- Time features (progress_rate, learning_pace_score, enrollment_phase)
- Hỗ trợ open course (không có deadline cố định)

#### 3. Model Training Layer (ml/train_model.py)
- Load data từ raw_data table
- Feature engineering với FeatureEngineer
- Train CatBoost model với target is_passed
- Lưu model file (.cbm) và feature importance (.csv)

#### 4. Inference Layer (backend/inference_service.py)
**Class InferenceService** với 3 sub-components:
- **DataFetcher**: Lấy dữ liệu từ database
- **FeaturePreparator**: Tạo feature matrix cho inference (đảm bảo consistency với training)
- **RiskPredictor**: Load model, predict fail_risk_score, SHAP explanation

Public API:
- `predict_course(course_id)`: Dự đoán cho tất cả sinh viên
- `predict_student(course_id, user_id)`: Dự đoán cho một sinh viên
- `explain_student(course_id, user_id)`: SHAP explanation (risk_factors, protective_factors)
- `generate_suggestions(student_data)`: Tạo intervention suggestions

#### 5. Backend API Layer (backend/routes/)
Flask REST APIs cho frontend:
- GET `/api/students/{course_id}`: Danh sách sinh viên với risk scores
- GET `/api/students/{course_id}/{user_id}`: Chi tiết một sinh viên
- GET `/api/students/{course_id}/{user_id}/explain`: SHAP explanation
- POST `/api/fetch-course-data`: Trigger data fetching từ MOOC/H5P APIs

### Đóng góp chính của đề tài

1. **Kiến trúc API-based data collection**: Không truy cập trực tiếp database MOOC, mà sử dụng RESTful APIs → dễ maintain, không phụ thuộc vào schema changes.

2. **Multi-source data integration**: Tích hợp dữ liệu từ 3 nguồn (MOOC platform, H5P system, Discussion service) vào unified data model.

3. **Comprehensive feature engineering**: 40+ features bao gồm raw metrics, derived features và comparative features (so sánh với course benchmarks).

4. **Production-ready ML pipeline**: 
   - CatBoost model với SHAP explainability
   - Consistent feature engineering giữa training và inference
   - Batch prediction với database optimization

5. **Actionable intervention system**: Không chỉ dự đoán risk score mà còn tạo prioritized suggestions cho giảng viên can thiệp kịp thời.

6. **Scalable concurrent processing**: ThreadPoolExecutor cho H5P/Video data fetching, giảm thời gian từ 30+ phút xuống 5-7 phút cho khóa học 200+ sinh viên.

Hệ thống này đóng vai trò như một **early warning system** hoàn chỉnh, từ data collection đến prediction và intervention, hỗ trợ giảng viên chủ động can thiệp để giảm tỷ lệ bỏ học và cải thiện kết quả học tập.
