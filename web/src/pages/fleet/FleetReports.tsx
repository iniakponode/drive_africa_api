import { useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { apiFetchBlob, getFleetReport } from '../../lib/api'
import type { FleetReportResponse } from '../../lib/types'

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function FleetReports() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [report, setReport] = useState<FleetReportResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  const handleLoad = async () => {
    if (!apiKey) return
    if (!driverId) {
      setError('Provide a driverProfileId to load reports.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await getFleetReport(apiKey, driverId)
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!apiKey || !driverId) return
    setDownloading(true)
    setError('')
    try {
      const blob = await apiFetchBlob(
        `/api/fleet/reports/${driverId}/download`,
        apiKey,
      )
      downloadBlob(blob, `fleet_report_${driverId}.json`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download report')
    } finally {
      setDownloading(false)
    }
  }

  const tripCount = report?.trips.length ?? 0
  const unsafeCount = report?.unsafe_behaviour_logs.length ?? 0
  const complianceRatio = report?.speed_compliance.compliance_ratio ?? 0

  return (
    <AppShell
      eyebrow="Compliance"
      title="Fleet Reports"
      subtitle="Driver-level reports with unsafe behaviours and trip summaries."
      actions={
        <button
          className="cta"
          onClick={handleDownload}
          disabled={!driverId || downloading}
        >
          {downloading ? 'Downloading...' : 'Download JSON'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Load Driver Report</h2>
          <span className="panel__meta">Latest report snapshot</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={driverId}
            onChange={(event) => setDriverId(event.target.value)}
          />
          <button className="cta" onClick={handleLoad} disabled={loading}>
            {loading ? 'Loading...' : 'Load Report'}
          </button>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      {report && (
        <>
          <section className="kpi-grid">
            <article className="card">
              <p className="card__label">Trips</p>
              <p className="card__value">{tripCount}</p>
              <p className="card__detail">Total trip records</p>
            </article>
            <article className="card">
              <p className="card__label">Unsafe Behaviours</p>
              <p className="card__value">{unsafeCount}</p>
              <p className="card__detail">Recent logs</p>
            </article>
            <article className="card">
              <p className="card__label">Speed Compliance</p>
              <p className="card__value">
                {(complianceRatio * 100).toFixed(1)}%
              </p>
              <p className="card__detail">Across all locations</p>
            </article>
            <article className="card">
              <p className="card__label">Report Generated</p>
              <p className="card__value">
                {new Date(report.report_generated_at).toLocaleDateString()}
              </p>
              <p className="card__detail">Most recent snapshot</p>
            </article>
          </section>

          <section className="grid">
            <article className="panel panel--wide">
              <div className="panel__header">
                <h2>Trip Summaries</h2>
                <span className="panel__meta">Distance and severity snapshot</span>
              </div>
              <div className="table">
                <div className="table__row table__row--header">
                  <span>Trip</span>
                  <span>Distance (km)</span>
                  <span>Unsafe Count</span>
                  <span>Avg Severity</span>
                  <span>Speeding</span>
                </div>
                {report.trips.map((trip) => (
                  <div className="table__row" key={trip.trip_id}>
                    <span>{trip.trip_id.slice(0, 8)}</span>
                    <span>{trip.distance_km.toFixed(2)}</span>
                    <span>{trip.unsafe_count}</span>
                    <span>{trip.avg_severity.toFixed(2)}</span>
                    <span>{trip.speeding_events}</span>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <div className="panel__header">
                <h2>Alcohol Responses</h2>
                <span className="panel__meta">Recent questionnaires</span>
              </div>
              <div className="stack">
                {report.alcohol_responses.length ? (
                  report.alcohol_responses.map((response) => (
                    <div className="stack__row" key={response.id}>
                      <div>
                        <p className="stack__title">
                          Impairment {response.impairmentLevel}
                        </p>
                        <p className="stack__meta">
                          {response.date
                            ? new Date(response.date).toLocaleDateString()
                            : 'Unknown date'}
                        </p>
                      </div>
                      <span
                        className={`tag ${
                          response.drankAlcohol ? 'tag--warn' : 'tag--good'
                        }`}
                      >
                        {response.drankAlcohol ? 'Drank' : 'No alcohol'}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="panel__meta">No questionnaire responses.</p>
                )}
              </div>
            </article>
          </section>
        </>
      )}
    </AppShell>
  )
}
