import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  batchCreateDriverProfiles,
  createDriverProfile,
  getDriverProfiles,
  updateDriverProfile,
} from '../../lib/api'
import type { DriverProfileResponse } from '../../lib/types'
import { getRowValue, parseCsvRecords } from '../../lib/csv'

function generateUuid() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return ''
}

export function AdminDriverProfiles() {
  const { apiKey } = useAuth()
  const [profiles, setProfiles] = useState<DriverProfileResponse[]>([])
  const [limit, setLimit] = useState(50)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [created, setCreated] = useState<DriverProfileResponse | null>(null)
  const [bulkResult, setBulkResult] = useState('')

  const [createForm, setCreateForm] = useState({
    driverProfileId: '',
    email: '',
    sync: false,
  })

  const [updateForm, setUpdateForm] = useState({
    driverProfileId: '',
    email: '',
    sync: '',
  })

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getDriverProfiles(apiKey, { limit })
      setProfiles(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profiles')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void handleLoad()
  }, [apiKey, limit])

  const handleCreate = async () => {
    if (!apiKey) return
    if (!createForm.driverProfileId || !createForm.email) {
      setError('DriverProfileId and email are required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await createDriverProfile(apiKey, {
        driverProfileId: createForm.driverProfileId,
        email: createForm.email,
        sync: createForm.sync,
      })
      setCreated(data)
      setCreateForm({ driverProfileId: '', email: '', sync: false })
      await handleLoad()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create profile')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!apiKey) return
    if (!updateForm.driverProfileId) {
      setError('Provide the driverProfileId to update.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload: { email?: string; sync?: boolean } = {}
      if (updateForm.email) payload.email = updateForm.email
      if (updateForm.sync) payload.sync = updateForm.sync === 'true'
      if (Object.keys(payload).length === 0) {
        setError('Provide at least one field to update.')
        setLoading(false)
        return
      }
      await updateDriverProfile(apiKey, updateForm.driverProfileId, payload)
      setUpdateForm({ driverProfileId: '', email: '', sync: '' })
      await handleLoad()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const handleBulkCreate = async (file: File | null) => {
    if (!apiKey || !file) return
    setBulkResult('')
    setLoading(true)
    setError('')
    try {
      const text = await file.text()
      const { rows } = parseCsvRecords(text)
      const errors: string[] = []
      const payload = rows
        .map((row, index) => {
          const driverProfileId = getRowValue(row, ['driverProfileId'])
          const email = getRowValue(row, ['email'])
          const syncValue = getRowValue(row, ['sync'])
          if (!driverProfileId || !email) {
            errors.push(`Row ${index + 2}: missing driverProfileId or email`)
            return null
          }
          const sync = syncValue
            ? ['true', '1', 'yes'].includes(syncValue.toLowerCase())
            : undefined
          return { driverProfileId, email, sync }
        })
        .filter(
          (row): row is { driverProfileId: string; email: string; sync?: boolean } =>
            Boolean(row),
        )
      if (!payload.length) {
        setError('CSV has no valid rows.')
        setLoading(false)
        return
      }
      const result = await batchCreateDriverProfiles(apiKey, payload)
      const combinedErrors = [...errors, ...(result.errors ?? [])]
      const processed = (result.created ?? 0) + (result.updated ?? 0)
      setBulkResult(
        `Processed ${processed}/${payload.length} profiles (created ${result.created ?? 0}, updated ${result.updated ?? 0}).${result.skipped ? ` Skipped: ${result.skipped}` : ''}${combinedErrors.length ? ` Errors: ${combinedErrors.length}` : ''}`,
      )
      if (combinedErrors.length) {
        setError(combinedErrors.slice(0, 5).join(' | '))
      }
      await handleLoad()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bulk create failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Admin"
      title="Driver Profiles"
      subtitle="Manage driver identities and sync status."
      actions={
        <button className="cta" onClick={handleLoad} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Create Driver Profile</h2>
          <span className="panel__meta">UUID is required.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={createForm.driverProfileId}
            onChange={(event) =>
              setCreateForm({
                ...createForm,
                driverProfileId: event.target.value,
              })
            }
          />
          <button
            className="ghost ghost--light"
            onClick={() =>
              setCreateForm({
                ...createForm,
                driverProfileId: generateUuid(),
              })
            }
            type="button"
          >
            Generate ID
          </button>
          <input
            className="login__input"
            placeholder="Email"
            value={createForm.email}
            onChange={(event) =>
              setCreateForm({ ...createForm, email: event.target.value })
            }
          />
          <label className="toggle">
            <input
              type="checkbox"
              checked={createForm.sync}
              onChange={(event) =>
                setCreateForm({ ...createForm, sync: event.target.checked })
              }
            />
            Sync
          </label>
          <button className="cta" onClick={handleCreate} disabled={loading}>
            Create Profile
          </button>
        </div>
        {created && (
          <p className="panel__meta">
            Created {created.email} ({created.driverProfileId})
          </p>
        )}
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Update Profile</h2>
          <span className="panel__meta">Provide only fields to change.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={updateForm.driverProfileId}
            onChange={(event) =>
              setUpdateForm({
                ...updateForm,
                driverProfileId: event.target.value,
              })
            }
          />
          <input
            className="login__input"
            placeholder="Email"
            value={updateForm.email}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, email: event.target.value })
            }
          />
          <select
            className="login__input"
            value={updateForm.sync}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, sync: event.target.value })
            }
          >
            <option value="">Sync (unchanged)</option>
            <option value="true">Synced</option>
            <option value="false">Unsynced</option>
          </select>
          <button className="cta" onClick={handleUpdate} disabled={loading}>
            Update Profile
          </button>
        </div>
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Bulk Create (CSV)</h2>
          <span className="panel__meta">
            Columns: driverProfileId, email, sync
          </span>
        </div>
        <input
          className="login__input"
          type="file"
          accept=".csv"
          onChange={(event) =>
            handleBulkCreate(event.target.files ? event.target.files[0] : null)
          }
        />
        {bulkResult && <p className="panel__meta">{bulkResult}</p>}
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Profiles</h2>
          <span className="panel__meta">{profiles.length} records</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            type="number"
            min={1}
            max={5000}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
        </div>
        <div className="table">
          <div className="table__row table__row--header">
            <span>ID</span>
            <span>Email</span>
            <span>Sync</span>
          </div>
          {profiles.map((profile) => (
            <div className="table__row" key={profile.driverProfileId}>
              <span>{profile.driverProfileId.slice(0, 8)}</span>
              <span>{profile.email}</span>
              <span>{profile.sync ? 'Yes' : 'No'}</span>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  )
}
