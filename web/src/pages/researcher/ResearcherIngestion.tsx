import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getResearcherIngestionStatus } from '../../lib/api'
import type { IngestionStatusResponse } from '../../lib/types'

export function ResearcherIngestion() {
  const { apiKey } = useAuth()
  const [status, setStatus] = useState<IngestionStatusResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      if (!apiKey) return
      setLoading(true)
      setError('')
      try {
        const data = await getResearcherIngestionStatus(apiKey)
        if (!active) return
        setStatus(data)
      } catch (err) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load ingestion')
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [apiKey])

  return (
    <AppShell
      eyebrow="Ingestion"
      title="Dataset Ingestion"
      subtitle="Track sync coverage across pipeline datasets."
    >
      {error && <div className="panel panel--wide">{error}</div>}

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Ingestion Status</h2>
          <span className="panel__meta">
            {loading ? 'Loading...' : status?.generated_at ?? 'Latest'}
          </span>
        </div>
        <div className="table">
          <div className="table__row table__row--header">
            <span>Dataset</span>
            <span>Total</span>
            <span>Synced</span>
            <span>Unsynced</span>
            <span>Latest Record</span>
          </div>
          {status?.datasets?.map((dataset) => (
            <div className="table__row" key={dataset.dataset}>
              <span>{dataset.dataset}</span>
              <span>{dataset.total}</span>
              <span>{dataset.synced}</span>
              <span>{dataset.unsynced}</span>
              <span>{dataset.latest_record_at ?? '--'}</span>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  )
}
