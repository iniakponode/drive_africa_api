import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getCloudEndpoints, updateCloudEndpoints } from '../../lib/api'

export function AdminCloudEndpoints() {
  const { apiKey } = useAuth()
  const [form, setForm] = useState({
    road_limits_url: '',
    driving_tips_url: '',
    model_response_url: '',
  })
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
        const data = await getCloudEndpoints(apiKey)
        if (!active) return
        setForm({
          road_limits_url: data.road_limits_url ?? '',
          driving_tips_url: data.driving_tips_url ?? '',
          model_response_url: data.model_response_url ?? '',
        })
      } catch (err) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load endpoints')
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
    setLoading(true)
    setSaved(false)
    setError('')
    try {
      await updateCloudEndpoints(apiKey, {
        road_limits_url: form.road_limits_url || null,
        driving_tips_url: form.driving_tips_url || null,
        model_response_url: form.model_response_url || null,
      })
      setSaved(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update endpoints')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Admin"
      title="Cloud Endpoints"
      subtitle="Configure external data feeds consumed by the mobile clients."
      actions={
        <button className="cta" onClick={handleSave} disabled={loading}>
          {loading ? 'Saving...' : 'Save Endpoints'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Endpoint Configuration</h2>
          <span className="panel__meta">Optional URLs for sync services.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Road limits URL"
            value={form.road_limits_url}
            onChange={(event) =>
              setForm({ ...form, road_limits_url: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Driving tips URL"
            value={form.driving_tips_url}
            onChange={(event) =>
              setForm({ ...form, driving_tips_url: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Model response URL"
            value={form.model_response_url}
            onChange={(event) =>
              setForm({ ...form, model_response_url: event.target.value })
            }
          />
        </div>
        {saved && <p className="panel__meta">Saved.</p>}
        {error && <p className="login__error">{error}</p>}
      </section>
    </AppShell>
  )
}
