import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  createDriverProfile,
  getDriverProfile,
  updateDriverProfile,
} from '../../lib/api'
import type { DriverProfileResponse } from '../../lib/types'

function generateUuid() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return ''
}

export function DriverProfilePage() {
  const { apiKey, profile } = useAuth()
  const [driverId, setDriverId] = useState('')
  const [email, setEmail] = useState('')
  const [sync, setSync] = useState(false)
  const [loadedProfile, setLoadedProfile] = useState<DriverProfileResponse | null>(
    null,
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (profile?.driverProfileId) {
      setDriverId(profile.driverProfileId)
    }
  }, [profile?.driverProfileId])

  const handleLoad = async () => {
    if (!apiKey || !driverId) return
    setLoading(true)
    setError('')
    try {
      const data = await getDriverProfile(apiKey, driverId)
      setLoadedProfile(data)
      setEmail(data.email)
      setSync(data.sync)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!apiKey) return
    if (!driverId || !email) {
      setError('DriverProfileId and email are required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await createDriverProfile(apiKey, {
        driverProfileId: driverId,
        email,
        sync,
      })
      setLoadedProfile(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create profile')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!apiKey || !driverId) return
    if (!email) {
      setError('Email is required for update.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await updateDriverProfile(apiKey, driverId, { email, sync })
      setLoadedProfile(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const allowEditId = profile?.role === 'admin' || !profile?.driverProfileId

  return (
    <AppShell
      eyebrow="Driver"
      title="Profile"
      subtitle="Create or update your driver profile."
      actions={
        <button className="cta" onClick={handleLoad} disabled={loading}>
          {loading ? 'Loading...' : 'Load Profile'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Profile Details</h2>
          <span className="panel__meta">Driver scope enforced by API key.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={driverId}
            onChange={(event) => setDriverId(event.target.value)}
            disabled={!allowEditId}
          />
          {allowEditId && (
            <button
              className="ghost ghost--light"
              onClick={() => setDriverId(generateUuid())}
              type="button"
            >
              Generate ID
            </button>
          )}
          <input
            className="login__input"
            placeholder="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <label className="toggle">
            <input
              type="checkbox"
              checked={sync}
              onChange={(event) => setSync(event.target.checked)}
            />
            Sync
          </label>
          <button className="cta" onClick={handleCreate} disabled={loading}>
            Create
          </button>
          <button className="ghost ghost--light" onClick={handleUpdate} disabled={loading}>
            Update
          </button>
        </div>
        {loadedProfile && (
          <p className="panel__meta">
            Loaded profile {loadedProfile.driverProfileId}
          </p>
        )}
        {error && <p className="login__error">{error}</p>}
      </section>
    </AppShell>
  )
}
