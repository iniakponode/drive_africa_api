import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getDrivingTips, getNlgReports } from '../../lib/api'
import type { DrivingTip, NlgReport } from '../../lib/types'

export function DriverTips() {
  const { apiKey, profile } = useAuth()
  const [limit, setLimit] = useState(10)
  const [driverId, setDriverId] = useState('')
  const [tips, setTips] = useState<DrivingTip[]>([])
  const [reports, setReports] = useState<NlgReport[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (profile?.driverProfileId) {
      setDriverId(profile.driverProfileId)
    }
  }, [profile?.driverProfileId])

  const queryDriverId = useMemo(() => {
    if (profile?.role === 'admin') {
      return driverId || undefined
    }
    return profile?.driverProfileId ?? undefined
  }, [driverId, profile?.driverProfileId, profile?.role])

  const loadTips = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const [tipsRes, reportsRes] = await Promise.all([
        getDrivingTips(apiKey, {
          limit,
          profile_id: queryDriverId,
        }),
        getNlgReports(apiKey, {
          limit,
          driverProfileId: queryDriverId,
        }),
      ])
      setTips(tipsRes)
      setReports(reportsRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tips')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadTips()
  }, [apiKey, limit, queryDriverId])

  return (
    <AppShell
      eyebrow="Coaching"
      title="Tips and Reports"
      subtitle="Personalized driving tips and AI-generated summaries."
      actions={
        <button className="cta" onClick={loadTips} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Filters</h2>
          <span className="panel__meta">Limit and driver scope</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            type="number"
            min={1}
            max={50}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
          {profile?.role === 'admin' && (
            <input
              className="login__input"
              placeholder="Driver Profile ID"
              value={driverId}
              onChange={(event) => setDriverId(event.target.value)}
            />
          )}
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Driving Tips</h2>
            <span className="panel__meta">{tips.length} tips</span>
          </div>
          <div className="stack">
            {tips.length ? (
              tips.map((tip) => (
                <div className="stack__row" key={tip.tip_id}>
                  <div>
                    <p className="stack__title">{tip.title}</p>
                    <p className="stack__meta">
                      {tip.summary_tip ?? tip.meaning ?? 'No summary'}
                    </p>
                  </div>
                  <span className="tag tag--good">
                    {tip.llm ?? 'Manual'}
                  </span>
                </div>
              ))
            ) : (
              <p className="panel__meta">No tips available.</p>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>NLG Reports</h2>
            <span className="panel__meta">{reports.length} reports</span>
          </div>
          <div className="stack">
            {reports.length ? (
              reports.map((report) => (
                <div className="stack__row" key={report.id}>
                  <div>
                    <p className="stack__title">Report {report.id.slice(0, 6)}</p>
                    <p className="stack__meta">
                      {report.report_text.slice(0, 120)}...
                    </p>
                  </div>
                  <span className="tag tag--warn">
                    {new Date(report.generated_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            ) : (
              <p className="panel__meta">No reports available.</p>
            )}
          </div>
        </article>
      </section>
    </AppShell>
  )
}
