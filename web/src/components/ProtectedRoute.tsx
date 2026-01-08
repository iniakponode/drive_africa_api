import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import type { Role } from '../lib/types'

export function RequireAuth({ children }: { children: JSX.Element }) {
  const { profile, loading } = useAuth()
  if (loading) {
    return <div className="page-status">Loading session...</div>
  }
  if (!profile) {
    return <Navigate to="/login" replace />
  }
  return children
}

export function RequireRole({
  roles,
  children,
}: {
  roles: Role[]
  children: JSX.Element
}) {
  const { profile, loading } = useAuth()
  if (loading) {
    return <div className="page-status">Loading session...</div>
  }
  if (!profile) {
    return <Navigate to="/login" replace />
  }
  if (!roles.includes(profile.role)) {
    return <Navigate to="/unauthorized" replace />
  }
  return children
}
