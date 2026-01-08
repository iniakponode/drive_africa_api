import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { RequireAuth, RequireRole } from './components/ProtectedRoute'
import { RoleRedirect } from './components/RoleRedirect'
import { AdminLanding } from './pages/AdminLanding'
import { AdminApiClients } from './pages/admin/AdminApiClients'
import { AdminCloudEndpoints } from './pages/admin/AdminCloudEndpoints'
import { AdminDatasetAccess } from './pages/admin/AdminDatasetAccess'
import { AdminDriverProfiles } from './pages/admin/AdminDriverProfiles'
import { AdminInsurancePartners } from './pages/admin/AdminInsurancePartners'
import { DriverDashboard } from './pages/driver/DriverDashboard'
import { DriverLeaderboard } from './pages/driver/DriverLeaderboard'
import { DriverProfilePage } from './pages/driver/DriverProfile'
import { DriverQuestionnaire } from './pages/driver/DriverQuestionnaire'
import { DriverTips } from './pages/driver/DriverTips'
import { DriverTrips } from './pages/driver/DriverTrips'
import { FleetDashboard } from './pages/fleet/FleetDashboard'
import { FleetAnalytics } from './pages/fleet/FleetAnalytics'
import { FleetAssignments } from './pages/fleet/FleetAssignments'
import { FleetMonitor } from './pages/fleet/FleetMonitor'
import { FleetManagement } from './pages/fleet/FleetManagement'
import { FleetReports } from './pages/fleet/FleetReports'
import { FleetTripContextView } from './pages/fleet/FleetTripContext'
import { InsuranceDashboard } from './pages/insurance/InsuranceDashboard'
import { InsuranceAlerts } from './pages/insurance/InsuranceAlerts'
import { InsuranceRawExport } from './pages/insurance/InsuranceRawExport'
import { InsuranceReports } from './pages/insurance/InsuranceReports'
import { InsuranceTelematics } from './pages/insurance/InsuranceTelematics'
import { Login } from './pages/Login'
import { ResearcherDashboard } from './pages/researcher/ResearcherDashboard'
import { ResearcherAlcoholBundle } from './pages/researcher/ResearcherAlcoholBundle'
import { ResearcherExports } from './pages/researcher/ResearcherExports'
import { ResearcherIngestion } from './pages/researcher/ResearcherIngestion'
import { ResearcherSnapshots } from './pages/researcher/ResearcherSnapshots'
import { Unauthorized } from './pages/Unauthorized'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <RoleRedirect />
          </RequireAuth>
        }
      />
      <Route
        path="/fleet"
        element={
          <RequireRole roles={['fleet_manager', 'admin']}>
            <FleetDashboard />
          </RequireRole>
        }
      />
      <Route
        path="/fleet/monitor"
        element={
          <RequireRole roles={['fleet_manager', 'admin']}>
            <FleetMonitor />
          </RequireRole>
        }
      />
      <Route
        path="/fleet/assignments"
        element={
          <RequireRole roles={['fleet_manager', 'admin']}>
            <FleetAssignments />
          </RequireRole>
        }
      />
      <Route
        path="/fleet/trip-context"
        element={
          <RequireRole roles={['fleet_manager', 'admin']}>
            <FleetTripContextView />
          </RequireRole>
        }
      />
      <Route
        path="/fleet/reports"
        element={
          <RequireRole roles={['fleet_manager', 'admin']}>
            <FleetReports />
          </RequireRole>
        }
      />
      <Route
        path="/fleet/analytics"
        element={
          <RequireRole roles={['fleet_manager', 'admin']}>
            <FleetAnalytics />
          </RequireRole>
        }
      />
      <Route
        path="/fleet/setup"
        element={
          <RequireRole roles={['fleet_manager', 'admin']}>
            <FleetManagement />
          </RequireRole>
        }
      />
      <Route
        path="/driver"
        element={
          <RequireRole roles={['driver', 'admin']}>
            <DriverDashboard />
          </RequireRole>
        }
      />
      <Route
        path="/driver/profile"
        element={
          <RequireRole roles={['driver', 'admin']}>
            <DriverProfilePage />
          </RequireRole>
        }
      />
      <Route
        path="/driver/trips"
        element={
          <RequireRole roles={['driver', 'admin']}>
            <DriverTrips />
          </RequireRole>
        }
      />
      <Route
        path="/driver/questionnaire"
        element={
          <RequireRole roles={['driver', 'admin']}>
            <DriverQuestionnaire />
          </RequireRole>
        }
      />
      <Route
        path="/driver/tips"
        element={
          <RequireRole roles={['driver', 'admin']}>
            <DriverTips />
          </RequireRole>
        }
      />
      <Route
        path="/driver/leaderboard"
        element={
          <RequireRole roles={['driver', 'admin']}>
            <DriverLeaderboard />
          </RequireRole>
        }
      />
      <Route
        path="/researcher"
        element={
          <RequireRole roles={['researcher', 'admin']}>
            <ResearcherDashboard />
          </RequireRole>
        }
      />
      <Route
        path="/researcher/alcohol-bundle"
        element={
          <RequireRole roles={['researcher', 'admin']}>
            <ResearcherAlcoholBundle />
          </RequireRole>
        }
      />
      <Route
        path="/researcher/exports"
        element={
          <RequireRole roles={['researcher', 'admin']}>
            <ResearcherExports />
          </RequireRole>
        }
      />
      <Route
        path="/researcher/snapshots"
        element={
          <RequireRole roles={['researcher', 'admin']}>
            <ResearcherSnapshots />
          </RequireRole>
        }
      />
      <Route
        path="/researcher/ingestion"
        element={
          <RequireRole roles={['researcher', 'admin']}>
            <ResearcherIngestion />
          </RequireRole>
        }
      />
      <Route
        path="/insurance"
        element={
          <RequireRole roles={['insurance_partner', 'admin']}>
            <InsuranceDashboard />
          </RequireRole>
        }
      />
      <Route
        path="/insurance/telematics"
        element={
          <RequireRole roles={['insurance_partner', 'admin']}>
            <InsuranceTelematics />
          </RequireRole>
        }
      />
      <Route
        path="/insurance/alerts"
        element={
          <RequireRole roles={['insurance_partner', 'admin']}>
            <InsuranceAlerts />
          </RequireRole>
        }
      />
      <Route
        path="/insurance/reports"
        element={
          <RequireRole roles={['insurance_partner', 'admin']}>
            <InsuranceReports />
          </RequireRole>
        }
      />
      <Route
        path="/insurance/raw-export"
        element={
          <RequireRole roles={['insurance_partner', 'admin']}>
            <InsuranceRawExport />
          </RequireRole>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireRole roles={['admin']}>
            <AdminLanding />
          </RequireRole>
        }
      />
      <Route
        path="/admin/api-clients"
        element={
          <RequireRole roles={['admin']}>
            <AdminApiClients />
          </RequireRole>
        }
      />
      <Route
        path="/admin/dataset-access"
        element={
          <RequireRole roles={['admin']}>
            <AdminDatasetAccess />
          </RequireRole>
        }
      />
      <Route
        path="/admin/cloud-endpoints"
        element={
          <RequireRole roles={['admin']}>
            <AdminCloudEndpoints />
          </RequireRole>
        }
      />
      <Route
        path="/admin/insurance-partners"
        element={
          <RequireRole roles={['admin']}>
            <AdminInsurancePartners />
          </RequireRole>
        }
      />
      <Route
        path="/admin/driver-profiles"
        element={
          <RequireRole roles={['admin']}>
            <AdminDriverProfiles />
          </RequireRole>
        }
      />
      <Route path="/unauthorized" element={<Unauthorized />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
