import { useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { apiFetchBlob } from '../../lib/api'

type ExportFormat = 'jsonl' | 'csv'

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

export function InsuranceRawExport() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [tripId, setTripId] = useState('')
  const [startTimestamp, setStartTimestamp] = useState('')
  const [endTimestamp, setEndTimestamp] = useState('')
  const [format, setFormat] = useState<ExportFormat>('jsonl')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleDownload = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    const params = new URLSearchParams()
    if (driverId) params.set('driverProfileId', driverId)
    if (tripId) params.set('tripId', tripId)
    if (startTimestamp) params.set('startTimestamp', startTimestamp)
    if (endTimestamp) params.set('endTimestamp', endTimestamp)
    params.set('format', format)
    const suffix = params.toString() ? `?${params}` : ''
    try {
      const blob = await apiFetchBlob(
        `/api/insurance/raw_sensor_data/export${suffix}`,
        apiKey,
      )
      downloadBlob(blob, `insurance_raw_sensor_data.${format}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download export')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Insurance"
      title="Raw Sensor Export"
      subtitle="Download raw telematics streams for insured drivers."
      actions={
        <button className="cta" onClick={handleDownload} disabled={loading}>
          {loading ? 'Downloading...' : 'Download'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Export Filters</h2>
          <span className="panel__meta">All fields optional</span>
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
            placeholder="Trip ID"
            value={tripId}
            onChange={(event) => setTripId(event.target.value)}
          />
          <input
            className="login__input"
            placeholder="Start Timestamp (ms)"
            value={startTimestamp}
            onChange={(event) => setStartTimestamp(event.target.value)}
          />
          <input
            className="login__input"
            placeholder="End Timestamp (ms)"
            value={endTimestamp}
            onChange={(event) => setEndTimestamp(event.target.value)}
          />
          <select
            className="login__input"
            value={format}
            onChange={(event) => setFormat(event.target.value as ExportFormat)}
          >
            <option value="jsonl">JSONL</option>
            <option value="csv">CSV</option>
          </select>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>
    </AppShell>
  )
}
