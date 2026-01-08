import { useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  getResearcherRawSensorSummary,
  getResearcherUnsafeSummary,
} from '../../lib/api'
import type { RawSensorSummary, UnsafeBehaviourSummary } from '../../lib/types'

export function ResearcherDashboard() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [week, setWeek] = useState('')
  const [unsafeSummary, setUnsafeSummary] = useState<UnsafeBehaviourSummary[]>([])
  const [rawSummary, setRawSummary] = useState<RawSensorSummary[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const params = {
        driverProfileId: driverId || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        week: week || undefined,
      }
      const [unsafe, raw] = await Promise.all([
        getResearcherUnsafeSummary(apiKey, params),
        getResearcherRawSensorSummary(apiKey, params),
      ])
      setUnsafeSummary(unsafe)
      setRawSummary(raw)
      setLoaded(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load summaries')
    } finally {
      setLoading(false)
    }
  }

  const totals = useMemo(() => {
    const unsafeTotal = unsafeSummary.reduce((sum, item) => sum + item.total, 0)
    const rawTotal = rawSummary.reduce((sum, item) => sum + item.total, 0)
    return { unsafeTotal, rawTotal }
  }, [unsafeSummary, rawSummary])

  return (
    <AppShell
      eyebrow="Research Lens"
      title="Researcher Workspace"
      subtitle="Summaries across unsafe behaviours and raw sensor coverage."
      actions={<div className="pill pill--active">Research</div>}
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Filters</h2>
          <span className="panel__meta">Optional slice parameters</span>
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
            placeholder="Start Date (YYYY-MM-DD)"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
          />
          <input
            className="login__input"
            placeholder="End Date (YYYY-MM-DD)"
            value={endDate}
            onChange={(event) => setEndDate(event.target.value)}
          />
          <input
            className="login__input"
            placeholder="Week (YYYY-Www)"
            value={week}
            onChange={(event) => setWeek(event.target.value)}
          />
          <button className="cta" onClick={handleLoad} disabled={loading}>
            {loading ? 'Loading...' : 'Load Summary'}
          </button>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="kpi-grid">
        <article className="card">
          <p className="card__label">Behaviour Events</p>
          <p className="card__value">
            {loaded ? totals.unsafeTotal : '--'}
          </p>
          <p className="card__detail">Total unsafe behaviour records</p>
        </article>
        <article className="card">
          <p className="card__label">Sensor Records</p>
          <p className="card__value">{loaded ? totals.rawTotal : '--'}</p>
          <p className="card__detail">Raw sensor samples</p>
        </article>
        <article className="card">
          <p className="card__label">Behaviour Types</p>
          <p className="card__value">
            {loaded ? unsafeSummary.length : '--'}
          </p>
          <p className="card__detail">Distinct behaviours</p>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Unsafe Behaviour Summary</h2>
            <span className="panel__meta">Severity averages</span>
          </div>
          <div className="stack">
            {unsafeSummary.length ? (
              unsafeSummary.map((item) => (
                <div className="stack__row" key={item.behaviour_type}>
                  <div>
                    <p className="stack__title">{item.behaviour_type}</p>
                    <p className="stack__meta">{item.total} events</p>
                  </div>
                  <span className="tag tag--warn">
                    {item.avg_severity.toFixed(2)}
                  </span>
                </div>
              ))
            ) : (
              <p className="panel__meta">No unsafe behaviour summary loaded.</p>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Raw Sensor Summary</h2>
            <span className="panel__meta">Accuracy snapshot</span>
          </div>
          <div className="table">
            <div className="table__row table__row--header">
              <span>Sensor</span>
              <span>Type</span>
              <span>Total</span>
              <span>Avg Accuracy</span>
            </div>
            {rawSummary.map((sensor) => (
              <div className="table__row" key={sensor.sensor_type}>
                <span>{sensor.sensor_type_name}</span>
                <span>{sensor.sensor_type}</span>
                <span>{sensor.total}</span>
                <span>{sensor.avg_accuracy.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </AppShell>
  )
}
