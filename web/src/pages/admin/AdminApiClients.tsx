import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  batchCreateApiClients,
  createApiClient,
  getApiClients,
  updateApiClient,
} from '../../lib/api'
import type { ApiClient, ApiClientCreated, Role } from '../../lib/types'
import { getRowValue, parseCsvRecords } from '../../lib/csv'

const ROLE_OPTIONS: Role[] = [
  'admin',
  'fleet_manager',
  'driver',
  'researcher',
  'insurance_partner',
]

function shortId(value: string) {
  return value.slice(0, 8)
}

export function AdminApiClients() {
  const { apiKey } = useAuth()
  const [clients, setClients] = useState<ApiClient[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [created, setCreated] = useState<ApiClientCreated | null>(null)
  const [bulkResult, setBulkResult] = useState('')

  const [createForm, setCreateForm] = useState({
    name: '',
    role: 'admin' as Role,
    active: true,
    driverProfileId: '',
    fleet_id: '',
    insurance_partner_id: '',
    api_key: '',
  })

  const [updateForm, setUpdateForm] = useState({
    id: '',
    name: '',
    role: '',
    active: '',
    driverProfileId: '',
    fleet_id: '',
    insurance_partner_id: '',
  })

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getApiClients(apiKey)
      setClients(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API clients')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void handleLoad()
  }, [apiKey])

  const handleCreate = async () => {
    if (!apiKey) return
    if (!createForm.name.trim()) {
      setError('Provide a client name.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload = {
        name: createForm.name.trim(),
        role: createForm.role,
        active: createForm.active,
        driverProfileId: createForm.driverProfileId || undefined,
        fleet_id: createForm.fleet_id || undefined,
        insurance_partner_id: createForm.insurance_partner_id || undefined,
        api_key: createForm.api_key || undefined,
      }
      const data = await createApiClient(apiKey, payload)
      setCreated(data)
      setCreateForm({
        name: '',
        role: 'admin',
        active: true,
        driverProfileId: '',
        fleet_id: '',
        insurance_partner_id: '',
        api_key: '',
      })
      await handleLoad()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API client')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!apiKey) return
    if (!updateForm.id.trim()) {
      setError('Provide the client ID to update.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload: Record<string, string | boolean> = {}
      if (updateForm.name) payload.name = updateForm.name
      if (updateForm.role) payload.role = updateForm.role
      if (updateForm.active) payload.active = updateForm.active === 'true'
      if (updateForm.driverProfileId) {
        payload.driverProfileId = updateForm.driverProfileId
      }
      if (updateForm.fleet_id) payload.fleet_id = updateForm.fleet_id
      if (updateForm.insurance_partner_id) {
        payload.insurance_partner_id = updateForm.insurance_partner_id
      }
      if (Object.keys(payload).length === 0) {
        setError('Provide at least one field to update.')
        setLoading(false)
        return
      }
      await updateApiClient(apiKey, updateForm.id, payload)
      setUpdateForm({
        id: '',
        name: '',
        role: '',
        active: '',
        driverProfileId: '',
        fleet_id: '',
        insurance_partner_id: '',
      })
      await handleLoad()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update API client')
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
          const name = getRowValue(row, ['name'])
          const role = getRowValue(row, ['role'])
          const activeValue = getRowValue(row, ['active'])
          const driverProfileId = getRowValue(row, ['driverProfileId'])
          const fleetId = getRowValue(row, ['fleet_id', 'fleetId'])
          const partnerId = getRowValue(row, [
            'insurance_partner_id',
            'insurancePartnerId',
          ])
          const apiKeyValue = getRowValue(row, ['api_key', 'apiKey'])
          if (!name || !role) {
            errors.push(`Row ${index + 2}: missing name or role`)
            return null
          }
          const active =
            activeValue === ''
              ? true
              : ['true', '1', 'yes'].includes(activeValue.toLowerCase())
          return {
            name,
            role,
            active,
            driverProfileId: driverProfileId || undefined,
            fleet_id: fleetId || undefined,
            insurance_partner_id: partnerId || undefined,
            api_key: apiKeyValue || undefined,
          }
        })
        .filter(
          (
            row,
          ): row is {
            name: string
            role: string
            active?: boolean
            driverProfileId?: string
            fleet_id?: string
            insurance_partner_id?: string
            api_key?: string
          } => Boolean(row),
        )
      if (!payload.length) {
        setError('CSV has no valid rows.')
        setLoading(false)
        return
      }
      const result = await batchCreateApiClients(apiKey, payload)
      const combinedErrors = [...errors, ...(result.errors ?? [])]
      setBulkResult(
        `Created ${result.created ?? 0}/${payload.length} API clients.${result.skipped ? ` Skipped: ${result.skipped}` : ''}${combinedErrors.length ? ` Errors: ${combinedErrors.length}` : ''}`,
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

  const clientRows = useMemo(() => clients, [clients])

  return (
    <AppShell
      eyebrow="Admin"
      title="API Clients"
      subtitle="Create and manage API keys for each role."
      actions={
        <button className="cta" onClick={handleLoad} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Create API Client</h2>
          <span className="panel__meta">Keys are shown once after creation.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Name"
            value={createForm.name}
            onChange={(event) =>
              setCreateForm({ ...createForm, name: event.target.value })
            }
          />
          <select
            className="login__input"
            value={createForm.role}
            onChange={(event) =>
              setCreateForm({ ...createForm, role: event.target.value as Role })
            }
          >
            {ROLE_OPTIONS.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
          <input
            className="login__input"
            placeholder="Driver Profile ID (optional)"
            value={createForm.driverProfileId}
            onChange={(event) =>
              setCreateForm({
                ...createForm,
                driverProfileId: event.target.value,
              })
            }
          />
          <input
            className="login__input"
            placeholder="Fleet ID (optional)"
            value={createForm.fleet_id}
            onChange={(event) =>
              setCreateForm({ ...createForm, fleet_id: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Insurance Partner ID (optional)"
            value={createForm.insurance_partner_id}
            onChange={(event) =>
              setCreateForm({
                ...createForm,
                insurance_partner_id: event.target.value,
              })
            }
          />
          <input
            className="login__input"
            placeholder="Custom API Key (optional)"
            value={createForm.api_key}
            onChange={(event) =>
              setCreateForm({ ...createForm, api_key: event.target.value })
            }
          />
          <label className="toggle">
            <input
              type="checkbox"
              checked={createForm.active}
              onChange={(event) =>
                setCreateForm({ ...createForm, active: event.target.checked })
              }
            />
            Active
          </label>
          <button className="cta" onClick={handleCreate} disabled={loading}>
            Create Client
          </button>
        </div>
        {created && (
          <div className="panel__meta">
            Created {created.name} ({created.role}) - API key:{' '}
            <strong>{created.api_key}</strong>
          </div>
        )}
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Update Client</h2>
          <span className="panel__meta">Provide only the fields to change.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Client ID"
            value={updateForm.id}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, id: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Name"
            value={updateForm.name}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, name: event.target.value })
            }
          />
          <select
            className="login__input"
            value={updateForm.role}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, role: event.target.value })
            }
          >
            <option value="">Role (unchanged)</option>
            {ROLE_OPTIONS.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
          <select
            className="login__input"
            value={updateForm.active}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, active: event.target.value })
            }
          >
            <option value="">Active (unchanged)</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={updateForm.driverProfileId}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, driverProfileId: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Fleet ID"
            value={updateForm.fleet_id}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, fleet_id: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Insurance Partner ID"
            value={updateForm.insurance_partner_id}
            onChange={(event) =>
              setUpdateForm({
                ...updateForm,
                insurance_partner_id: event.target.value,
              })
            }
          />
          <button className="cta" onClick={handleUpdate} disabled={loading}>
            Update Client
          </button>
        </div>
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Bulk Create (CSV)</h2>
          <span className="panel__meta">
            Columns: name, role, active, driverProfileId, fleet_id, insurance_partner_id, api_key
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
          <h2>Existing Clients</h2>
          <span className="panel__meta">{clientRows.length} clients</span>
        </div>
        <div className="table">
          <div className="table__row table__row--header">
            <span>ID</span>
            <span>Name</span>
            <span>Role</span>
            <span>Active</span>
            <span>Scope</span>
          </div>
          {clientRows.map((client) => (
            <div className="table__row" key={client.id}>
              <span>{shortId(client.id)}</span>
              <span>{client.name}</span>
              <span>{client.role}</span>
              <span>{client.active ? 'Yes' : 'No'}</span>
              <span>
                {client.driverProfileId
                  ? `driver:${shortId(client.driverProfileId)}`
                  : client.fleet_id
                    ? `fleet:${shortId(client.fleet_id)}`
                    : client.insurance_partner_id
                      ? `ins:${shortId(client.insurance_partner_id)}`
                      : 'global'}
              </span>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  )
}

