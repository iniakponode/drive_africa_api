import { useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  apiFetchBlob,
  getInsuranceAggregateReport,
  getInsuranceDriverReport,
} from '../../lib/api'
import type {
  FleetReportResponse,
  InsuranceAggregateReport,
} from '../../lib/types'

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

export function InsuranceReports() {
  const { apiKey, profile } = useAuth()
  const [partnerId, setPartnerId] = useState('')
  const [partnerLabel, setPartnerLabel] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [aggregate, setAggregate] = useState<InsuranceAggregateReport | null>(
    null,
  )
  const [driverId, setDriverId] = useState('')
  const [driverReport, setDriverReport] = useState<FleetReportResponse | null>(
    null,
  )
  const [loadingAggregate, setLoadingAggregate] = useState(false)
  const [loadingDriver, setLoadingDriver] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  const handleAggregateLoad = async () => {
    if (!apiKey) return
    setLoadingAggregate(true)
    setError('')
    try {
      const data = await getInsuranceAggregateReport(apiKey, {
        partnerId: partnerId || undefined,
        partnerLabel: partnerLabel || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
      })
      setAggregate(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report')
    } finally {
      setLoadingAggregate(false)
    }
  }

  const handleAggregateDownload = async () => {
    if (!apiKey) return
    setDownloading(true)
    setError('')
    const params = new URLSearchParams()
    if (partnerId) params.set('partnerId', partnerId)
    if (partnerLabel) params.set('partnerLabel', partnerLabel)
    if (startDate) params.set('startDate', startDate)
    if (endDate) params.set('endDate', endDate)
    const suffix = params.toString() ? `?${params}` : ''
    try {
      const blob = await apiFetchBlob(
        `/api/insurance/reports/aggregate/download${suffix}`,
        apiKey,
      )
      const filename = partnerLabel
        ? `insurance_aggregate_${partnerLabel}.json`
        : 'insurance_aggregate_report.json'
      downloadBlob(blob, filename)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to download report',
      )
    } finally {
      setDownloading(false)
    }
  }

  const handleDriverLoad = async () => {
    if (!apiKey || !driverId) {
      setError('Provide a driverProfileId to load driver report.')
      return
    }
    setLoadingDriver(true)
    setError('')
    try {
      const data = await getInsuranceDriverReport(apiKey, driverId)
      setDriverReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load driver report')
    } finally {
      setLoadingDriver(false)
    }
  }

  const handleDriverDownload = async () => {
    if (!apiKey || !driverId) return
    setDownloading(true)
    setError('')
    try {
      const blob = await apiFetchBlob(
        `/api/insurance/reports/${driverId}/download`,
        apiKey,
      )
      downloadBlob(blob, `insurance_report_${driverId}.json`)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to download driver report',
      )
    } finally {
      setDownloading(false)
    }
  }

  const aggregateTop = useMemo(() => {
    return aggregate?.drivers.slice(0, 10) ?? []
  }, [aggregate])

  return (
    <AppShell
      eyebrow="Reports"
      title="Insurance Reports"
      subtitle="Aggregate summaries and driver-level reports."
      actions={
        <button
          className="cta"
          onClick={handleAggregateDownload}
          disabled={downloading}
        >
          {downloading ? 'Downloading...' : 'Download Aggregate'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Aggregate Filters</h2>
          <span className="panel__meta">
            {profile?.role === 'insurance_partner'
              ? 'Partner scope is enforced by API key.'
              : 'Optional partner scope for admin.'}
          </span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Partner ID"
            value={partnerId}
            onChange={(event) => setPartnerId(event.target.value)}
          />
          <input
            className="login__input"
            placeholder="Partner Label"
            value={partnerLabel}
            onChange={(event) => setPartnerLabel(event.target.value)}
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
          <button
            className="cta"
            onClick={handleAggregateLoad}
            disabled={loadingAggregate}
          >
            {loadingAggregate ? 'Loading...' : 'Load Aggregate'}
          </button>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      {aggregate && (
        <>
          <section className="kpi-grid">
            <article className="card">
              <p className="card__label">Drivers</p>
              <p className="card__value">{aggregate.total_drivers}</p>
              <p className="card__detail">In partner scope</p>
            </article>
            <article className="card">
              <p className="card__label">Trips</p>
              <p className="card__value">{aggregate.total_trips}</p>
              <p className="card__detail">Total trips</p>
            </article>
            <article className="card">
              <p className="card__label">Unsafe Events</p>
              <p className="card__value">{aggregate.total_unsafe_events}</p>
              <p className="card__detail">Across all drivers</p>
            </article>
            <article className="card">
              <p className="card__label">Speeding Events</p>
              <p className="card__value">{aggregate.total_speeding_events}</p>
              <p className="card__detail">Speed limit violations</p>
            </article>
          </section>

          <section className="panel panel--wide">
            <div className="panel__header">
              <h2>Driver Summary</h2>
              <span className="panel__meta">Top unsafe counts</span>
            </div>
            <div className="table">
              <div className="table__row table__row--header">
                <span>Driver</span>
                <span>Trips</span>
                <span>Distance</span>
                <span>Unsafe</span>
                <span>Avg Severity</span>
                <span>Speeding</span>
                <span>Alcohol</span>
              </div>
              {aggregateTop.map((driver) => (
                <div className="table__row" key={driver.driverProfileId}>
                  <span>{driver.driverProfileId.slice(0, 8)}</span>
                  <span>{driver.trip_count}</span>
                  <span>{driver.distance_km.toFixed(1)} km</span>
                  <span>{driver.unsafe_count}</span>
                  <span>{driver.avg_severity.toFixed(2)}</span>
                  <span>{driver.speeding_events}</span>
                  <span>{driver.alcohol_positive}</span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Driver Report</h2>
          <span className="panel__meta">Detailed driver report</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={driverId}
            onChange={(event) => setDriverId(event.target.value)}
          />
          <button className="cta" onClick={handleDriverLoad} disabled={loadingDriver}>
            {loadingDriver ? 'Loading...' : 'Load Driver Report'}
          </button>
          <button
            className="ghost ghost--light"
            onClick={handleDriverDownload}
            disabled={downloading || !driverId}
          >
            Download Driver JSON
          </button>
        </div>
      </section>

      {driverReport && (
        <section className="grid">
          <article className="panel">
            <div className="panel__header">
              <h2>Summary</h2>
              <span className="panel__meta">Driver report metrics</span>
            </div>
            <div className="kv">
              <div className="kv__row">
                <span className="kv__label">Trips</span>
                <span className="kv__value">{driverReport.trips.length}</span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Unsafe Logs</span>
                <span className="kv__value">
                  {driverReport.unsafe_behaviour_logs.length}
                </span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Speed Compliance</span>
                <span className="kv__value">
                  {(driverReport.speed_compliance.compliance_ratio * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </article>

          <article className="panel panel--wide">
            <div className="panel__header">
              <h2>Trip Summaries</h2>
              <span className="panel__meta">Distance and severity</span>
            </div>
            <div className="table">
              <div className="table__row table__row--header">
                <span>Trip</span>
                <span>Distance</span>
                <span>Unsafe</span>
                <span>Avg Severity</span>
                <span>Speeding</span>
              </div>
              {driverReport.trips.map((trip) => (
                <div className="table__row" key={trip.trip_id}>
                  <span>{trip.trip_id.slice(0, 8)}</span>
                  <span>{trip.distance_km.toFixed(1)} km</span>
                  <span>{trip.unsafe_count}</span>
                  <span>{trip.avg_severity.toFixed(2)}</span>
                  <span>{trip.speeding_events}</span>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}
    </AppShell>
  )
}
