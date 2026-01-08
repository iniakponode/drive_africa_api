import { useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getFleetTripContext } from '../../lib/api'
import type { FleetTripContext } from '../../lib/types'

export function FleetTripContextView() {
  const { apiKey } = useAuth()
  const [tripId, setTripId] = useState('')
  const [context, setContext] = useState<FleetTripContext | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLoad = async () => {
    if (!apiKey) return
    if (!tripId) {
      setError('Provide a trip ID to load context.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await getFleetTripContext(apiKey, tripId)
      setContext(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trip context')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Fleet Coaching"
      title="Trip Context"
      subtitle="Tips, severity findings, and NLG reports for a trip."
      actions={
        <button className="cta" onClick={handleLoad} disabled={loading}>
          {loading ? 'Loading...' : 'Load Context'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Trip Lookup</h2>
          <span className="panel__meta">Enter a trip UUID</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Trip ID"
            value={tripId}
            onChange={(event) => setTripId(event.target.value)}
          />
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      {context && (
        <section className="grid">
          <article className="panel">
            <div className="panel__header">
              <h2>Driving Tips</h2>
              <span className="panel__meta">{context.tips.length} tips</span>
            </div>
            <div className="stack">
              {context.tips.length ? (
                context.tips.map((tip) => (
                  <div className="stack__row" key={tip.tip_id}>
                    <div>
                      <p className="stack__title">{tip.title}</p>
                      <p className="stack__meta">
                        {tip.summary_tip ?? 'No summary'}
                      </p>
                    </div>
                    <span className="tag tag--good">{tip.llm ?? 'Tip'}</span>
                  </div>
                ))
              ) : (
                <p className="panel__meta">No tips for this trip.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel__header">
              <h2>Severity Findings</h2>
              <span className="panel__meta">
                {context.severity_findings.length} findings
              </span>
            </div>
            <div className="stack">
              {context.severity_findings.length ? (
                context.severity_findings.map((finding) => (
                  <div className="stack__row" key={finding.id}>
                    <div>
                      <p className="stack__title">{finding.behaviour_type}</p>
                      <p className="stack__meta">
                        {new Date(finding.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <span className="tag tag--warn">
                      {finding.severity.toFixed(2)}
                    </span>
                  </div>
                ))
              ) : (
                <p className="panel__meta">No severity findings.</p>
              )}
            </div>
          </article>

          <article className="panel panel--wide">
            <div className="panel__header">
              <h2>NLG Reports</h2>
              <span className="panel__meta">
                {context.nlg_reports.length} reports
              </span>
            </div>
            <div className="stack">
              {context.nlg_reports.length ? (
                context.nlg_reports.map((report) => (
                  <div className="stack__row" key={report.id}>
                    <div>
                      <p className="stack__title">Report {report.id.slice(0, 6)}</p>
                      <p className="stack__meta">
                        {report.report_text.slice(0, 160)}...
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
      )}
    </AppShell>
  )
}
