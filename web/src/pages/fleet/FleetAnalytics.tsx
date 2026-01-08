import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getDriverKpis, getLeaderboard } from '../../lib/api'
import type { DriverKpiResponse, LeaderboardResponse } from '../../lib/types'

const PERIODS = ['day', 'week', 'month'] as const

function shortId(value: string) {
  return value.slice(0, 6).toUpperCase()
}

export function FleetAnalytics() {
  const { apiKey, profile } = useAuth()
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>('week')
  const [fleetScopeId, setFleetScopeId] = useState('')
  const [kpis, setKpis] = useState<DriverKpiResponse | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      if (!apiKey) return
      if (profile?.role === 'admin' && !fleetScopeId) {
        setKpis(null)
        setLeaderboard(null)
        return
      }
      setLoading(true)
      setError('')
      try {
        const scope =
          profile?.role === 'admin' && fleetScopeId
            ? { fleetId: fleetScopeId }
            : undefined
        const [kpiRes, leaderboardRes] = await Promise.all([
          getDriverKpis(apiKey, period, scope),
          getLeaderboard(apiKey, period, scope),
        ])
        if (!active) return
        setKpis(kpiRes)
        setLeaderboard(leaderboardRes)
      } catch (err) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load analytics')
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [apiKey, period, profile?.role, fleetScopeId])

  const totals = useMemo(() => {
    const drivers = kpis?.drivers ?? []
    const distance = drivers.reduce((sum, d) => sum + d.distance_km, 0)
    const unsafe = drivers.reduce((sum, d) => sum + d.unsafe_count, 0)
    return {
      drivers: drivers.length,
      distance,
      unsafe,
    }
  }, [kpis])

  return (
    <AppShell
      eyebrow="Analytics"
      title="Fleet Analytics"
      subtitle="Driver KPIs and leaderboard ranking per time window."
      actions={
        <>
          {PERIODS.map((value) => (
            <button
              key={value}
              className={`pill ${period === value ? 'pill--active' : ''}`}
              onClick={() => setPeriod(value)}
            >
              {value}
            </button>
          ))}
        </>
      }
    >
      {profile?.role === 'admin' && (
        <section className="panel panel--wide">
          <div className="panel__header">
            <h2>Fleet Scope</h2>
            <span className="panel__meta">Admin analytics require a fleetId.</span>
          </div>
          <div className="form-row">
            <input
              className="login__input"
              placeholder="Fleet ID"
              value={fleetScopeId}
              onChange={(event) => setFleetScopeId(event.target.value)}
            />
          </div>
        </section>
      )}

      {error && <div className="panel panel--wide">{error}</div>}

      <section className="kpi-grid">
        <article className="card">
          <p className="card__label">Drivers</p>
          <p className="card__value">{loading ? '--' : totals.drivers}</p>
          <p className="card__detail">Active in scope</p>
        </article>
        <article className="card">
          <p className="card__label">Distance</p>
          <p className="card__value">
            {loading ? '--' : totals.distance.toFixed(1)}
          </p>
          <p className="card__detail">Total km</p>
        </article>
        <article className="card">
          <p className="card__label">Unsafe Events</p>
          <p className="card__value">{loading ? '--' : totals.unsafe}</p>
          <p className="card__detail">All drivers</p>
        </article>
      </section>

      <section className="grid">
        <article className="panel panel--wide">
          <div className="panel__header">
            <h2>Driver KPIs</h2>
            <span className="panel__meta">UBPK and distance per driver</span>
          </div>
          {kpis?.drivers.length ? (
            <div className="table">
              <div className="table__row table__row--header">
                <span>Driver</span>
                <span>UBPK</span>
                <span>Unsafe</span>
                <span>Distance (km)</span>
                <span>Bad Days</span>
              </div>
              {kpis.drivers.map((driver) => (
                <div className="table__row" key={driver.driverProfileId}>
                  <span>Driver {shortId(driver.driverProfileId)}</span>
                  <span>{driver.ubpk.toFixed(2)}</span>
                  <span>{driver.unsafe_count}</span>
                  <span>{driver.distance_km.toFixed(1)}</span>
                  <span>{driver.bad_days}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="panel__meta">No KPI data loaded.</p>
          )}
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Best</h2>
            <span className="panel__meta">Lowest UBPK</span>
          </div>
          <div className="stack">
            {leaderboard?.best?.map((entry) => (
              <div className="stack__row" key={entry.driverProfileId}>
                <div>
                  <p className="stack__title">Driver {shortId(entry.driverProfileId)}</p>
                  <p className="stack__meta">{entry.distance_km.toFixed(1)} km</p>
                </div>
                <span className="tag tag--good">{entry.ubpk.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Needs Attention</h2>
            <span className="panel__meta">Highest UBPK</span>
          </div>
          <div className="stack">
            {leaderboard?.worst?.map((entry) => (
              <div className="stack__row" key={entry.driverProfileId}>
                <div>
                  <p className="stack__title">Driver {shortId(entry.driverProfileId)}</p>
                  <p className="stack__meta">{entry.distance_km.toFixed(1)} km</p>
                </div>
                <span className="tag tag--warn">{entry.ubpk.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </AppShell>
  )
}
