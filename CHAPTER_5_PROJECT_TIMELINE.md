# CHAPTER 5. PROJECT TIMELINE

## 5.1. Tổng quan kế hoạch thực hiện

Dự án "Hệ thống dự đoán rủi ro bỏ học sinh viên dựa trên dữ liệu MOOC và H5P" được thực hiện trong khoảng thời gian từ **15/01/2025 đến 29/04/2025** (tổng cộng khoảng 15 tuần). Dự án được chia thành 7 mốc chính, mỗi mốc kéo dài 2-3 tuần, nhằm đảm bảo tiến độ và chất lượng từng giai đoạn.

### Các giai đoạn chính:
1. **Giai đoạn 1**: Khảo sát và phân tích yêu cầu hệ thống
2. **Giai đoạn 2**: Thiết kế kiến trúc dữ liệu và mô hình học máy
3. **Giai đoạn 3**: Xây dựng pipeline thu thập và tổng hợp dữ liệu
4. **Giai đoạn 4**: Nâng cấp mô hình - Phân tích và bổ sung features hiệu quả
5. **Giai đoạn 5**: Huấn luyện, tối ưu và so sánh mô hình
6. **Giai đoạn 6**: Tích hợp mô hình vào hệ thống MOOC
7. **Giai đoạn 7**: Liên kết các chức năng nâng cao và hoàn thiện hệ thống

---

## 5.2. Chi tiết timeline theo từng mốc

### MỐC 1: Khảo sát và Phân tích Yêu cầu
**Thời gian**: 15/01/2025 - 28/01/2025 (2 tuần)

#### Mục tiêu:
- Hiểu rõ bối cảnh bài toán và yêu cầu từ hệ thống MOOC hiện tại
- Xác định phạm vi dữ liệu và các use case chính của hệ thống

#### Nhiệm vụ chi tiết:

**Tuần 1 (15/01 - 21/01/2025)**:
- Thu thập và nghiên cứu tài liệu về hệ thống MOOC hiện tại:
  - Cấu trúc khóa học, API endpoints có sẵn
  - Các loại dữ liệu log và tracking hiện có
  - Quy trình quản lý sinh viên và enrollment
- Khảo sát các nghiên cứu liên quan về dropout prediction trong e-learning
- Xác định các stakeholders: giảng viên, quản trị viên, sinh viên

**Tuần 2 (22/01 - 28/01/2025)**:
- Phân tích yêu cầu chức năng (Functional Requirements):
  - Dashboard cho giảng viên: hiển thị danh sách sinh viên có rủi ro
  - Cảnh báo sớm (early warning) khi phát hiện dấu hiệu dropout
  - Báo cáo thống kê và phân tích xu hướng
- Phân tích yêu cầu phi chức năng (Non-functional Requirements):
  - Hiệu năng: thời gian dự đoán, tần suất cập nhật
  - Độ chính xác: mục tiêu AUC > 0.75, Recall cho lớp dropout > 0.70
- Xác định phạm vi dữ liệu:
  - H5P scores và video progress
  - MOOC grades, progress, discussions
  - Enrollment information
- Hoàn thiện tài liệu đặc tả yêu cầu (Requirements Specification Document)

#### Deliverables:
- Tài liệu đặc tả yêu cầu hệ thống
- Báo cáo khảo sát các nghiên cứu liên quan
- Danh sách API endpoints và dữ liệu có sẵn

---

### MỐC 2: Thiết kế Kiến trúc Dữ liệu và Mô hình
**Thời gian**: 29/01/2025 - 11/02/2025 (2 tuần)

#### Mục tiêu:
- Thiết kế nền tảng dữ liệu vững chắc và kiến trúc mô hình học máy
- Xác định bộ features ban đầu cho mô hình dự đoán

#### Nhiệm vụ chi tiết:

**Tuần 3 (29/01 - 04/02/2025)**:
- Thiết kế database schema:
  - Bảng raw data: `enrollments`, `h5p_scores`, `video_progress`, `mooc_progress`, `mooc_grades`, `mooc_discussions`
  - Bảng tổng hợp: `raw_data` (aggregated features)
  - Bảng metadata: `batch_metadata`, `training_sets`
- Thiết kế data flow:
  ```
  APIs (MOOC/H5P) → Raw Tables → Aggregation → raw_data → Feature Engineering → Model Training
  ```
