import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import AppLayout from './components/ui/AppLayout'
import ProtectedRoute from './components/ui/ProtectedRoute'

// Pages
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import MachinesPage from './pages/MachinesPage'
import MachineDetailPage from './pages/MachineDetailPage'
import OperatorsPage from './pages/OperatorsPage'
import OperatorDetailPage from './pages/OperatorDetailPage'
import TasksPage from './pages/TasksPage'
import AlertsPage from './pages/AlertsPage'
import IncidentsPage from './pages/IncidentsPage'
import WatchPage from './pages/WatchPage'
import PrestartPage from './pages/PrestartPage'
import DashcamPage from './pages/DashcamPage'
import TrainingPage from './pages/TrainingPage'
import AnalyticsPage from './pages/AnalyticsPage'
import CopilotPage from './pages/CopilotPage'
import SettingsPage from './pages/SettingsPage'
import OperatorDashboardPage from './pages/OperatorDashboardPage'

export default function App() {
  const { isAuthenticated, user } = useAuthStore()

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={
          isAuthenticated
            ? <Navigate to={user?.role === 'operator' ? '/operator' : '/dashboard'} replace />
            : <LoginPage />
        } />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            {/* Engineer/Supervisor routes */}
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/machines" element={<MachinesPage />} />
            <Route path="/machines/:id" element={<MachineDetailPage />} />
            <Route path="/operators" element={<OperatorsPage />} />
            <Route path="/operators/:id" element={<OperatorDetailPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/incidents" element={<IncidentsPage />} />
            <Route path="/training" element={<TrainingPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/prestart" element={<PrestartPage />} />
            <Route path="/dashcam" element={<DashcamPage />} />
            <Route path="/copilot" element={<CopilotPage />} />
            <Route path="/settings" element={<SettingsPage />} />

            {/* Operator-specific */}
            <Route path="/operator" element={<OperatorDashboardPage />} />
            <Route path="/watch" element={<WatchPage />} />

            {/* Default redirect */}
            <Route path="/" element={
              <Navigate to={user?.role === 'operator' ? '/operator' : '/dashboard'} replace />
            } />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
