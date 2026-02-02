# 🚀 HƯỚNG DẪN FETCH MÔN HỌC MỚI - ĐƠN GIẢN

## ✅ Chỉ cần chạy 1 file: `fetch_mooc_h5p_data.py`

---

## 📝 CÁCH CHẠY:

### **Bước 1: Mở terminal**

```bash
cd d:\ProjectThesis\dropout_prediction\database
```

### **Bước 2: Chạy script**

```bash
python fetch_mooc_h5p_data.py --course-id "course-v1:DHQG-HCM+TENCOURSE+2025_S2"
```

**Thay `TENCOURSE` bằng mã môn học thực tế!**

---

## 🎯 VÍ DỤ CỤ THỂ:

### **Fetch môn học CS101:**

```bash
python fetch_mooc_h5p_data.py --course-id "course-v1:DHQG-HCM+CS101+2025_S2"
```

### **Fetch với sessionid (nếu cần authentication):**

```bash
python fetch_mooc_h5p_data.py --course-id "course-v1:DHQG-HCM+CS101+2025_S2" --sessionid "your_session_cookie"
```

### **Fetch nhưng giới hạn 100 sinh viên (để test):**

```bash
python fetch_mooc_h5p_data.py --course-id "course-v1:DHQG-HCM+CS101+2025_S2" --max-users 100
```

---

## 📊 Script sẽ làm gì?

1. ✅ **Fetch dữ liệu từ MOOC API:**
   - Danh sách sinh viên
   - Điểm số (grades)
   - Tiến độ (progress)
   - Hoạt động (activities)

2. ✅ **Fetch dữ liệu từ H5P API:**
   - H5P interactions
   - H5P scores
   - H5P completion

3. ✅ **Lưu vào database:**
   - `enrollments` - Thông tin sinh viên
   - `mooc_grades` - Điểm số
   - `mooc_video_interactions` - Video
   - `mooc_quiz_attempts` - Quiz
   - `h5p_*` tables - H5P data
   - `raw_data` - Aggregate tất cả (dùng cho prediction)

4. ✅ **Tự động aggregate:**
   - Tính toán features
   - Chuẩn bị data cho model

---

## ⚙️ CÁC THAM SỐ:

| Tham số | Mô tả | Bắt buộc |
|---------|-------|----------|
| `--course-id` | Course ID cần fetch | ✅ Bắt buộc |
| `--sessionid` | Cookie session (nếu cần auth) | ❌ Optional |
| `--delay` | Delay giữa các requests (giây) | ❌ Default: 0.5 |
| `--max-users` | Giới hạn số sinh viên (để test) | ❌ Optional |
| `--no-aggregate` | Không aggregate vào raw_data | ❌ Optional |
| `--aggregate-only` | Chỉ aggregate (không fetch mới) | ❌ Optional |

---

## 🔍 KIỂM TRA SAU KHI FETCH:

### **1. Kiểm tra database:**

```bash
cd d:\ProjectThesis\dropout_prediction
python check_courses.py
```

**Expected:**
```
Tổng số môn học: 2

1. course-v1:DHQG-HCM+FM101+2025_S2
   - Tổng SV: 921

2. course-v1:DHQG-HCM+CS101+2025_S2  ← MỚI!
   - Tổng SV: 450
```

### **2. Kiểm tra API:**

```bash
curl http://localhost:5000/api/courses
```

### **3. Kiểm tra Frontend:**

1. Mở dashboard: `http://localhost:5173`
2. Refresh: `Ctrl + Shift + R`
3. Click dropdown "Chọn khóa học"
4. ✅ Môn học mới xuất hiện!

---

## 📋 LOGS:

Script tạo log file tại:
```
d:\ProjectThesis\dropout_prediction\logs\fetch_data_YYYYMMDD_HHMMSS.log
```

Nếu có lỗi, check log file này!

---

## ⏱️ THỜI GIAN:

- **~100 sinh viên:** ~1-2 phút
- **~500 sinh viên:** ~5-10 phút
- **~1000 sinh viên:** ~15-20 phút

*Tùy thuộc vào tốc độ API và số lượng data*

---

## 🔧 TROUBLESHOOTING:

### ❌ **Lỗi: "Connection refused"**

**Giải pháp:**
```bash
# Kiểm tra database đang chạy
cd d:\ProjectThesis\dropout_prediction\database
docker-compose ps

# Nếu không chạy, start lại
docker-compose up -d
```

### ❌ **Lỗi: "401 Unauthorized"**

**Giải pháp:** Cần sessionid

1. Đăng nhập vào MOOC: https://mooc.vnuhcm.edu.vn
2. Mở DevTools (F12) → Application → Cookies
3. Copy giá trị của `sessionid`
4. Chạy lại với `--sessionid`:
   ```bash
   python fetch_mooc_h5p_data.py --course-id "..." --sessionid "abc123..."
   ```

### ❌ **Lỗi: "Course not found"**

**Giải pháp:** Course ID sai hoặc không tồn tại

- Kiểm tra lại course ID
- Format đúng: `course-v1:ORG+COURSE+RUN`

---

## 🎯 QUICK COMMAND:

**Fetch môn học mới (cách nhanh nhất):**

```bash
cd d:\ProjectThesis\dropout_prediction\database
python fetch_mooc_h5p_data.py --course-id "course-v1:DHQG-HCM+NEWCOURSE+2025_S2"
```

**Nếu được hỏi sessionid, nhấn Enter để bỏ qua (nếu không cần auth)**

---

## ✅ DONE!

Sau khi chạy xong:
1. ✅ Database có data mới
2. ✅ Backend API trả về course mới
3. ✅ Frontend hiển thị course mới trong dropdown

**Refresh browser và enjoy!** 🎉