- Xác định các features ban đầu:
  - Enrollment features: `weeks_since_enrollment`, `enrollment_mode`
  - Progress features: `progress_percent`, `completion_rate`, `days_since_last_activity`
  - H5P features: `h5p_total_contents`, `h5p_completion_rate`, `h5p_overall_percentage`
  - Video features: `video_completion_rate`, `video_watch_rate`
  - Discussion features: `discussion_total_interactions`, `discussion_threads_count`

**Tuần 4 (05/02 - 11/02/2025)**:
- Chọn loại mô hình học máy:
  - So sánh: XGBoost, Random Forest, Gradient Boosting, Neural Networks
  - Quyết định: XGBoost (vì hiệu năng tốt với tabular data và có thể giải thích được)
- Thiết kế pipeline training:
  - Train/Validation/Test split (70/15/15)
  - K-fold cross-validation (k=5)
  - Metrics: AUC-ROC, F1-score, Precision, Recall
- Thiết kế module structure:
  - `feature_engineering.py`: Tạo derived features
  - `storage_manager.py`: Quản lý lưu trữ dữ liệu
  - `train_model.py`: Huấn luyện mô hình
  - `predict.py`: Dự đoán trên dữ liệu mới

#### Deliverables:
- Database schema diagram
- Data flow diagram
- Feature list và mô tả
- Kiến trúc mô hình và pipeline training

---

### MỐC 3: Xây dựng Pipeline Thu thập và Tổng hợp Dữ liệu
**Thời gian**: 12/02/2025 - 25/02/2025 (2 tuần)

#### Mục tiêu:
- Xây dựng pipeline hoàn chỉnh để thu thập dữ liệu từ MOOC/H5P APIs và lưu vào database
- Đảm bảo dữ liệu được tổng hợp đúng cách vào bảng `raw_data`

#### Nhiệm vụ chi tiết:

**Tuần 5 (12/02 - 18/02/2025)**:
- Hoàn thiện script `fetch_mooc_h5p_data.py`:
  - Implement các hàm fetch từ MOOC APIs:
    - `fetch_mooc_course_students()`: Lấy danh sách sinh viên
    - `fetch_mooc_grades()`: Lấy điểm số
    - `fetch_mooc_progress()`: Lấy tiến độ học tập
    - `fetch_mooc_discussions()`: Lấy tương tác thảo luận
  - Implement các hàm fetch từ H5P APIs:
    - `fetch_h5p_scores()`: Lấy điểm H5P
    - `fetch_video_progress()`: Lấy tiến độ video
  - Xử lý authentication (session cookies)
  - Xử lý lỗi và retry logic

**Tuần 6 (19/02 - 25/02/2025)**:
- Xây dựng hàm `aggregate_raw_data()`:
  - Tổng hợp dữ liệu từ các bảng raw vào bảng `raw_data`
  - Tính toán các features cơ bản: completion rates, averages, totals
  - Xử lý missing values và outliers
- Xây dựng migration scripts:
  - Tạo các bảng cần thiết
  - Thêm/cập nhật columns khi cần
- Testing pipeline:
  - Chạy thử trên 1-2 khóa học nhỏ
  - Kiểm tra chất lượng dữ liệu: completeness, accuracy, consistency
  - Xử lý các edge cases: user không có data, course mới, data không đồng bộ

#### Deliverables:
- Script `fetch_mooc_h5p_data.py` hoàn chỉnh
- Hàm `aggregate_raw_data()` đã test
- Database đã được populate với dữ liệu mẫu
- Báo cáo chất lượng dữ liệu

---

### MỐC 4: Nâng cấp Mô hình - Phân tích và Bổ sung Features Hiệu quả
**Thời gian**: 26/02/2025 - 18/03/2025 (3 tuần)
> **Giai đoạn hiện tại**: Đang tập trung vào việc phân tích các data cần thiết để thêm vào training cho hiệu quả hơn

#### Mục tiêu:
- Phân tích sâu dữ liệu hiện có để phát hiện các patterns và relationships
- Thiết kế và implement các features nâng cao có ý nghĩa hơn
- Loại bỏ các features không hiệu quả (như đã làm với h5p_early features)

#### Nhiệm vụ chi tiết:

**Tuần 7 (26/02 - 04/03/2025)**:
- Phân tích thống kê trên dữ liệu `raw_data`:
  - Correlation analysis: Tìm mối quan hệ giữa các features
  - Feature importance analysis: Xác định features nào quan trọng nhất
  - Missing data analysis: Xử lý missing values
  - Outlier detection: Phát hiện và xử lý outliers
- Phân tích các features không hiệu quả:
  - Xác định các features có variance thấp hoặc correlation cao với features khác
  - Quyết định loại bỏ các features không cần thiết (ví dụ: h5p_early features đã xóa)
- EDA (Exploratory Data Analysis):
  - Phân tích phân phối của các features
  - Phân tích mối quan hệ giữa features và target (is_dropout)

**Tuần 8 (05/03 - 11/03/2025)**:
- Thiết kế các features nâng cao mới:
  - **Activity-based features**:
    - `activity_consistency`: Độ nhất quán hoạt động (dựa trên engagement và recency)
    - `max_inactive_gap_days`: Khoảng thời gian không hoạt động dài nhất
    - `late_night_ratio`: Tỷ lệ hoạt động vào đêm khuya
    - `weekend_ratio`: Tỷ lệ hoạt động cuối tuần
  - **Progress-based features**:
    - `progress_velocity`: Tốc độ tiến độ (% completion per week)
    - `progress_acceleration`: Gia tốc tiến độ
    - `weeks_to_complete_estimate`: Ước tính số tuần còn lại để hoàn thành
    - `enrollment_phase`: Giai đoạn enrollment (very_early, early, mid, late, very_late)
  - **Interaction-based features**:
    - `discussion_engagement_rate`: Tỷ lệ tương tác thảo luận
    - `interaction_score`: Điểm tổng hợp về tương tác
    - `has_no_discussion`: Binary feature - có tương tác thảo luận hay không
  - **Performance-based features** (tránh data leakage):
    - `relative_completion`: Tiến độ so với trung bình lớp
    - `is_struggling`: Binary - có dấu hiệu đang gặp khó khăn không
    - `completion_consistency`: Độ nhất quán completion giữa các loại content

**Tuần 9 (12/03 - 18/03/2025)**:
- Implement các features mới trong `feature_engineering.py`:
  - `create_engagement_score()`: Tạo engagement score tổng hợp
  - `create_activity_features()`: Tạo activity-based features
  - `create_performance_features()`: Tạo performance features (không dùng grade để tránh leakage)
  - `create_interaction_features()`: Tạo interaction features
  - `create_time_features()`: Tạo time-based features
- Xây dựng script đánh giá feature importance:
  - Sử dụng XGBoost feature importance
  - Sử dụng permutation importance
  - So sánh feature importance giữa mô hình cũ và mới
- Testing và validation:
  - Đảm bảo không có data leakage (không dùng future information)
  - Kiểm tra tính hợp lý của các features mới
  - So sánh performance của model với features cũ vs features mới

#### Deliverables:
- Báo cáo phân tích dữ liệu (EDA report)
- Danh sách features mới và mô tả
- Module `feature_engineering.py` đã được nâng cấp
- Feature importance analysis report

---

### MỐC 5: Huấn luyện, Tối ưu và So sánh Mô hình
**Thời gian**: 19/03/2025 - 01/04/2025 (2 tuần)

#### Mục tiêu:
- Huấn luyện mô hình với bộ features đã được nâng cấp
- Tối ưu hyperparameters và so sánh các mô hình khác nhau
- Chọn mô hình tốt nhất để đưa vào production

#### Nhiệm vụ chi tiết:

**Tuần 10 (19/03 - 25/03/2025)**:
- Thiết lập pipeline training:
  - Implement `train_model.py` với train/val/test split
  - Implement `kfold_evaluation.py` cho cross-validation
  - Thiết lập early stopping và model checkpointing
- Huấn luyện baseline model:
  - Model với features cơ bản (trước khi nâng cấp)
  - Ghi nhận metrics: AUC, F1, Precision, Recall
- Huấn luyện improved model:
  - Model với features mới đã được thiết kế
  - So sánh performance với baseline

**Tuần 11 (26/03 - 01/04/2025)**:
- Hyperparameter tuning:
  - Grid search hoặc random search cho các hyperparameters:
    - `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`
    - `min_child_weight`, `gamma`, `reg_alpha`, `reg_lambda`
  - Class weight tuning để xử lý class imbalance
