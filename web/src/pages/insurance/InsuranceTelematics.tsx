import { useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getInsuranceTelematicsTrips } from '../../lib/api'
import type { InsuranceTelematicsResponse } from '../../lib/types'

function shortId(value: string) {
  return value.slice(0, 6).toUpperCase()
}

export function InsuranceTelematics() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [skip, setSkip] = useState(0)
  const [limit, setLimit] = useState(50)
  const [data, setData] = useState<InsuranceTelematicsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const response = await getInsuranceTelematicsTrips(apiKey, {
        driverProfileId: driverId || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        skip,
        limit,
      })
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load telematics')
    } finally {
      setLoading(false)
    }
  }

  const totals = useMemo(() => {
    const trips = data?.trips ?? []
    const distance = trips.reduce((sum, trip) => sum + trip.distance_km, 0)
    const unsafe = trips.reduce((sum, trip) => sum + trip.unsafe_count, 0)
    const severity =
      trips.reduce((sum, trip) => sum + trip.avg_severity, 0) / (trips.length || 1)
    const compliance =
      trips.reduce((sum, trip) => sum + trip.speed_compliance_ratio, 0) /
      (trips.length || 1)
    return { distance, unsafe, severity, compliance }
  }, [data])

  return (
    <AppShell
      eyebrow="Telematics"
      title="Trips & Risk Signals"
      subtitle="Trip-level risk telemetry for your insured drivers."
      actions={
        <button className="cta" onClick={handleLoad} disabled={loading}>
          {loading ? 'Loading...' : 'Load Trips'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Filters</h2>
          <span className="panel__meta">Optional driver/date slicing</span>
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
            type="number"
            min={0}
            value={skip}
            onChange={(event) => setSkip(Number(event.target.value))}
          />
          <input
            className="login__input"
            type="number"
            min={1}
            max={200}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="kpi-grid">
        <article className="card">
          <p className="card__label">Trips Loaded</p>
          <p className="card__value">{data?.total ?? '--'}</p>
          <p className="card__detail">Telematics trips</p>
        </article>
        <article className="card">
          <p className="card__label">Distance</p>
          <p className="card__value">
            {data ? totals.distance.toFixed(1) : '--'}
          </p>
          <p className="card__detail">Total km</p>
        </article>
        <article className="card">
          <p className="card__label">Unsafe Events</p>
          <p className="card__value">
            {data ? totals.unsafe : '--'}
          </p>
          <p className="card__detail">Unsafe behaviours</p>
        </article>
        <article className="card">
          <p className="card__label">Compliance</p>
          <p className="card__value">
            {data ? `${(totals.compliance * 100).toFixed(1)}%` : '--'}
          </p>
          <p className="card__detail">Avg speed compliance</p>
        </article>
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Trip Log</h2>
          <span className="panel__meta">
            {data?.trips.length ?? 0} trips returned
          </span>
        </div>
        <div className="table">
          <div className="table__row table__row--header">
            <span>Trip</span>
            <span>Driver</span>
            <span>Distance</span>
            <span>Unsafe</span>
            <span>Avg Severity</span>
            <span>Speeding</span>
            <span>Compliance</span>
          </div>
          {data?.trips.map((trip) => (
            <div className="table__row" key={trip.trip_id}>
              <span>{shortId(trip.trip_id)}</span>
              <span>{shortId(trip.driverProfileId)}</span>
              <span>{trip.distance_km.toFixed(1)} km</span>
              <span>{trip.unsafe_count}</span>
              <span>{trip.avg_severity.toFixed(2)}</span>
              <span>{trip.speeding_events}</span>
              <span>{(trip.speed_compliance_ratio * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  )
}
