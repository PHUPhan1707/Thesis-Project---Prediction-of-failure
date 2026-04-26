# 🐛 Hướng dẫn Debug "Chưa có dữ liệu H5P"

## ✅ Đã xác nhận:

1. **Database CÓ dữ liệu H5P** ✅
   - Course 1: `course-v1:DHQG-HCM+FM101+2025_S2` (121,542 records)
   - Course 2: `course-v1:UEL+NLTT241225+2025_12` (132 records)

2. **Backend đang chạy** ✅  
   - Port 5000 đang listen

3. **Frontend đã thêm console.log** ✅
   - Component và API service có log

## 🔍 Bước Debug tiếp theo:

### 1. Kiểm tra Browser Console

1. **Mở DevTools**: `F12` hoặc `Ctrl+Shift+I`
2. **Vào tab Console**
3. **Xem logs**:
   ```
   [H5P] Loading H5P data for course: ...
   [API] Calling H5P API: {...}
   ```

4. **Tìm xem**:
   - Course ID nào đang được gọi?
   - Có khớp với `course-v1:DHQG-HCM+FM101+2025_S2` không?

---

### 2. So sánh Course ID

**Course ID trong database**:
- `course-v1:DHQG-HCM+FM101+2025_S2`
- `course-v1:UEL+NLTT241225+2025_12`

**Course ID Frontend đang dùng**: (xem trong console)
- Nếu KHÁC → Đây là vấn đề!

---

### 3. Nếu Course ID khác nhau:

**Giải pháp 1**: Chọn đúng course
1. Trong dropdown course selector
2. Chọn course "FM101" hoặc "NLTT241225"

**Giải pháp 2**: Thêm dữ liệu H5P cho course hiện tại
1. Chạy script fetch H5P data cho course này
2. Xem file: `database/fetch_mooc_h5p_data.py`

---

### 4. Kiểm tra API Response

**Trong DevTools → Network tab**:
1. Refresh page
2. Tìm request: `h5p-analytics`
3. Click vào request
4. Xem **Response**:
   ```json
   {
     "success": true,
     "contents": []  // ← Nếu empty = không có dữ liệu
   }
   ```

---

### 5. Test API trực tiếp

**Test với course có dữ liệu**:

```bash
# Windows PowerShell (URL encoded)
curl "http://localhost:5000/api/h5p-analytics/course-v1%3ADHQG-HCM%2BFM101%2B2025_S2/low-performance?limit=5&min_students=3"
```

**Kết quả mong đợi**:
```json
{
  "success": true,
  "statistics": {...},
  "contents": [...]  // Có data
}
```

---

### 6. Kiểm tra Backend Log

Nếu có terminal chạy `python app.py`, xem output:
```
INFO - Loading H5P data for course: ...
```

Nếu có lỗi, sẽ hiển thị:
```
ERROR - Failed to ... : ...
```

---

### 7. Quick Fix: In ra Course ID

**Thêm vào component** (đã thêm rồi):
```tsx
console.log('[H5P] Loading H5P data for course:', selectedCourse);
```

**Check console → Sẽ thấy course ID**:
- Nếu khớp `course-v1:DHQG-HCM+FM101+2025_S2` → API có vấn đề
- Nếu khác → Chọn sai course

---

## 🎯 Các trường hợp thường gặp:

### Case 1: Course ID không khớp ❌
**Triệu chứng**: Console log show course ID khác với DB
**Giải pháp**: Chọn đúng course trong dropdown

### Case 2: API bị lỗi ❌
**Triệu chứng**: Network tab show 500 error
**Giải pháp**: Check backend logs, có thể database connection lỗi

### Case 3: Min students quá cao ❌
**Triệu chứng**: Response `contents: []` nhưng có dữ liệu trong DB
**Giải pháp**: Giảm `min_students` từ 3 xuống 1

### Case 4: Frontend cache ❌
**Triệu chứng**: Đã fix nhưng vẫn lỗi
**Giải pháp**: Hard refresh `Ctrl+Shift+R` hoặc clear cache

---

## 🔧 Quick Tests:

### Test 1: Check database có dữ liệu
```bash
cd d:/ProjectThesis/dropout_prediction
python check_h5p_debug.py
```

### Test 2: Check API endpoint
```bash
# Test với course FM101
curl "http://localhost:5000/api/h5p-analytics/course-v1%3ADHQG-HCM%2BFM101%2B2025_S2/low-performance?limit=5&min_students=1"
```

### Test 3: Check Frontend logs
1. Open browser
2. F12 → Console
3. Refresh page
4. Look for `[H5P]` and `[API]` logs

---

## 📝 Checklist Debug:

- [ ] Database có dữ liệu H5P? → **Yes** (121,674 records)
- [ ] Backend đang chạy? → **Yes** (port 5000)
- [ ] Course ID trong frontend = course ID trong DB?
  - [ ] Kiểm tra console log
  - [ ] Xem dropdown course selector
- [ ] API response có data?
  - [ ] Check Network tab
  - [ ] Test curl command
- [ ] Min students có quá cao không?
  - [ ] Thử giảm xuống 1
- [ ] Frontend đã refresh?
  - [ ] Hard refresh (Ctrl+Shift+R)

---

## ✅ Sau khi tìm ra vấn đề:

1. **Nếu chọn sai course**:
   - Chọn course "FM101" hoặc "NLTT241225"
   - Widget sẽ hiển thị data

2. **Nếu API lỗi**:
   - Check backend logs
   - Restart backend nếu cần

3. **Nếu muốn thêm dữ liệu cho course khác**:
   - Chạy `database/fetch_mooc_h5p_data.py`
   - Fetch H5P data cho course mới

---

## 📞 Next Steps:

Hãy:
1. **Mở browser DevTools (F12)**
2. **Vào tab Console**
3. **Refresh page và chọn course**
4. **Xem console logs**
5. **Cho tôi biết**:
   - Course ID nào đang được gọi?
   - API response là gì?

Sau đó tôi sẽ giúp bạn fix!

---

**TL;DR**: Rất có thể bạn đang chọn course KHÔNG CÓ dữ liệu H5P. Hãy chọn course "FM101" thử xem!
