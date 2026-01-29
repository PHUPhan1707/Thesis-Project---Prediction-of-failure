# 🐛 Hướng Dẫn Debug Frontend Trắng Màn Hình

## 🔍 Các Bước Kiểm Tra

### 1. Kiểm Tra Backend Có Chạy Không

```bash
# Chạy script test
python test_backend.py

# Hoặc kiểm tra thủ công
curl http://localhost:5000/api/health
```

**Kết quả mong đợi:**
```json
{
  "service": "Teacher Dashboard API",
  "status": "ok",
  "timestamp": "..."
}
```

### 2. Kiểm Tra Console Browser

Mở **Developer Tools** (F12) và kiểm tra:
- **Console tab**: Xem có lỗi JavaScript không
- **Network tab**: Xem API calls có thành công không

**Lỗi thường gặp:**
- `ECONNREFUSED`: Backend không chạy
- `CORS error`: CORS chưa được cấu hình
- `404`: API endpoint không đúng
- `500`: Lỗi server

### 3. Kiểm Tra API URL

Kiểm tra file `.env` trong `frontend/`:

```env
VITE_API_URL=http://localhost:5000
```

**Lưu ý:** Sau khi sửa `.env`, cần **restart** frontend dev server.

### 4. Kiểm Tra Data Format

Backend trả về data có thể có vấn đề:
- Số là string thay vì number
- Null/undefined values
- Missing fields

**Đã sửa:** Backend đã có function `normalize_dict_numbers()` để convert đúng format.

### 5. Kiểm Tra Error Boundary

Frontend đã có `ErrorBoundary` component để catch lỗi React.

Nếu có lỗi, sẽ hiển thị:
- Thông báo lỗi
- Chi tiết lỗi (trong development mode)
- Nút "Tải lại trang"

---

## 🔧 Các Lỗi Thường Gặp & Cách Sửa

### ❌ Lỗi: "Không thể kết nối đến backend API"

**Nguyên nhân:**
- Backend không chạy
- Port sai (không phải 5000)
- Firewall chặn

**Cách sửa:**
```bash
# Chạy backend
cd backend
python app.py
```

### ❌ Lỗi: "CORS policy"

**Nguyên nhân:**
- CORS chưa được enable trong backend

**Cách sửa:**
Backend đã có `CORS(app)` trong `app.py`. Nếu vẫn lỗi, kiểm tra:
```python
from flask_cors import CORS
CORS(app)  # Phải có dòng này
```

### ❌ Lỗi: "Cannot read property 'toFixed' of undefined"

**Nguyên nhân:**
- Data từ API thiếu field hoặc là null/undefined

**Cách sửa:**
- Backend đã normalize numbers
- Frontend đã có optional chaining (`?.`)

### ❌ Lỗi: Trắng màn hình không có thông báo

**Nguyên nhân:**
- Lỗi JavaScript không được catch
- Component render fail

**Cách sửa:**
1. Mở Console (F12)
2. Xem lỗi cụ thể
3. Kiểm tra ErrorBoundary có catch được không

---

## 🧪 Test Thủ Công

### Test 1: Health Check

```bash
curl http://localhost:5000/api/health
```

### Test 2: Courses API

```bash
curl http://localhost:5000/api/courses
```

### Test 3: Statistics API

```bash
curl http://localhost:5000/api/statistics/course-v1:DHQG-HCM+FM101+2025_S2
```

### Test 4: Students API

```bash
curl http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2
```

---

## 📋 Checklist Debug

- [ ] Backend đang chạy (port 5000)
- [ ] Frontend đang chạy (port 5173 hoặc khác)
- [ ] `.env` file có `VITE_API_URL` đúng
- [ ] Console không có lỗi JavaScript
- [ ] Network tab thấy API calls thành công (200)
- [ ] CORS headers có trong response
- [ ] Data format đúng (numbers là numbers, không phải strings)

---

## 🚀 Khởi Động Lại

Nếu vẫn lỗi, thử khởi động lại:

```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Sau đó:
1. Mở browser: http://localhost:5173
2. Mở Developer Tools (F12)
3. Xem Console và Network tabs
4. Báo cáo lỗi cụ thể

---

## 📞 Thông Tin Debug

Khi báo lỗi, cung cấp:
1. **Console errors** (copy/paste)
2. **Network requests** (screenshot hoặc copy response)
3. **Backend logs** (từ terminal chạy backend)
4. **Browser** (Chrome, Firefox, Edge?)
5. **OS** (Windows, Mac, Linux?)

