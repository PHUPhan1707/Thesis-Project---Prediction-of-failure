# 📊 Tài Liệu Xuất Báo Cáo và Các API Sử Dụng

## 📁 Các File Code Liên Quan Đến Xuất Báo Cáo

### 1. File Chính - Export Utilities

#### `src/dashboard/utils/studentReportExport.js`
**Chức năng:** Xuất báo cáo học tập của sinh viên ra file PDF
- `generateStudentReportPDF()`: Tạo PDF cho một sinh viên
- `exportMultipleStudentReportsToZip()`: Xuất nhiều PDF vào file ZIP
- `downloadZipFile()`: Tải file ZIP về máy

**Công nghệ sử dụng:**
- `html2canvas`: Chuyển HTML thành hình ảnh
- `jsPDF`: Tạo file PDF
- `JSZip`: Tạo file ZIP

---

#### `src/dashboard/components/CourseExportModal/CourseExportModal.jsx`
**Chức năng:** Modal để cấu hình và xuất báo cáo khóa học
- Cho phép chọn loại báo cáo (enrollments, grades, progress, discussions, comprehensive, h5p-video)
- Cấu hình filter (email domain, sort by, sort order)
- Chọn các trường dữ liệu cần xuất
- Preview dữ liệu trước khi xuất
- Xuất ra Excel hoặc in

---

#### `src/dashboard/Dashboard.jsx`
**Chức năng:** Component chính quản lý xuất báo cáo
- Hàm `handleExport()`: Xử lý logic xuất báo cáo
- Gọi các API để lấy dữ liệu
- Xử lý preview và export

**Các loại export được hỗ trợ:**
1. `export-enrollments`: Danh sách đăng ký
2. `export-comprehensive`: Báo cáo toàn diện (MOOC + H5P)
3. `export-grades`: Bảng điểm
4. `export-progress`: Tiến độ học tập
5. `export-discussions`: Tương tác thảo luận
6. `export-h5p-video-interaction`: Tương tác H5P và Video

---

#### `src/dashboard/data/api.js`
**Chức năng:** Định nghĩa các hàm gọi API
- `fetchStudentEnrollments()`: Lấy danh sách đăng ký
- `fetchStudentGrades()`: Lấy bảng điểm
- `fetchStudentProgress()`: Lấy tiến độ học tập
- `fetchStudentDiscussions()`: Lấy tương tác thảo luận
- `fetchCompleteStudentData()`: Lấy dữ liệu toàn diện
- `fetchH5PVideoInteraction()`: Lấy dữ liệu H5P và Video

---

#### `src/dashboard/data/utils.js`
**Chức năng:** Xử lý chuyển đổi dữ liệu API thành Excel
- `exportToExcel()`: Chuyển đổi dữ liệu API thành file Excel

---

## 🔌 Các API Được Sử Dụng

### Base URL
- **MOOC API:** `{LMS_BASE_URL}/api/custom/v1/`
- **H5P API:** `https://h5p.itp.vn/wp-json/mooc/v1`

---

## 📡 1. API Xuất Danh Sách Đăng Ký (Student Enrollments)

### Endpoint
```
GET /api/custom/v1/export/student-enrollments/{course_id}/
```

### Query Parameters
| Parameter | Type | Required | Mô tả |
|-----------|------|----------|-------|
| `email_filter` | string | No | Lọc theo email (ví dụ: uel, gmail) |
| `enrollment_mode` | string | No | Lọc theo mode (audit, verified, honor, professional) |
| `is_active` | boolean | No | Lọc theo trạng thái active |
| `sort_by` | string | No | Sắp xếp theo (enrollment_date, username, email) - mặc định: enrollment_date |
| `sort_order` | string | No | Thứ tự sắp xếp (desc, asc) - mặc định: desc |

### Response Output
```json
{
  "enrollments": [
    {
      "user_id": 123,
      "username": "student001",
      "email": "student001@example.com",
      "full_name": "Nguyễn Văn A",
      "date_joined": "2024-01-01T00:00:00Z",
      "enrollment_date": "2024-01-10T08:00:00Z",
      "is_active": true,
      "enrollment_mode": "honor"
    }
  ],
  "total_count": 1250,
  "filtered_count": 1250
}
```

