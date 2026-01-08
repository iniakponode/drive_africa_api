import { useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getInsuranceAlerts } from '../../lib/api'
import type { InsuranceAlert } from '../../lib/types'

function shortId(value: string) {
  return value.slice(0, 6).toUpperCase()
}

export function InsuranceAlerts() {
  const { apiKey } = useAuth()
  const [minSeverity, setMinSeverity] = useState(0.8)
  const [sinceHours, setSinceHours] = useState(24)
  const [limit, setLimit] = useState(100)
  const [alerts, setAlerts] = useState<InsuranceAlert[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getInsuranceAlerts(apiKey, {
        minSeverity,
        sinceHours,
        limit,
      })
      setAlerts(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }

  const summary = useMemo(() => {
    const unsafe = alerts.filter((item) => item.alert_type === 'unsafe_behaviour')
    const speed = alerts.filter((item) => item.alert_type === 'speed_violation')
    return { unsafe: unsafe.length, speed: speed.length }
  }, [alerts])

  return (
    <AppShell
      eyebrow="Alerts"
      title="Risk Alerts"
      subtitle="Severe unsafe behaviours and speed violations."
      actions={
        <button className="cta" onClick={handleLoad} disabled={loading}>
          {loading ? 'Loading...' : 'Load Alerts'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Filters</h2>
          <span className="panel__meta">Severity + time window</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            type="number"
            step="0.1"
            min={0}
            max={1}
            value={minSeverity}
            onChange={(event) => setMinSeverity(Number(event.target.value))}
          />
          <input
            className="login__input"
            type="number"
            min={1}
            max={168}
            value={sinceHours}
            onChange={(event) => setSinceHours(Number(event.target.value))}
          />
          <input
            className="login__input"
            type="number"
            min={1}
            max={500}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="kpi-grid">
        <article className="card">
          <p className="card__label">Total Alerts</p>
          <p className="card__value">{alerts.length || '--'}</p>
          <p className="card__detail">Loaded alerts</p>
        </article>
        <article className="card">
          <p className="card__label">Unsafe Behaviours</p>
          <p className="card__value">{summary.unsafe || '--'}</p>
          <p className="card__detail">Severity threshold hits</p>
        </article>
        <article className="card">
          <p className="card__label">Speed Violations</p>
          <p className="card__value">{summary.speed || '--'}</p>
          <p className="card__detail">Limit exceedances</p>
        </article>
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Alert Feed</h2>
          <span className="panel__meta">{alerts.length} alerts</span>
        </div>
        <div className="alerts">
          {alerts.length ? (
            alerts.map((alert, index) => (
              <div className="alert" key={`${alert.alert_type}-${index}`}>
                <div>
                  <p className="alert__title">
                    {alert.alert_type.replace('_', ' ')}
                  </p>
                  <p className="alert__meta">{alert.message}</p>
                  <p className="alert__meta">
                    Driver {shortId(alert.driverProfileId)}
                  </p>
                </div>
                <div className="alert__details">
                  <span
                    className={`badge ${
                      alert.alert_type === 'speed_violation'
                        ? 'badge--medium'
                        : 'badge--high'
                    }`}
                  >
                    {alert.severity?.toFixed(2) ?? 'Speed'}
                  </span>
                  <span className="alert__time">
                    {alert.timestamp
                      ? new Date(alert.timestamp).toLocaleString()
                      : '--'}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <p className="panel__meta">No alerts loaded.</p>
          )}
        </div>
      </section>
    </AppShell>
  )
}
