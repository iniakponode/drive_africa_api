import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getDatasetAccess, updateDatasetAccess } from '../../lib/api'
import type { DatasetAccessConfig } from '../../lib/types'

export function AdminDatasetAccess() {
  const { apiKey } = useAuth()
  const [raw, setRaw] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      if (!apiKey) return
      setLoading(true)
      setError('')
      try {
        const data = await getDatasetAccess(apiKey)
        if (!active) return
        setRaw(JSON.stringify(data, null, 2))
      } catch (err) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load dataset access')
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [apiKey])

  const handleSave = async () => {
    if (!apiKey) return
    setSaved(false)
    setError('')
    try {
      const parsed = JSON.parse(raw) as DatasetAccessConfig
      await updateDatasetAccess(apiKey, parsed)
      setSaved(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid JSON payload')
    }
  }

  return (
    <AppShell
      eyebrow="Admin"
      title="Dataset Access"
      subtitle="Control dataset visibility per role."
      actions={
        <button className="cta" onClick={handleSave} disabled={loading}>
          {loading ? 'Loading...' : 'Save Changes'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Access Policy JSON</h2>
          <span className="panel__meta">Edit with caution.</span>
        </div>
        <textarea
          className="login__input textarea"
          value={raw}
          onChange={(event) => setRaw(event.target.value)}
        />
        {saved && <p className="panel__meta">Saved.</p>}
        {error && <p className="login__error">{error}</p>}
      </section>
    </AppShell>
  )
}
