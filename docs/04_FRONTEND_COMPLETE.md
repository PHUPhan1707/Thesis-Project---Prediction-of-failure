# 🎨 FRONTEND - TÀI LIỆU TỔNG HỢP

## 📋 Mục Lục

1. [Setup & Installation](#setup--installation)
2. [Project Structure](#project-structure)
3. [Components](#components)
4. [Pages](#pages)
5. [API Integration](#api-integration)
6. [Deployment](#deployment)

---

## ⚙️ SETUP & INSTALLATION

### Prerequisites
- Node.js 18+
- npm hoặc yarn

### Installation

```bash
cd frontend
npm install
```

### Environment Configuration

Tạo file `.env`:
```env
VITE_API_URL=http://localhost:5000
```

### Run Development Server

```bash
npm run dev
```

**URL:** `http://localhost:5173`

### Build for Production

```bash
npm run build
```

**Output:** `frontend/dist/`

---

## 📁 PROJECT STRUCTURE

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── DashboardLayout.tsx    # Main layout
│   │   │   ├── Sidebar.tsx              # Navigation sidebar
│   │   │   └── Header.tsx               # Top header
│   │   ├── RiskBadge.tsx                # Risk level badge
│   │   └── StatsCard.tsx                # Statistics card
│   ├── context/
│   │   └── DashboardContext.tsx         # Global state (selected course)
│   ├── pages/
│   │   ├── Dashboard.tsx                # Overview page
│   │   ├── StudentList.tsx              # Student list page
│   │   └── StudentDetail.tsx            # Student detail page
│   ├── services/
│   │   └── api.ts                       # API service layer
│   ├── types/
│   │   └── index.ts                     # TypeScript types
│   ├── App.tsx                          # Main app component
│   └── main.tsx                         # Entry point
├── package.json
└── vite.config.ts
```

---

## 🧩 COMPONENTS

### 1. DashboardLayout
**File:** `src/components/Layout/DashboardLayout.tsx`

**Props:** `children`

**Features:**
- Responsive layout
- Sidebar navigation
- Header với course selector

### 2. Sidebar
**File:** `src/components/Layout/Sidebar.tsx`

**Features:**
- Navigation menu
- Course selection
- Active route highlighting

### 3. RiskBadge
**File:** `src/components/RiskBadge.tsx`

**Props:**
- `level`: 'HIGH' | 'MEDIUM' | 'LOW'
- `score`: number
- `size?`: 'small' | 'medium' | 'large'
- `showScore?`: boolean

**Features:**
- Color-coded badges
- Risk score display

### 4. StatsCard
**File:** `src/components/StatsCard.tsx`

**Props:**
- `icon`: Lucide icon component
- `title`: string
- `value`: number | string
- `description?`: string
- `color?`: 'primary' | 'success' | 'warning' | 'danger'

**Features:**
- Icon + value display
- Color themes

---

## 📄 PAGES

### 1. Dashboard
**File:** `src/pages/Dashboard.tsx`
**Route:** `/`

**Features:**
- Statistics overview (total students, avg grade, etc.)
- Risk distribution pie chart
- Top 5 high-risk students
- Additional stats (inactive students, failing students)

**API Calls:**
- `getCourseStatistics(courseId)`
- `getStudents(courseId, {risk_level: 'HIGH'})`

### 2. Student List
**File:** `src/pages/StudentList.tsx`
**Route:** `/students`

**Features:**
- Filterable list (by risk level)
- Sortable (by risk score, name, grade, last activity)
- Search (by name or email)
- Export to CSV
- Click to view detail

**API Calls:**
- `getStudents(courseId, filters)`

### 3. Student Detail
**File:** `src/pages/StudentDetail.tsx`
**Route:** `/student/:userId/:courseId`

**Features:**
- Student profile
- Key metrics (grade, completion, quiz score, etc.)
- Intervention suggestions
- Quick actions (email, call, schedule)

**API Calls:**
- `getStudentDetail(userId, courseId)`

---

## 🔌 API INTEGRATION

### API Service Layer
**File:** `src/services/api.ts`

### Functions

#### 1. Health Check
```typescript
healthCheck(): Promise<any>
```

#### 2. Get Courses
```typescript
getCourses(): Promise<Course[]>
```

#### 3. Get Students
```typescript
getStudents(
  courseId: string,
  filters?: StudentFilters
): Promise<Student[]>
```

#### 4. Get Student Detail
```typescript
getStudentDetail(
  userId: number,
  courseId: string
): Promise<StudentDetail>
```

#### 5. Get Course Statistics
```typescript
getCourseStatistics(
  courseId: string
): Promise<CourseStatistics>
```

#### 6. Record Intervention
```typescript
recordIntervention(
  intervention: InterventionAction
): Promise<InterventionResponse>
```

#### 7. Export Students to CSV
```typescript
exportStudentsToCSV(
  students: Student[],
  filename?: string
): void
```

### Error Handling

- Request interceptor: Logging
- Response interceptor: Error logging
- Try-catch trong components

---

## 🎨 STYLING

### CSS Files

- `src/index.css` - Global styles
- `src/App.css` - App-level styles
- Component-specific CSS files

### Color Scheme

- **Primary:** Blue (#3b82f6)
- **Success:** Green (#10b981)
- **Warning:** Orange (#f59e0b)
- **Danger:** Red (#ef4444)

### Responsive Design

- Mobile-first approach
- Breakpoints: sm, md, lg, xl
- Flexbox & Grid layouts

---

## 📦 DEPENDENCIES

### Production

- `react` ^19.2.0
- `react-dom` ^19.2.0
- `react-router-dom` ^7.12.0
- `axios` ^1.13.2
- `recharts` ^3.7.0
- `lucide-react` ^0.562.0

### Development

- `typescript` ~5.9.3
- `vite` ^7.2.4
- `@vitejs/plugin-react` ^5.1.1
- `eslint` ^9.39.1

---

## 🚀 DEPLOYMENT

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Deploy to Static Hosting

1. Build: `npm run build`
2. Upload `dist/` folder to hosting
3. Configure API URL in environment variables

### Environment Variables

**Development:**
```env
VITE_API_URL=http://localhost:5000
```

**Production:**
```env
VITE_API_URL=https://api.yourdomain.com
```

---

## 🧪 TESTING

### Manual Testing Checklist

- [ ] Dashboard loads statistics
- [ ] Student list displays students
- [ ] Filters work (risk level, sort)
- [ ] Search works
- [ ] Student detail shows all info
- [ ] Export CSV works
- [ ] Navigation works
- [ ] Responsive on mobile

### Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

---

## 🐛 TROUBLESHOOTING

### Lỗi: "Network Error"

**Nguyên nhân:** Backend không chạy hoặc URL sai

**Giải pháp:**
1. Kiểm tra backend: `curl http://localhost:5000/api/health`
2. Kiểm tra `.env`: `VITE_API_URL=http://localhost:5000`
3. Restart frontend: `npm run dev`

### Lỗi: "Module not found"

**Giải pháp:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### Lỗi: "CORS policy blocked"

**Nguyên nhân:** Backend chưa enable CORS

**Giải pháp:** Kiểm tra `backend/app.py` có `CORS(app)`

---

## 📚 Tài Liệu Liên Quan

- **Backend API:** `backend/app.py`
- **Connection Guide:** `FRONTEND_BACKEND_CONNECTION_GUIDE.md`
- **Quick Start:** `QUICK_START.md`
- **Types:** `frontend/src/types/index.ts`
- **API Service:** `frontend/src/services/api.ts`

