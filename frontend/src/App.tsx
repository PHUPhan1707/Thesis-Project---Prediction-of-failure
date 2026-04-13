import ErrorBoundary from './components/ErrorBoundary'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { DashboardProvider } from './context/DashboardContext'
import { ThemeProvider } from './context/ThemeContext'
import DashboardLayout from './layout/DashboardLayout'
import PipelineLayout from './layout/PipelineLayout'
import Overview from './pages/Overview'
import Details from './pages/Details'
import StudentDetailPage from './pages/StudentDetailPage'
import H5PAnalytics from './pages/H5PAnalytics'
import SchedulerDashboard from './pages/SchedulerDashboard'
import PipelineMonitor from './pages/PipelineMonitor'
import ReportPage from './pages/ReportPage'

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <DashboardProvider>
          <BrowserRouter>
            <Routes>
              {/* Dashboard pages */}
              <Route element={<DashboardLayout />}>
                <Route path="/" element={<Overview />} />
                <Route path="/h5p-analytics" element={<H5PAnalytics />} />
                <Route path="/details" element={<Details />} />
                <Route path="/student/:userId" element={<StudentDetailPage />} />
                <Route path="/report" element={<ReportPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>

              {/* Pipeline — separate layout with course sidebar */}
              <Route path="/pipeline" element={<PipelineLayout />}>
                <Route index element={<PipelineMonitor />} />
                <Route path="scheduler" element={<SchedulerDashboard />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </DashboardProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App
