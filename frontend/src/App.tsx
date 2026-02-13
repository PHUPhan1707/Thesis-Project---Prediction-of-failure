import ErrorBoundary from './components/ErrorBoundary'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { DashboardProvider } from './context/DashboardContext'
import DashboardLayout from './layout/DashboardLayout'
import Overview from './pages/Overview'
import Details from './pages/Details'
import StudentDetailPage from './pages/StudentDetailPage'
import H5PAnalytics from './pages/H5PAnalytics'

function App() {
  return (
    <ErrorBoundary>
      <DashboardProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<Overview />} />
              <Route path="/h5p-analytics" element={<H5PAnalytics />} />
              <Route path="/details" element={<Details />} />
              <Route path="/student/:userId" element={<StudentDetailPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </DashboardProvider>
    </ErrorBoundary>
  )
}

export default App