---

## 📡 2. API Xuất Bảng Điểm (Student Grades) ⭐ **API CUNG CẤP ĐẬU/RỚT**

### Endpoint
```
GET /api/custom/v1/export/student-grades/{course_id}/
```

**🎯 Đây là API chính cung cấp thông tin đậu/rớt của học viên MOOC**

### Query Parameters
| Parameter | Type | Required | Mô tả |
|-----------|------|----------|-------|
| `email_filter` | string | No | Lọc theo email |
| `sort_by` | string | No | Sắp xếp theo (grade_percentage, username) - mặc định: grade_percentage |
| `sort_order` | string | No | Thứ tự sắp xếp (desc, asc) - mặc định: desc |

### Response Output
```json
{
  "grade_data": {
    "grade_table": [
      {
        "user_id": 123,
        "username": "student001",
        "email": "student001@example.com",
        "full_name": "Nguyễn Văn A",
        "grade_percentage": 85.5,
        "letter_grade": "B",
        "is_passed": true  // ⭐ true = Đậu, false = Rớt
      }
    ]
  },
  "summary": {
    "total_students": 1250,
    "avg_grade": 75.5,
    "pass_rate": 80.0  // ⭐ Tỉ lệ đậu (%)
  }
}
```

### Các Trường Liên Quan Đến Đậu/Rớt:
- **`is_passed`** (boolean): `true` = Đậu, `false` = Rớt
- **`letter_grade`** (string): Xếp loại (A, B, C, D, F)
- **`grade_percentage`** (number): Điểm phần trăm (0-100)
- **`pass_rate`** (number trong summary): Tỉ lệ đậu của lớp (%)

---

## 📡 3. API Xuất Tiến Độ Học Tập (Student Progress)

### Endpoint
```
GET /api/custom/v1/export/student-progress/{course_id}/
```

### Query Parameters
| Parameter | Type | Required | Mô tả |
|-----------|------|----------|-------|
| `email_filter` | string | No | Lọc theo email |
| `sort_by` | string | No | Sắp xếp theo (completion_rate, username) - mặc định: completion_rate |
| `sort_order` | string | No | Thứ tự sắp xếp (desc, asc) - mặc định: desc |

### Response Output
```json
{
  "students_progress_data": {
    "students_progress": [
      {
        "user_id": 123,
        "username": "student001",
        "email": "student001@example.com",
        "full_name": "Nguyễn Văn A",
        "current_chapter": "Chương 3",
        "current_section": "Section 2",
        "current_unit": "Unit 5",
        "completion_rate": 75.5,
        "last_activity": "2024-10-04T15:30:00Z"
      }
    ]
  },
  "summary": {
    "total_students": 1250,
    "avg_completion_rate": 65.5
  }
}
```

---

## 📡 4. API Xuất Tương Tác Thảo Luận (Student Discussions)

### Endpoint
```
GET /api/custom/v1/export/student-discussions/{course_id}/
```

### Query Parameters
| Parameter | Type | Required | Mô tả |
|-----------|------|----------|-------|
| `email_filter` | string | No | Lọc theo email |
| `sort_by` | string | No | Sắp xếp theo (total_interactions, threads_count, comments_count) - mặc định: total_interactions |
| `sort_order` | string | No | Thứ tự sắp xếp (desc, asc) - mặc định: desc |

### Response Output
```json
{
  "students": [
    {
      "user_id": 123,
      "username": "student001",
      "email": "student001@example.com",
      "full_name": "Nguyễn Văn A",
      "threads_count": 5,
      "comments_count": 15,
      "total_interactions": 20,
      "questions_count": 3,
      "total_upvotes": 12
    }
  ],
  "summary": {
    "total_students": 1250,
    "total_threads": 500,
    "total_comments": 2000
  }
}
```

---

## 📡 5. API Xuất Báo Cáo Toàn Diện (Complete Student Data) ⭐ **CŨNG CUNG CẤP ĐẬU/RỚT**

