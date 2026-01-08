import { useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getFleetAssignment } from '../../lib/api'
import type { DriverAssignmentWithCompliance } from '../../lib/types'

export function FleetAssignments() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [assignment, setAssignment] =
    useState<DriverAssignmentWithCompliance | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLoad = async () => {
    if (!apiKey) return
    if (!driverId) {
      setError('Provide a driverProfileId to fetch assignment details.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await getFleetAssignment(apiKey, driverId)
      setAssignment(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assignment')
    } finally {
      setLoading(false)
    }
  }

  const assignmentData = assignment?.assignment
  const questionnaire = assignment?.questionnaire

  return (
    <AppShell
      eyebrow="Operations"
      title="Assignments"
      subtitle="Confirm fleet placement, onboarding status, and compliance notes."
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Find Driver Assignment</h2>
          <span className="panel__meta">Latest assignment per driver</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={driverId}
            onChange={(event) => setDriverId(event.target.value)}
          />
          <button className="cta" onClick={handleLoad} disabled={loading}>
            {loading ? 'Loading...' : 'Load Assignment'}
          </button>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Assignment</h2>
            <span className="panel__meta">Fleet and vehicle group</span>
          </div>
          {assignmentData ? (
            <div className="kv">
              <div className="kv__row">
                <span className="kv__label">Fleet</span>
                <span className="kv__value">
                  {assignmentData.fleet?.name ?? assignmentData.fleet_id}
                </span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Vehicle Group</span>
                <span className="kv__value">
                  {assignmentData.vehicle_group?.name ??
                    assignmentData.vehicle_group_id ??
                    'Unassigned'}
                </span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Onboarding</span>
                <span className="kv__value">
                  {assignmentData.onboarding_completed ? 'Complete' : 'Pending'}
                </span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Assigned At</span>
                <span className="kv__value">
                  {new Date(assignmentData.assigned_at).toLocaleString()}
                </span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Compliance Note</span>
                <span className="kv__value">
                  {assignmentData.compliance_note ?? 'None'}
                </span>
              </div>
            </div>
          ) : (
            <p className="panel__meta">No assignment loaded.</p>
          )}
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Alcohol Questionnaire</h2>
            <span className="panel__meta">Latest response</span>
          </div>
          {questionnaire ? (
            <div className="kv">
              <div className="kv__row">
                <span className="kv__label">Drank Alcohol</span>
                <span className="kv__value">
                  {questionnaire.drankAlcohol ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Plans to Drive</span>
                <span className="kv__value">
                  {questionnaire.plansToDrive ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Impairment Level</span>
                <span className="kv__value">
                  {questionnaire.impairmentLevel}
                </span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Response Date</span>
                <span className="kv__value">
                  {questionnaire.date
                    ? new Date(questionnaire.date).toLocaleDateString()
                    : 'Unknown'}
                </span>
              </div>
            </div>
          ) : (
            <p className="panel__meta">No questionnaire response loaded.</p>
          )}
        </article>
      </section>
    </AppShell>
  )
}
