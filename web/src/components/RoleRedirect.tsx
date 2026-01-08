import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function RoleRedirect() {
  const { profile } = useAuth()
  if (!profile) {
    return <Navigate to="/login" replace />
  }
  if (profile.role === 'fleet_manager') {
    return <Navigate to="/fleet" replace />
  }
  if (profile.role === 'driver') {
    return <Navigate to="/driver" replace />
  }
  if (profile.role === 'researcher') {
    return <Navigate to="/researcher" replace />
  }
  if (profile.role === 'insurance_partner') {
    return <Navigate to="/insurance" replace />
  }
  return <Navigate to="/admin" replace />
}
