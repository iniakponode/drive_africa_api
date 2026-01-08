import { useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  apiFetchBlob,
  getResearcherAggregateSnapshot,
} from '../../lib/api'
import type { AggregatedSnapshotResponse } from '../../lib/types'

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

function buildQuery(params: Record<string, string>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (!value) return
    search.set(key, value)
  })
  const query = search.toString()
  return query ? `?${query}` : ''
}

export function ResearcherSnapshots() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [week, setWeek] = useState('')
  const [snapshot, setSnapshot] = useState<AggregatedSnapshotResponse | null>(
    null,
  )
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  const filters = {
    driverProfileId: driverId,
    startDate,
    endDate,
    week,
  }

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getResearcherAggregateSnapshot(apiKey, filters)
      setSnapshot(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load snapshot')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!apiKey) return
    setDownloading(true)
    setError('')
    try {
      const query = buildQuery(filters)
      const blob = await apiFetchBlob(
        `/api/researcher/snapshots/aggregate/download${query}`,
        apiKey,
      )
      downloadBlob(blob, 'researcher_aggregate_snapshot.json')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download snapshot')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Snapshots"
      title="Aggregate Snapshot"
      subtitle="UBPK, unsafe behaviours, and raw sensor summaries in one view."
      actions={
        <button className="cta" onClick={handleDownload} disabled={downloading}>
          {downloading ? 'Downloading...' : 'Download JSON'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Filters</h2>
          <span className="panel__meta">Refine snapshot window</span>
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
            placeholder="Week (YYYY-Www)"
            value={week}
            onChange={(event) => setWeek(event.target.value)}
          />
          <button className="cta" onClick={handleLoad} disabled={loading}>
            {loading ? 'Loading...' : 'Load Snapshot'}
          </button>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      {snapshot && (
        <section className="grid">
          <article className="panel">
            <div className="panel__header">
              <h2>UBPK Coverage</h2>
              <span className="panel__meta">Driver vs trip metrics</span>
            </div>
            <div className="kv">
              <div className="kv__row">
                <span className="kv__label">Drivers</span>
                <span className="kv__value">{snapshot.ubpk_per_driver.length}</span>
              </div>
              <div className="kv__row">
                <span className="kv__label">Trips</span>
                <span className="kv__value">{snapshot.ubpk_per_trip.length}</span>
              </div>
            </div>
          </article>

          <article className="panel">
            <div className="panel__header">
              <h2>Unsafe Summary</h2>
              <span className="panel__meta">Top behaviours</span>
            </div>
            <div className="stack">
              {snapshot.unsafe_behaviour_summary.slice(0, 5).map((item) => (
                <div className="stack__row" key={item.behaviour_type}>
                  <div>
                    <p className="stack__title">{item.behaviour_type}</p>
                    <p className="stack__meta">{item.total} events</p>
                  </div>
                  <span className="tag tag--warn">
                    {item.avg_severity.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </article>

          <article className="panel panel--wide">
            <div className="panel__header">
              <h2>Raw Sensor Summary</h2>
              <span className="panel__meta">Sensor coverage</span>
            </div>
            <div className="table">
              <div className="table__row table__row--header">
                <span>Sensor</span>
                <span>Type</span>
                <span>Total</span>
                <span>Avg Accuracy</span>
              </div>
              {snapshot.raw_sensor_summary.map((sensor) => (
                <div className="table__row" key={sensor.sensor_type}>
                  <span>{sensor.sensor_type_name}</span>
                  <span>{sensor.sensor_type}</span>
                  <span>{sensor.total}</span>
                  <span>{sensor.avg_accuracy.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}
    </AppShell>
  )
}