### Endpoint
```
GET /api/custom/v1/export/complete-student-data/{course_id}/
```

**🎯 API này cũng cung cấp thông tin đậu/rớt cùng với các dữ liệu khác (tiến độ, thảo luận)**

### Query Parameters
| Parameter | Type | Required | Mô tả |
|-----------|------|----------|-------|
| `email_filter` | string | No | Lọc theo email |
| `sort_by` | string | No | Sắp xếp theo (overall_engagement_score, grade_percentage, completion_rate) - mặc định: overall_engagement_score |
| `sort_order` | string | No | Thứ tự sắp xếp (desc, asc) - mặc định: desc |

### Response Output
```json
{
  "students": [
    {
      "user_id": 123,
      "username": "student001",
      "email": "student001@example.com",
      "full_name": "Nguyễn Văn A",
      "grade_percentage": 85.5,
      "letter_grade": "B",
      "is_passed": true,  // ⭐ true = Đậu, false = Rớt
      "current_chapter": "Chương 3",
      "current_section": "Section 2",
      "current_unit": "Unit 5",
      "completion_rate": 75.5,
      "last_activity": "2024-10-04T15:30:00Z",
      "threads_count": 5,
      "comments_count": 15,
      "total_discussion_interactions": 20,
      "overall_engagement_score": 80.5
    }
  ],
  "summary": {
    "total_students": 1250,
    "avg_grade": 75.5,
    "avg_completion_rate": 65.5,
    "avg_engagement_score": 70.0
  }
}
```

---

## 📡 6. API H5P Video Interaction (H5P & Video Data)

### Endpoint
```
GET https://h5p.itp.vn/wp-json/mooc/v1/course-students/{course_id}
```

### Query Parameters
Không có query parameters

### Response Output
Dựa theo tài liệu H5P_MOOC-API-DOCUMENTATION.md, API này trả về dữ liệu tổng hợp về:
- Điểm số H5P (scores)
- Tiến độ xem video (video progress)
- Thống kê theo folder

**Ví dụ Response:**
```json
{
  "course_id": "course-v1:edX+DemoX+Demo_Course",
  "students": [
    {
      "user_id": "123",
      "username": "student001",
      "email": "student001@example.com",
      "full_name": "Nguyễn Văn A",
      "h5p_completed_items": 25,
      "h5p_total_items_attempted": 30,
      "h5p_total_items_in_course": 35,
      "h5p_completion_percent": 83.33,
      "h5p_course_completion_percent": 71.43,
      "h5p_total_videos": 20,
      "h5p_completed_videos": 18,
      "h5p_in_progress_videos": 2,
      "h5p_average_video_progress": 90.0,
      "h5p_total_watched_time": 3600,
      "h5p_total_contents": 35,
      "h5p_completed_contents": 25,
      "h5p_total_score": 850,
      "h5p_total_max_score_attempted": 1000,
      "h5p_course_max_score": 1200,
      "h5p_average_percentage": 85.0
    }
  ],
  "summary": {
    "total_students": 1250,
    "avg_completion": 75.5
  }
}
```

**Lưu ý:** API này có thể cần URL encode course_id nếu gặp lỗi 404:
- `:` → `%3A`
- `+` → `%2B`

---

## 📊 Tổng Hợp Các API Theo Loại Export

| Loại Export | API Endpoint | Output Format | Có Đậu/Rớt? |
|-------------|--------------|---------------|-------------|
| **Enrollments** | `/export/student-enrollments/{course_id}/` | `{ enrollments: [...], total_count: number }` | ❌ Không |
| **Grades** ⭐ | `/export/student-grades/{course_id}/` | `{ grade_data: { grade_table: [...] }, summary: {...} }` | ✅ **Có** |
| **Progress** | `/export/student-progress/{course_id}/` | `{ students_progress_data: { students_progress: [...] }, summary: {...} }` | ❌ Không |
| **Discussions** | `/export/student-discussions/{course_id}/` | `{ students: [...], summary: {...} }` | ❌ Không |
| **Comprehensive** ⭐ | `/export/complete-student-data/{course_id}/` | `{ students: [...], summary: {...} }` | ✅ **Có** |
| **H5P Video** | `https://h5p.itp.vn/wp-json/mooc/v1/course-students/{course_id}` | `{ students: [...], summary: {...} }` | ❌ Không |

