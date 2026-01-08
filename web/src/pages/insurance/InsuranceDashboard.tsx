import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getBadDays, getDriverKpis, getLeaderboard } from '../../lib/api'
import type { BadDaysResponse, DriverKpiResponse, LeaderboardResponse } from '../../lib/types'

const PERIODS = ['day', 'week', 'month'] as const

function shortId(value: string) {
  return value.slice(0, 6).toUpperCase()
}

export function InsuranceDashboard() {
  const { apiKey } = useAuth()
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>('week')
  const [kpis, setKpis] = useState<DriverKpiResponse | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null)
  const [badDays, setBadDays] = useState<BadDaysResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      if (!apiKey) return
      setError('')
      try {
        const [kpiRes, leaderboardRes, badDaysRes] = await Promise.all([
          getDriverKpis(apiKey, period),
          getLeaderboard(apiKey, period),
          getBadDays(apiKey),
        ])
        if (!active) return
        setKpis(kpiRes)
        setLeaderboard(leaderboardRes)
        setBadDays(badDaysRes)
      } catch (err) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load data')
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [apiKey, period])

  const avgUbpk = useMemo(() => {
    const drivers = kpis?.drivers ?? []
    if (!drivers.length) return 0
    return drivers.reduce((sum, driver) => sum + driver.ubpk, 0) / drivers.length
  }, [kpis])

  return (
    <AppShell
      eyebrow="Insurance Intelligence"
      title="Partner Dashboard"
      subtitle="Assess risk exposure across your insured drivers."
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
      {error && <div className="panel panel--wide">{error}</div>}
      <section className="kpi-grid">
        <article className="card">
          <p className="card__label">Avg UBPK</p>
          <p className="card__value">{avgUbpk.toFixed(2)}</p>
          <p className="card__detail">Across insured drivers</p>
        </article>
        <article className="card">
          <p className="card__label">Drivers</p>
          <p className="card__value">{kpis?.drivers.length ?? '--'}</p>
          <p className="card__detail">In partner cohort</p>
        </article>
        <article className="card">
          <p className="card__label">Bad Days</p>
          <p className="card__value">
            {badDays?.drivers.reduce((sum, item) => sum + item.bad_days, 0) ?? '--'}
          </p>
          <p className="card__detail">Above 75th percentile</p>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Best Drivers</h2>
            <span className="panel__meta">Lowest UBPK</span>
          </div>
          {leaderboard?.best?.map((entry) => (
            <div className="leaderboard__row" key={entry.driverProfileId}>
              <span>Driver {shortId(entry.driverProfileId)}</span>
              <span className="leaderboard__score">{entry.ubpk.toFixed(2)}</span>
              <span className="leaderboard__delta down">stable</span>
            </div>
          ))}
        </article>
        <article className="panel">
          <div className="panel__header">
            <h2>Needs Review</h2>
            <span className="panel__meta">Highest UBPK</span>
          </div>
          {leaderboard?.worst?.map((entry) => (
            <div className="leaderboard__row" key={entry.driverProfileId}>
              <span>Driver {shortId(entry.driverProfileId)}</span>
              <span className="leaderboard__score">{entry.ubpk.toFixed(2)}</span>
              <span className="leaderboard__delta up">watch</span>
            </div>
          ))}
        </article>
      </section>
    </AppShell>
  )
}
