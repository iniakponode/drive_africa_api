import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  getBadDays,
  getDriverUbpkSeries,
  getLeaderboard,
} from '../../lib/api'
import type {
  BadDaysResponse,
  DriverUBPKSeriesResponse,
  LeaderboardResponse,
} from '../../lib/types'

const PERIODS = ['day', 'week', 'month'] as const

function shortId(value?: string | null) {
  if (!value) return '----'
  return value.slice(0, 6).toUpperCase()
}

export function DriverDashboard() {
  const { apiKey, profile } = useAuth()
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>('week')
  const [series, setSeries] = useState<DriverUBPKSeriesResponse | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null)
  const [badDays, setBadDays] = useState<BadDaysResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      if (!apiKey) return
      setError('')
      try {
        const [seriesRes, leaderboardRes, badDaysRes] = await Promise.all([
          getDriverUbpkSeries(apiKey, period, profile?.driverProfileId ?? undefined),
          getLeaderboard(apiKey, period),
          getBadDays(apiKey),
        ])
        if (!active) return
        setSeries(seriesRes)
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
  }, [apiKey, period, profile?.driverProfileId])

  const latest = series?.series[series.series.length - 1]
  const badDayEntry = badDays?.drivers.find(
    (driver) => driver.driverProfileId === profile?.driverProfileId,
  )

  const bars = useMemo(() => {
    const items = series?.series.slice(-6) ?? []
    const max = Math.max(...items.map((item) => item.ubpk), 1)
    return items.map((item) => ({
      label: item.period_start.slice(5, 10),
      value: item.ubpk,
      height: Math.round((item.ubpk / max) * 100),
    }))
  }, [series])

  return (
    <AppShell
      eyebrow="Driver Scorecard"
      title="Your Safety Snapshot"
      subtitle="Review UBPK trends and peer ranking within your fleet."
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
          <p className="card__label">Current UBPK</p>
          <p className="card__value">
            {latest ? latest.ubpk.toFixed(2) : '--'}
          </p>
          <p className="card__detail">Unsafe behaviours per km</p>
        </article>
        <article className="card">
          <p className="card__label">Bad Days</p>
          <p className="card__value">{badDayEntry?.bad_days ?? '--'}</p>
          <p className="card__detail">Above 75th percentile delta</p>
        </article>
        <article className="card">
          <p className="card__label">Peer Rank</p>
          <p className="card__value">{leaderboard?.total_drivers ?? '--'}</p>
          <p className="card__detail">Peers in leaderboard</p>
        </article>
        <article className="card">
          <p className="card__label">Driver ID</p>
          <p className="card__value">{shortId(profile?.driverProfileId)}</p>
          <p className="card__detail">Profile scope</p>
        </article>
      </section>

      <section className="grid">
        <article className="panel panel--wide">
          <div className="panel__header">
            <h2>UBPK Trend</h2>
            <span className="panel__meta">Last 6 periods</span>
          </div>
          <div className="trend">
            {bars.map((bar) => (
              <div className="trend__item" key={bar.label}>
                <div className="trend__bar" style={{ height: `${bar.height}%` }} />
                <span>{bar.label}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Fleet Leaders</h2>
            <span className="panel__meta">Top UBPK performers</span>
          </div>
          <div className="leaderboard">
            <div>
              {leaderboard?.best?.map((entry) => (
                <div className="leaderboard__row" key={entry.driverProfileId}>
                  <span>Driver {shortId(entry.driverProfileId)}</span>
                  <span className="leaderboard__score">
                    {entry.ubpk.toFixed(2)}
                  </span>
                  <span className="leaderboard__delta down">best</span>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Needs Attention</h2>
            <span className="panel__meta">Highest UBPK</span>
          </div>
          <div className="leaderboard">
            <div>
              {leaderboard?.worst?.map((entry) => (
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
      </section>
    </AppShell>
  )
}
