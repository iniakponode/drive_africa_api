import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getLeaderboard } from '../../lib/api'
import type { LeaderboardResponse } from '../../lib/types'

const PERIODS = ['day', 'week', 'month'] as const

function shortId(value: string) {
  return value.slice(0, 6).toUpperCase()
}

export function DriverLeaderboard() {
  const { apiKey, profile } = useAuth()
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>('week')
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      if (!apiKey) return
      setError('')
      try {
        const data = await getLeaderboard(apiKey, period)
        if (!active) return
        setLeaderboard(data)
      } catch (err) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load leaderboard')
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [apiKey, period])

  const driverId = profile?.driverProfileId

  return (
    <AppShell
      eyebrow="Peer Rank"
      title="Leaderboard"
      subtitle="Compare UBPK performance within your fleet or insurer."
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
      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Top Drivers</h2>
            <span className="panel__meta">
              {leaderboard?.total_drivers ?? '--'} peers
            </span>
          </div>
          <div className="leaderboard">
            <div>
              {leaderboard?.best?.map((entry) => (
                <div className="leaderboard__row" key={entry.driverProfileId}>
                  <span>
                    Driver {shortId(entry.driverProfileId)}
                    {entry.driverProfileId === driverId ? ' (You)' : ''}
                  </span>
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
                  <span>
                    Driver {shortId(entry.driverProfileId)}
                    {entry.driverProfileId === driverId ? ' (You)' : ''}
                  </span>
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
