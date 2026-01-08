import { useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  apiFetchBlob,
  backfillTripAlcohol,
  getResearcherAlcoholBundle,
} from '../../lib/api'
import type {
  ResearcherBackfillResponse,
  ResearcherTripAlcoholBundle,
} from '../../lib/types'

type BundleDataset = 'trips' | 'questionnaires' | 'unsafe_behaviours'

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

function toEpochMs(value: string, endOfDay = false) {
  if (!value) return undefined
  const parts = value.split('-').map((part) => Number(part))
  if (parts.length !== 3 || parts.some((part) => Number.isNaN(part))) {
    return undefined
  }
  const [year, month, day] = parts
  const date = endOfDay
    ? new Date(Date.UTC(year, month - 1, day, 23, 59, 59, 999))
    : new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0))
  return date.getTime()
}

export function ResearcherAlcoholBundle() {
  const { apiKey } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [week, setWeek] = useState('')
  const [skip, setSkip] = useState(0)
  const [limit, setLimit] = useState(100)
  const [overwrite, setOverwrite] = useState(false)
  const [bundle, setBundle] = useState<ResearcherTripAlcoholBundle | null>(null)
  const [backfill, setBackfill] = useState<ResearcherBackfillResponse | null>(
    null,
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getResearcherAlcoholBundle(apiKey, {
        driverProfileId: driverId || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        week: week || undefined,
        skip,
        limit,
      })
      setBundle(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bundle')
    } finally {
      setLoading(false)
    }
  }

  const handleBackfill = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await backfillTripAlcohol(apiKey, {
        driverProfileId: driverId || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        week: week || undefined,
        overwrite,
      })
      setBackfill(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to backfill')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadBundleCsv = async (dataset: BundleDataset) => {
    if (!apiKey) return
    const resolvedDriverId = driverId || bundle?.driverProfileId
    if (!resolvedDriverId) {
      setError('Driver Profile ID is required for CSV export.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams()
      params.set('dataset', dataset)
      const startTime = toEpochMs(startDate)
      const endTime = toEpochMs(endDate, true)
      if (startTime !== undefined) {
        params.set('start_time', String(startTime))
      }
      if (endTime !== undefined) {
        params.set('end_time', String(endTime))
      }
      const query = params.toString()
      const suffix = query ? `?${query}` : ''
      const blob = await apiFetchBlob(
        `/api/researcher/alcohol_bundle/${resolvedDriverId}/csv${suffix}`,
        apiKey,
      )
      downloadBlob(blob, `alcohol_bundle_${dataset}_${resolvedDriverId}.csv`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export bundle')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Research"
      title="Alcohol Trip Bundle"
      subtitle="Match alcohol questionnaires to trips and backfill responses."
      actions={
        <>
          <button className="cta" onClick={handleLoad} disabled={loading}>
            {loading ? 'Loading...' : 'Load Bundle'}
          </button>
          <button className="ghost ghost--light" onClick={handleBackfill} disabled={loading}>
            Run Backfill
          </button>
        </>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Filters</h2>
          <span className="panel__meta">Driver + date range</span>
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
          <input
            className="login__input"
            type="number"
            min={0}
            value={skip}
            onChange={(event) => setSkip(Number(event.target.value))}
          />
          <input
            className="login__input"
            type="number"
            min={1}
            max={5000}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
          <label className="toggle">
            <input
              type="checkbox"
              checked={overwrite}
              onChange={(event) => setOverwrite(event.target.checked)}
            />
            Overwrite
          </label>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      {bundle && (
        <section className="kpi-grid">
          <article className="card">
            <p className="card__label">Trips</p>
            <p className="card__value">{bundle.total_trips}</p>
            <p className="card__detail">Trips in scope</p>
          </article>
          <article className="card">
            <p className="card__label">Questionnaires</p>
            <p className="card__value">{bundle.total_questionnaires}</p>
            <p className="card__detail">Questionnaires in scope</p>
          </article>
          <article className="card">
            <p className="card__label">Matching Rule</p>
            <p className="card__value">{bundle.matchingRule}</p>
            <p className="card__detail">{bundle.matchingTimezone}</p>
          </article>
        </section>
      )}

      {bundle && (
        <section className="panel panel--wide">
          <div className="panel__header">
            <h2>Export Bundle (CSV)</h2>
            <span className="panel__meta">
              Download trip, questionnaire, and unsafe behaviour tables.
            </span>
          </div>
          <div className="form-row">
            <button className="cta" onClick={() => handleDownloadBundleCsv('trips')}>
              Download Trips CSV
            </button>
            <button
              className="ghost ghost--light"
              onClick={() => handleDownloadBundleCsv('questionnaires')}
            >
              Download Questionnaires CSV
            </button>
            <button
              className="ghost ghost--light"
              onClick={() => handleDownloadBundleCsv('unsafe_behaviours')}
            >
              Download Unsafe Behaviours CSV
            </button>
          </div>
        </section>
      )}

      {backfill && (
        <section className="panel panel--wide">
          <div className="panel__header">
            <h2>Backfill Results</h2>
            <span className="panel__meta">Latest run</span>
          </div>
          <div className="table">
            <div className="table__row table__row--header">
              <span>Total Trips</span>
              <span>Matched</span>
              <span>Updated</span>
              <span>Skipped</span>
              <span>Overwrite</span>
            </div>
            <div className="table__row">
              <span>{backfill.totalTrips}</span>
              <span>{backfill.matchedTrips}</span>
              <span>{backfill.updatedTrips}</span>
              <span>{backfill.skippedTripsNoDate}</span>
              <span>{backfill.overwrite ? 'Yes' : 'No'}</span>
            </div>
          </div>
        </section>
      )}

      {bundle && (
        <section className="grid">
          <article className="panel">
            <div className="panel__header">
              <h2>Trips (sample)</h2>
              <span className="panel__meta">First 5 trips</span>
            </div>
            <div className="stack">
              {bundle.trips.slice(0, 5).map((trip) => (
                <div className="stack__row" key={trip.id}>
                  <div>
                    <p className="stack__title">Trip {trip.id.slice(0, 6)}</p>
                    <p className="stack__meta">
                      {trip.tripNotes ?? 'No notes'}
                    </p>
                  </div>
                  <span className="tag tag--good">
                    {trip.matchedQuestionnaire ? 'Matched' : 'Unmatched'}
                  </span>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel__header">
              <h2>Questionnaires (sample)</h2>
              <span className="panel__meta">First 5 questionnaires</span>
            </div>
            <div className="stack">
              {bundle.questionnaires.slice(0, 5).map((item) => (
                <div className="stack__row" key={item.id}>
                  <div>
                    <p className="stack__title">Questionnaire {item.id.slice(0, 6)}</p>
                    <p className="stack__meta">
                      {new Date(item.date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="tag tag--warn">
                    {item.drankAlcohol ? 'Alcohol' : 'None'}
                  </span>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}
    </AppShell>
  )
}
