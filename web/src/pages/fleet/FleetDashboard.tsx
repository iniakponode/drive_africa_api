import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  getBadDays,
  getDriverKpis,
  getLeaderboard,
} from '../../lib/api'
import type {
  BadDaysResponse,
  DriverKpiResponse,
  LeaderboardResponse,
} from '../../lib/types'

const PERIODS = ['day', 'week', 'month'] as const

function shortId(value: string) {
  return value.slice(0, 6).toUpperCase()
}

export function FleetDashboard() {
  const { apiKey, profile } = useAuth()
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>('week')
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null)
  const [driverKpis, setDriverKpis] = useState<DriverKpiResponse | null>(null)
  const [badDays, setBadDays] = useState<BadDaysResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [fleetScopeId, setFleetScopeId] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      if (!apiKey) {
        return
      }
      setLoading(true)
      setError('')
      try {
        if (profile?.role === 'admin' && !fleetScopeId) {
          setLoading(false)
          return
        }
        const scope =
          profile?.role === 'admin' && fleetScopeId
            ? { fleetId: fleetScopeId }
            : undefined
        const [leaderboardRes, kpiRes, badDaysRes] = await Promise.all([
          getLeaderboard(apiKey, period, scope),
          getDriverKpis(apiKey, period, scope),
          getBadDays(apiKey, scope),
        ])
        if (!active) {
          return
        }
        setLeaderboard(leaderboardRes)
        setDriverKpis(kpiRes)
        setBadDays(badDaysRes)
      } catch (err) {
        if (!active) {
          return
        }
        setError(err instanceof Error ? err.message : 'Failed to load KPIs')
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [apiKey, period, profile?.role, fleetScopeId])

  const kpiSummary = useMemo(() => {
    const drivers = driverKpis?.drivers ?? []
    const totalDrivers = drivers.length
    const avgUbpk =
      drivers.reduce((sum, driver) => sum + driver.ubpk, 0) /
      (totalDrivers || 1)
    const badDaysTotal = badDays?.drivers.reduce(
      (sum, driver) => sum + driver.bad_days,
      0,
    )
    return {
      totalDrivers,
      avgUbpk,
      badDaysTotal: badDaysTotal ?? 0,
    }
  }, [driverKpis, badDays])

  const pulseDrivers = useMemo(() => {
    const drivers = driverKpis?.drivers ?? []
    return drivers.slice(0, 4).map((driver) => {
      const risk =
        driver.ubpk >= 2 ? 'High' : driver.ubpk >= 1.4 ? 'Medium' : 'Low'
      return {
        name: `Driver ${shortId(driver.driverProfileId)}`,
        status: 'Status pending',
        ubpk: driver.ubpk.toFixed(2),
        lastTrip: 'Recent trip',
        risk,
      }
    })
  }, [driverKpis])

  const avgDelta = useMemo(() => {
    if (!badDays) {
      return {
        day: 0,
        week: 0,
        month: 0,
      }
    }
    const calc = (key: 'last_day_delta' | 'last_week_delta' | 'last_month_delta') => {
      const values = badDays.drivers
        .map((driver) => driver[key] ?? 0)
        .filter((value) => value !== null)
      if (!values.length) {
        return 0
      }
      return values.reduce((sum, value) => sum + value, 0) / values.length
    }
    return {
      day: calc('last_day_delta'),
      week: calc('last_week_delta'),
      month: calc('last_month_delta'),
    }
  }, [badDays])

  const bestDrivers = leaderboard?.best ?? []
  const worstDrivers = leaderboard?.worst ?? []

  return (
    <AppShell
      eyebrow="Operational Pulse"
      title="Fleet Overview"
      subtitle="Lagos Ops performance, with UBPK and bad-day spikes."
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
          <button className="cta">Download Report</button>
        </>
      }
    >
      {profile?.role === 'admin' && (
        <section className="panel panel--wide">
          <div className="panel__header">
            <h2>Select Fleet Scope</h2>
            <span className="panel__meta">
              Admin access requires a fleetId for analytics.
            </span>
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
        <article className="card reveal">
          <div className="card__header">
            <p className="card__label">Fleet UBPK</p>
            <span className="card__change">
              {loading ? 'Loading' : `${kpiSummary.totalDrivers} drivers`}
            </span>
          </div>
          <p className="card__value">
            {loading ? '--' : kpiSummary.avgUbpk.toFixed(2)}
          </p>
          <p className="card__detail">Unsafe behaviours per km</p>
        </article>
        <article className="card reveal" style={{ animationDelay: '80ms' }}>
          <div className="card__header">
            <p className="card__label">Bad Days</p>
            <span className="card__change">75th percentile delta</span>
          </div>
          <p className="card__value">
            {loading ? '--' : kpiSummary.badDaysTotal}
          </p>
          <p className="card__detail">Across selected window</p>
        </article>
        <article className="card reveal" style={{ animationDelay: '160ms' }}>
          <div className="card__header">
            <p className="card__label">Active Drivers</p>
            <span className="card__change">
              {loading ? 'Loading' : 'Snapshot'}
            </span>
          </div>
          <p className="card__value">
            {loading ? '--' : kpiSummary.totalDrivers}
          </p>
          <p className="card__detail">Tracked in this fleet</p>
        </article>
        <article className="card reveal" style={{ animationDelay: '240ms' }}>
          <div className="card__header">
            <p className="card__label">Critical Alerts</p>
            <span className="card__change">Monitoring feed</span>
          </div>
          <p className="card__value">{loading ? '--' : '0'}</p>
          <p className="card__detail">Alerts not yet connected</p>
        </article>
      </section>

      <section className="grid">
        <article className="panel reveal" style={{ animationDelay: '120ms' }}>
          <div className="panel__header">
            <h2>Driver Pulse</h2>
            <span className="panel__meta">Latest status snapshots</span>
          </div>
          <div className="driver-list">
            {pulseDrivers.length === 0 && <p>No drivers loaded.</p>}
            {pulseDrivers.map((driver) => (
              <div className="driver" key={driver.name}>
                <div>
                  <p className="driver__name">{driver.name}</p>
                  <p className="driver__meta">{driver.lastTrip}</p>
                </div>
                <div className="driver__metrics">
                  <span className="status">{driver.status}</span>
                  <span className={`risk risk--${driver.risk.toLowerCase()}`}>
                    {driver.risk}
                  </span>
                  <span className="ubpk">{driver.ubpk} UBPK</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel reveal" style={{ animationDelay: '200ms' }}>
          <div className="panel__header">
            <h2>Leaderboard</h2>
            <span className="panel__meta">Best vs worst performers</span>
          </div>
          <div className="leaderboard">
            <div>
              <p className="leaderboard__title">Best</p>
              {bestDrivers.map((entry) => (
                <div className="leaderboard__row" key={entry.driverProfileId}>
                  <span>Driver {shortId(entry.driverProfileId)}</span>
                  <span className="leaderboard__score">
                    {entry.ubpk.toFixed(2)}
                  </span>
                  <span className="leaderboard__delta down">stable</span>
                </div>
              ))}
            </div>
            <div>
              <p className="leaderboard__title">Needs Attention</p>
              {worstDrivers.map((entry) => (
                <div className="leaderboard__row" key={entry.driverProfileId}>
                  <span>Driver {shortId(entry.driverProfileId)}</span>
                  <span className="leaderboard__score">
                    {entry.ubpk.toFixed(2)}
                  </span>
                  <span className="leaderboard__delta up">watch</span>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article className="panel panel--wide reveal" style={{ animationDelay: '280ms' }}>
          <div className="panel__header">
            <h2>Bad Days Radar</h2>
            <span className="panel__meta">75th percentile delta tracking</span>
          </div>
          <div className="radar">
            <div className="radar__card">
              <p>Daily Delta</p>
              <h3>{avgDelta.day.toFixed(2)}</h3>
              <span>Threshold {badDays?.thresholds.day.toFixed(2) ?? '--'}</span>
            </div>
            <div className="radar__card">
              <p>Weekly Delta</p>
              <h3>{avgDelta.week.toFixed(2)}</h3>
              <span>Threshold {badDays?.thresholds.week.toFixed(2) ?? '--'}</span>
            </div>
            <div className="radar__card">
              <p>Monthly Delta</p>
              <h3>{avgDelta.month.toFixed(2)}</h3>
              <span>Threshold {badDays?.thresholds.month.toFixed(2) ?? '--'}</span>
            </div>
            <div className="radar__insight">
              <h4>Coaching focus</h4>
              <p>
                Check drivers with rising UBPK deltas over the selected window.
              </p>
              <button className="ghost">View Driver KPIs</button>
            </div>
          </div>
        </article>

        <article className="panel panel--wide reveal" style={{ animationDelay: '360ms' }}>
          <div className="panel__header">
            <h2>Critical Alerts</h2>
            <span className="panel__meta">Alerts feed pending integration</span>
          </div>
          <div className="alerts">
            <div className="alert">
              <div>
                <p className="alert__title">No alerts configured</p>
                <p className="alert__meta">
                  Connect fleet events to populate this feed.
                </p>
              </div>
              <div className="alert__details">
                <span className="badge badge--medium">Info</span>
                <span className="alert__time">--</span>
              </div>
            </div>
          </div>
        </article>
      </section>
    </AppShell>
  )
}