**⭐ Lưu ý:** Chỉ có API **Grades** và **Comprehensive** cung cấp thông tin đậu/rớt (`is_passed`, `letter_grade`, `grade_percentage`)

---

## 🔄 Luồng Xử Lý Xuất Báo Cáo

```
1. User chọn khóa học và loại export
   ↓
2. Mở CourseExportModal
   ↓
3. User cấu hình:
   - Email filter
   - Sort by / Sort order
   - Chọn các trường dữ liệu
   ↓
4. Click "Preview" hoặc "Export"
   ↓
5. Gọi API tương ứng:
   - fetchStudentEnrollments()
   - fetchStudentGrades()
   - fetchStudentProgress()
   - fetchStudentDiscussions()
   - fetchCompleteStudentData()
   - fetchH5PVideoInteraction() (cho comprehensive và h5p-video)
   ↓
6. Xử lý dữ liệu:
   - Preview: Hiển thị bảng dữ liệu
   - Export: Chuyển đổi sang Excel bằng exportToExcel()
   ↓
7. Download file Excel về máy
```

---

## 📝 Các Trường Dữ Liệu Có Thể Xuất

### Enrollments Export
- STT, Mã HV, Tên đăng nhập, Email, Họ và tên
- Ngày tạo tài khoản, Ngày đăng ký
- Trạng thái, Loại đăng ký

### Grades Export ⭐ **CÓ ĐẬU/RỚT**
- STT, Mã HV, Tên đăng nhập, Email, Họ và tên
- **Điểm (%)** (`grade_percentage`)
- **Xếp loại** (`letter_grade`: A, B, C, D, F)
- **Kết quả** (`is_passed`: Đạt/Không đạt)

### Progress Export
- STT, Mã HV, Tên đăng nhập, Email, Họ và tên
- Chương hiện tại, Section hiện tại, Unit hiện tại
- Tỉ lệ hoàn thành (%), Hoạt động gần nhất

### Discussions Export
- STT, Mã HV, Tên đăng nhập, Email, Họ và tên
- Số chủ đề, Số bình luận, Tổng tương tác
- Số câu hỏi, Số upvote

### Comprehensive Export ⭐ **CÓ ĐẬU/RỚT**
- Tất cả các trường từ Grades + Progress + Discussions
- **Điểm (%)** (`grade_percentage`)
- **Xếp loại** (`letter_grade`)
- **Kết quả** (`is_passed`: Đạt/Không đạt)
- Điểm tổng hợp (overall_engagement_score)

### H5P Video Export
- STT, Mã HV, Tên đăng nhập, Email, Họ và tên
- Items hoàn thành, Items đã thử, Tổng items khóa học
- % hoàn thành (đã thử), % hoàn thành (tổng)
- Tổng video, Video hoàn thành, Video đang xem
- Tiến độ video trung bình (%), Thời gian xem (giây)
- Tổng contents, Contents hoàn thành
- Tổng điểm đạt, Điểm max (đã thử), Điểm max khóa học
- Tỉ lệ điểm tương tác video đạt được

---

## 🔐 Authentication

Tất cả các API MOOC yêu cầu authentication:
- Sử dụng session authentication (credentials: 'include')
- Hoặc Bearer token trong header Authorization

API H5P hiện tại là public access (không cần authentication).

---

## 📌 Lưu Ý Quan Trọng

1. **Course ID Format:** Course ID có thể chứa ký tự đặc biệt (`:`, `+`)
   - Nếu gặp lỗi 404, thử URL encode: `:` → `%3A`, `+` → `%2B`

2. **Error Handling:** Tất cả các API đều có xử lý lỗi:
   - 401: Authentication required
   - 403: Access forbidden
   - 404: API not found
   - 500: Internal server error