- So sánh các mô hình:
  - XGBoost vs Random Forest vs Gradient Boosting
  - So sánh metrics trên validation và test set
- Feature importance analysis:
  - Xác định top 20 features quan trọng nhất
  - Phân tích ý nghĩa của các features này
- Chọn mô hình cuối cùng:
  - Dựa trên performance metrics
  - Dựa trên tính giải thích được (interpretability)
  - Lưu model artifact để sử dụng trong production

#### Deliverables:
- Trained model files (.pkl hoặc .json)
- Model evaluation report với metrics chi tiết
- Feature importance visualization
- Hyperparameter tuning results
- So sánh performance giữa các mô hình

---

### MỐC 6: Tích hợp Mô hình vào Hệ thống MOOC
**Thời gian**: 02/04/2025 - 15/04/2025 (2 tuần)
> **Yêu cầu**: Tích hợp vào hệ thống MOOC ngay khi làm xong

#### Mục tiêu:
- Đưa mô hình vào hệ thống thực tế, cho phép chạy dự đoán trực tiếp trên dữ liệu MOOC
- Xây dựng API backend để frontend có thể gọi và hiển thị kết quả

#### Nhiệm vụ chi tiết:

**Tuần 12 (02/04 - 08/04/2025)**:
- Xây dựng/hoàn thiện backend API (`backend/app.py`):
  - Endpoint `/api/predict`: Trigger prediction cho một course
  - Endpoint `/api/predictions/{course_id}`: Lấy danh sách predictions cho course
  - Endpoint `/api/students/{course_id}`: Lấy danh sách sinh viên với risk scores
  - Endpoint `/api/student/{user_id}/{course_id}`: Lấy chi tiết một sinh viên
  - Endpoint `/api/stats/{course_id}`: Lấy thống kê tổng quan
- Xây dựng script `daily_prediction.py`:
  - Chạy tự động hàng ngày (cron job hoặc scheduled task)
  - Lấy dữ liệu mới nhất từ APIs
  - Chạy feature engineering
  - Áp dụng mô hình và cập nhật predictions vào database
  - Gửi cảnh báo nếu phát hiện sinh viên có rủi ro cao

**Tuần 13 (09/04 - 15/04/2025)**:
- Kết nối với database:
  - Connection pooling để tối ưu performance
  - Retry logic khi có lỗi kết nối
  - Transaction management để đảm bảo data consistency
- Testing end-to-end:
  - Test pipeline: APIs → Database → Feature Engineering → Model → Predictions
  - Test với dữ liệu thực tế từ MOOC
  - Kiểm tra performance: thời gian chạy, memory usage
  - Xử lý edge cases: course mới, user mới, data thiếu
- Integration testing:
  - Test API endpoints với Postman hoặc curl
  - Test với frontend dashboard (nếu đã có)
  - Đảm bảo data flow hoạt động đúng

#### Deliverables:
- Backend API hoàn chỉnh với các endpoints
- Script `daily_prediction.py` đã test
- Integration test results
- API documentation

---

### MỐC 7: Liên kết Chức năng Nâng cao và Hoàn thiện Hệ thống
**Thời gian**: 16/04/2025 - 29/04/2025 (2 tuần)
> **Yêu cầu**: Liên kết một số chức năng nâng cao

#### Mục tiêu:
- Tăng tính hữu ích cho giảng viên/người quản trị thông qua các chức năng nâng cao
- Hoàn thiện hệ thống và chuẩn bị cho việc bảo vệ luận văn

#### Nhiệm vụ chi tiết:

**Tuần 14 (16/04 - 22/04/2025)**:
- Tích hợp frontend dashboard (`frontend/src/pages/Dashboard.tsx`):
  - Hiển thị danh sách sinh viên theo mức độ rủi ro (High/Medium/Low)
  - Filters: theo course, khoa, lớp, enrollment status
  - Sorting: theo risk score, progress, last activity
