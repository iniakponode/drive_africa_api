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

function buildQuery(params: Record<string, string>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (!value) return
    search.set(key, value)
  })
  const query = search.toString()
  return query ? `?${query}` : ''
}

export function ResearcherExports() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [week, setWeek] = useState('')
  const [format, setFormat] = useState<ExportFormat>('jsonl')
  const [loading, setLoading] = useState('')
  const [error, setError] = useState('')

  const exportFilters = {
    driverProfileId: driverId,
    startDate,
    endDate,
    week,
    format,
  }

  const handleDownload = async (path: string, filename: string) => {
    if (!apiKey) return
    setLoading(path)
    setError('')
    try {
      const query = buildQuery(exportFilters)
      const blob = await apiFetchBlob(`${path}${query}`, apiKey)
      downloadBlob(blob, filename)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export data')
    } finally {
      setLoading('')
    }
  }

  return (
    <AppShell
      eyebrow="Exports"
      title="Researcher Exports"
      subtitle="Download research datasets in CSV or JSONL."
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

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>NLG Reports</h2>
            <span className="panel__meta">Narrative summaries</span>
          </div>
          <button
            className="cta"
            onClick={() =>
              handleDownload(
                '/api/researcher/nlg_reports/export',
                `nlg_reports.${format}`,
              )
            }
            disabled={loading !== ''}
          >
            {loading ? 'Downloading...' : 'Download'}
          </button>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Raw Sensor Data</h2>
            <span className="panel__meta">Telematics streams</span>
          </div>
          <button
            className="cta"
            onClick={() =>
              handleDownload(
                '/api/researcher/raw_sensor_data/export',
                `raw_sensor_data.${format}`,
              )
            }
            disabled={loading !== ''}
          >
            {loading ? 'Downloading...' : 'Download'}
          </button>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Trips</h2>
            <span className="panel__meta">Trip metadata + alcohol matches</span>
          </div>
          <button
            className="cta"
            onClick={() =>
              handleDownload(
                '/api/researcher/trips/export',
                `trips.${format}`,
              )
            }
            disabled={loading !== ''}
          >
            {loading ? 'Downloading...' : 'Download'}
          </button>
        </article>
      </section>
    </AppShell>
  )
}