3. **Preview Mode:** Có thể preview dữ liệu trước khi export bằng cách truyền `previewOnly = true`

4. **Excel Export:** Sử dụng thư viện `xlsx` để tạo file Excel từ dữ liệu API

5. **PDF Export:** Sử dụng `jsPDF` và `html2canvas` để tạo PDF từ HTML

---

## 📚 Tài Liệu Tham Khảo

- **API List:** `C:\Users\Asus\Downloads\hướng dẫn về api mooc_h5p (1)\API_LIST.md`
- **Complete API List:** `C:\Users\Asus\Downloads\hướng dẫn về api mooc_h5p (1)\COMPLETE_API_LIST.md`
- **Advanced Statistics API:** `C:\Users\Asus\Downloads\hướng dẫn về api mooc_h5p (1)\ADVANCED_STATISTICS_API.md`
- **H5P MOOC API:** `C:\Users\Asus\Downloads\hướng dẫn về api mooc_h5p (1)\H5P_MOOC-API-DOCUMENTATION.md`

---

---

## 🎯 TÓM TẮT: API CUNG CẤP THÔNG TIN ĐẬU/RỚT MOOC

### ✅ Các API Cung Cấp Đậu/Rớt:

#### 1. **API Bảng Điểm (Grades)** - ⭐ **KHUYẾN NGHỊ**
```
GET /api/custom/v1/export/student-grades/{course_id}/
```
**Cung cấp:**
- `is_passed`: boolean (true = Đậu, false = Rớt)
- `letter_grade`: string (A, B, C, D, F)
- `grade_percentage`: number (0-100)
- `pass_rate`: Tỉ lệ đậu của lớp (trong summary)

**Ví dụ Response:**
```json
{
  "grade_data": {
    "grade_table": [
      {
        "user_id": 123,
        "username": "student001",
        "full_name": "Nguyễn Văn A",
        "grade_percentage": 85.5,
        "letter_grade": "B",
        "is_passed": true  // ✅ Đậu
      }
    ]
  },
  "summary": {
    "total_students": 1250,
    "avg_grade": 75.5,
    "pass_rate": 80.0  // 80% học viên đậu
  }
}
```

#### 2. **API Báo Cáo Toàn Diện (Comprehensive)**
```
GET /api/custom/v1/export/complete-student-data/{course_id}/
```
**Cung cấp:** Tất cả thông tin từ API Grades + thêm tiến độ và thảo luận

**Ví dụ Response:**
```json
{
  "students": [
    {
      "user_id": 123,
      "username": "student001",
      "full_name": "Nguyễn Văn A",
      "grade_percentage": 85.5,
      "letter_grade": "B",
      "is_passed": true,  // ✅ Đậu
      "completion_rate": 75.5,
      "threads_count": 5,
      "comments_count": 15,
      "overall_engagement_score": 80.5
    }
  ]
}
```

### ❌ Các API KHÔNG Cung Cấp Đậu/Rớt:
- `/export/student-enrollments/` - Chỉ có thông tin đăng ký
- `/export/student-progress/` - Chỉ có tiến độ học tập
- `/export/student-discussions/` - Chỉ có tương tác thảo luận
- H5P API (`/course-students/`) - Chỉ có dữ liệu H5P và video

### 💡 Cách Sử Dụng:

**Để lấy danh sách học viên đậu/rớt:**
```javascript
// Sử dụng API Grades
const response = await fetch(
  `/api/custom/v1/export/student-grades/${courseId}/?sort_by=grade_percentage&sort_order=desc`
);
const data = await response.json();

// Lọc học viên đậu
const passedStudents = data.grade_data.grade_table.filter(
  student => student.is_passed === true
);

// Lọc học viên rớt
const failedStudents = data.grade_data.grade_table.filter(
  student => student.is_passed === false
);

// Lấy tỉ lệ đậu
const passRate = data.summary.pass_rate; // %
```

---

**Tài liệu được tạo:** 2025-01-11
**Phiên bản:** 1.1
**Cập nhật:** Thêm thông tin về API cung cấp đậu/rớt