- Các chức năng nâng cao:
  - **Student Profile Page**:
    - Timeline hoạt động: video views, H5P attempts, discussion posts theo thời gian
    - Biểu đồ tiến độ: progress over time
    - So sánh với trung bình lớp: radar chart
  - **Early Warning System**:
    - Cảnh báo real-time khi phát hiện sinh viên có rủi ro cao
    - Gợi ý hành động: gửi email nhắc nhở, can thiệp sớm
  - **Analytics Dashboard**:
    - Phân phối risk scores trong lớp
    - Trend analysis: xu hướng dropout theo thời gian
    - So sánh giữa các lớp/courses
  - **Export & Reporting**:
    - Export danh sách sinh viên có rủi ro ra Excel/CSV
    - Generate báo cáo PDF cho giảng viên

**Tuần 15 (23/04 - 29/04/2025)**:
- Testing toàn diện:
  - Unit tests cho các modules chính
  - Integration tests cho toàn bộ pipeline
  - User acceptance testing với giảng viên (nếu có thể)
  - Performance testing: load testing, stress testing
- Tối ưu hệ thống:
  - Tối ưu database queries (indexes, query optimization)
  - Caching cho các predictions thường xuyên được truy vấn
  - Tối ưu frontend: lazy loading, pagination
- Hoàn thiện tài liệu:
  - User manual cho giảng viên
  - Technical documentation cho developers
  - API documentation
  - Deployment guide
- Chuẩn bị bảo vệ:
  - Slide presentation
  - Demo video (nếu cần)
  - Q&A preparation

#### Deliverables:
- Frontend dashboard hoàn chỉnh với các chức năng nâng cao
- User manual và technical documentation
- Test reports
- Presentation slides
- Demo video (optional)

---

## 5.3. Biểu đồ Gantt Timeline

```
Mốc 1: Khảo sát & Phân tích
|████████████████| 15/01 - 28/01

Mốc 2: Thiết kế Kiến trúc
        |████████████████| 29/01 - 11/02

Mốc 3: Pipeline Thu thập Dữ liệu
                |████████████████| 12/02 - 25/02

Mốc 4: Nâng cấp Features
                        |████████████████████████| 26/02 - 18/03

Mốc 5: Training & Tối ưu Model
                                        |████████████████| 19/03 - 01/04

Mốc 6: Tích hợp vào MOOC
                                                |████████████████| 02/04 - 15/04

Mốc 7: Chức năng Nâng cao & Hoàn thiện
                                                        |████████████████| 16/04 - 29/04
```

---

## 5.4. Rủi ro và Giải pháp

### Rủi ro tiềm ẩn:

1. **Thiếu dữ liệu hoặc chất lượng dữ liệu kém**:
   - **Giải pháp**: Thu thập dữ liệu từ nhiều khóa học, xử lý missing values, sử dụng data augmentation nếu cần

2. **API không ổn định hoặc thay đổi**:
   - **Giải pháp**: Implement retry logic, caching, fallback mechanisms

3. **Model performance không đạt mục tiêu**:
   - **Giải pháp**: Thử nghiệm nhiều mô hình khác nhau, feature engineering sâu hơn, ensemble methods

4. **Thời gian tích hợp vào MOOC bị trễ**:
   - **Giải pháp**: Bắt đầu tích hợp sớm, làm song song với việc training model

5. **Chức năng nâng cao phức tạp hơn dự kiến**:
   - **Giải pháp**: Ưu tiên các chức năng core trước, chức năng nâng cao làm sau

---

## 5.5. Kết luận

Timeline trên được thiết kế để đảm bảo dự án hoàn thành đúng hạn (29/04/2025) với chất lượng cao. Mỗi mốc đều có deliverables cụ thể và có thể đánh giá được tiến độ. Việc chia nhỏ thành các mốc 2-3 tuần giúp dễ dàng theo dõi và điều chỉnh khi cần thiết.

**Điểm nhấn quan trọng**:
- **Mốc 4** (26/02 - 18/03): Tập trung vào phân tích và nâng cấp features - đây là giai đoạn quan trọng để cải thiện model performance
- **Mốc 6** (02/04 - 15/04): Tích hợp vào hệ thống MOOC - đảm bảo model có thể chạy trong môi trường thực tế
- **Mốc 7** (16/04 - 29/04): Liên kết các chức năng nâng cao - tăng giá trị thực tế của hệ thống

Với timeline này, dự án sẽ hoàn thành đầy đủ các yêu cầu: nâng cấp model hiệu quả, tích hợp vào MOOC, và có các chức năng nâng cao hữu ích cho người dùng.



