import { useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getFleetDriverEvents, getFleetDriverMonitor } from '../../lib/api'
import type {
  FleetDriverEventsResponse,
  FleetDriverMonitor,
} from '../../lib/types'

function shortId(value: string) {
  return value.slice(0, 6).toUpperCase()
}

export function FleetMonitor() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [limit, setLimit] = useState(20)
  const [monitor, setMonitor] = useState<FleetDriverMonitor | null>(null)
  const [events, setEvents] = useState<FleetDriverEventsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLoad = async () => {
    if (!apiKey) return
    if (!driverId) {
      setError('Provide a driverProfileId to load monitoring data.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const [monitorRes, eventsRes] = await Promise.all([
        getFleetDriverMonitor(apiKey, driverId),
        getFleetDriverEvents(apiKey, driverId, limit),
      ])
      setMonitor(monitorRes)
      setEvents(eventsRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load monitor data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Fleet Live"
      title="Driver Monitor"
      subtitle="Track active trip state, compliance signals, and recent events."
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Load Driver</h2>
          <span className="panel__meta">Use a driverProfileId</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={driverId}
            onChange={(event) => setDriverId(event.target.value)}
          />
          <input
            className="login__input"
            type="number"
            min={1}
            max={100}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
          <button className="cta" onClick={handleLoad} disabled={loading}>
            {loading ? 'Loading...' : 'Load Monitor'}
          </button>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      {monitor && (
        <section className="kpi-grid">
          <article className="card">
            <p className="card__label">Trip Status</p>
            <p className="card__value">{monitor.activeTripStatus}</p>
            <p className="card__detail">Current activity</p>
          </article>
          <article className="card">
            <p className="card__label">Unsafe Behaviours</p>
            <p className="card__value">{monitor.unsafeBehaviourCount}</p>
            <p className="card__detail">All-time logged</p>
          </article>
          <article className="card">
            <p className="card__label">Last 24h</p>
            <p className="card__value">{monitor.unsafeBehaviourLast24h}</p>
            <p className="card__detail">Recent spikes</p>
          </article>
          <article className="card">
            <p className="card__label">Speed Compliance</p>
            <p className="card__value">
              {(monitor.speedComplianceRatio * 100).toFixed(1)}%
            </p>
            <p className="card__detail">{monitor.speedingCount} speeding events</p>
          </article>
        </section>
      )}

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Recent Unsafe Behaviours</h2>
            <span className="panel__meta">Latest signals</span>
          </div>
          <div className="stack">
            {monitor?.recentUnsafeBehaviours.length ? (
              monitor.recentUnsafeBehaviours.map((item) => (
                <div className="stack__row" key={item.id}>
                  <div>
                    <p className="stack__title">{item.behaviour_type}</p>
                    <p className="stack__meta">
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <span className="tag tag--warn">
                    {item.severity.toFixed(1)}
                  </span>
                </div>
              ))
            ) : (
              <p className="panel__meta">No behaviours loaded.</p>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Event Feed</h2>
            <span className="panel__meta">Last {limit} events</span>
          </div>
          <div className="alerts">
            {events?.events.length ? (
              events.events.map((event) => (
                <div className="alert" key={event.id}>
                  <div>
                    <p className="alert__title">{event.event_type}</p>
                    <p className="alert__meta">
                      {event.message ?? 'No message'}
                    </p>
                    <p className="alert__meta">
                      Driver {shortId(event.driverProfileId)}
                    </p>
                  </div>
                  <div className="alert__details">
                    <span className="badge badge--medium">
                      {event.gps_health ?? 'GPS'}
                    </span>
                    <span className="alert__time">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="panel__meta">No events loaded.</p>
            )}
          </div>
        </article>
      </section>
    </AppShell>
  )
}
