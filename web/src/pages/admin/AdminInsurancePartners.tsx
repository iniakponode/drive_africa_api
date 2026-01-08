import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  assignInsurancePartnerDriver,
  batchAssignInsurancePartnerMappings,
  batchRemoveInsurancePartnerMappings,
  createInsurancePartner,
  getInsurancePartners,
  removeInsurancePartnerDriver,
} from '../../lib/api'
import type { InsurancePartner } from '../../lib/types'
import { getRowValue, parseCsvRecords } from '../../lib/csv'

export function AdminInsurancePartners() {
  const { apiKey } = useAuth()
  const [partners, setPartners] = useState<InsurancePartner[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [created, setCreated] = useState<InsurancePartner | null>(null)

  const [createForm, setCreateForm] = useState({
    name: '',
    label: '',
    active: true,
  })
  const [assignForm, setAssignForm] = useState({
    partnerId: '',
    driverProfileId: '',
  })
  const [removeForm, setRemoveForm] = useState({
    partnerId: '',
    driverProfileId: '',
  })
  const [bulkAssignResult, setBulkAssignResult] = useState('')
  const [bulkRemoveResult, setBulkRemoveResult] = useState('')

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getInsurancePartners(apiKey)
      setPartners(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load partners')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void handleLoad()
  }, [apiKey])

  const handleCreate = async () => {
    if (!apiKey) return
    if (!createForm.name.trim() || !createForm.label.trim()) {
      setError('Name and label are required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await createInsurancePartner(apiKey, {
        name: createForm.name.trim(),
        label: createForm.label.trim(),
        active: createForm.active,
      })
      setCreated(data)
      setCreateForm({ name: '', label: '', active: true })
      await handleLoad()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create partner')
    } finally {
      setLoading(false)
    }
  }

  const handleAssign = async () => {
    if (!apiKey) return
    if (!assignForm.partnerId || !assignForm.driverProfileId) {
      setError('Provide partnerId and driverProfileId to assign.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await assignInsurancePartnerDriver(
        apiKey,
        assignForm.partnerId,
        assignForm.driverProfileId,
      )
      setAssignForm({ partnerId: '', driverProfileId: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign driver')
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async () => {
    if (!apiKey) return
    if (!removeForm.partnerId || !removeForm.driverProfileId) {
      setError('Provide partnerId and driverProfileId to remove.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await removeInsurancePartnerDriver(
        apiKey,
        removeForm.partnerId,
        removeForm.driverProfileId,
      )
      setRemoveForm({ partnerId: '', driverProfileId: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove driver')
    } finally {
      setLoading(false)
    }
  }

  const handleBulkAssign = async (file: File | null) => {
    if (!apiKey || !file) return
    setBulkAssignResult('')
    setLoading(true)
    setError('')
    try {
      const text = await file.text()
      const { rows } = parseCsvRecords(text)
      const errors: string[] = []
      const payload = rows
        .map((row, index) => {
          const partnerId = getRowValue(row, ['partner_id', 'partnerId'])
          const driverId = getRowValue(row, [
            'driverProfileId',
            'driver_profile_id',
          ])
          if (!partnerId || !driverId) {
            errors.push(`Row ${index + 2}: missing partner_id or driverProfileId`)
            return null
          }
          return { partner_id: partnerId, driverProfileId: driverId }
        })
        .filter(
          (
            row,
          ): row is { partner_id: string; driverProfileId: string } =>
            Boolean(row),
        )
      if (!payload.length) {
        setError('CSV has no valid rows.')
        setLoading(false)
        return
      }
      const result = await batchAssignInsurancePartnerMappings(apiKey, payload)
      const combinedErrors = [...errors, ...(result.errors ?? [])]
      setBulkAssignResult(
        `Assigned ${result.created ?? 0}/${payload.length} drivers.${result.skipped ? ` Skipped: ${result.skipped}` : ''}${combinedErrors.length ? ` Errors: ${combinedErrors.length}` : ''}`,
      )
      if (combinedErrors.length) {
        setError(combinedErrors.slice(0, 5).join(' | '))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bulk assign failed')
    } finally {
      setLoading(false)
    }
  }

  const handleBulkRemove = async (file: File | null) => {
    if (!apiKey || !file) return
    setBulkRemoveResult('')
    setLoading(true)
    setError('')
    try {
      const text = await file.text()
      const { rows } = parseCsvRecords(text)
      const errors: string[] = []
      const payload = rows
        .map((row, index) => {
          const partnerId = getRowValue(row, ['partner_id', 'partnerId'])
          const driverId = getRowValue(row, [
            'driverProfileId',
            'driver_profile_id',
          ])
          if (!partnerId || !driverId) {
            errors.push(`Row ${index + 2}: missing partner_id or driverProfileId`)
            return null
          }
          return { partner_id: partnerId, driverProfileId: driverId }
        })
        .filter(
          (
            row,
          ): row is { partner_id: string; driverProfileId: string } =>
            Boolean(row),
        )
      if (!payload.length) {
        setError('CSV has no valid rows.')
        setLoading(false)
        return
      }
      const result = await batchRemoveInsurancePartnerMappings(apiKey, payload)
      const combinedErrors = [...errors, ...(result.errors ?? [])]
      setBulkRemoveResult(
        `Removed ${result.removed ?? 0}/${payload.length} drivers.${result.skipped ? ` Skipped: ${result.skipped}` : ''}${combinedErrors.length ? ` Errors: ${combinedErrors.length}` : ''}`,
      )
      if (combinedErrors.length) {
        setError(combinedErrors.slice(0, 5).join(' | '))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bulk remove failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Admin"
      title="Insurance Partners"
      subtitle="Manage partners and driver mappings."
      actions={
        <button className="cta" onClick={handleLoad} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Create Partner</h2>
          <span className="panel__meta">Labels must be unique.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Partner Name"
            value={createForm.name}
            onChange={(event) =>
              setCreateForm({ ...createForm, name: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Label"
            value={createForm.label}
            onChange={(event) =>
              setCreateForm({ ...createForm, label: event.target.value })
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
            Create Partner
          </button>
        </div>
        {created && (
          <p className="panel__meta">
            Created {created.name} ({created.label})
          </p>
        )}
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Assign Driver</h2>
            <span className="panel__meta">Map driver to partner</span>
          </div>
          <div className="form-row">
            <input
              className="login__input"
              placeholder="Partner ID"
              value={assignForm.partnerId}
              onChange={(event) =>
                setAssignForm({ ...assignForm, partnerId: event.target.value })
              }
            />
            <input
              className="login__input"
              placeholder="Driver Profile ID"
              value={assignForm.driverProfileId}
              onChange={(event) =>
                setAssignForm({
                  ...assignForm,
                  driverProfileId: event.target.value,
                })
              }
            />
            <button className="cta" onClick={handleAssign} disabled={loading}>
              Assign
            </button>
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Remove Mapping</h2>
            <span className="panel__meta">Unlink driver from partner</span>
          </div>
          <div className="form-row">
            <input
              className="login__input"
              placeholder="Partner ID"
              value={removeForm.partnerId}
              onChange={(event) =>
                setRemoveForm({ ...removeForm, partnerId: event.target.value })
              }
            />
            <input
              className="login__input"
              placeholder="Driver Profile ID"
              value={removeForm.driverProfileId}
              onChange={(event) =>
                setRemoveForm({
                  ...removeForm,
                  driverProfileId: event.target.value,
                })
              }
            />
            <button className="cta" onClick={handleRemove} disabled={loading}>
              Remove
            </button>
          </div>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Bulk Assign (CSV)</h2>
            <span className="panel__meta">Columns: partner_id, driverProfileId</span>
          </div>
          <input
            className="login__input"
            type="file"
            accept=".csv"
            onChange={(event) =>
              handleBulkAssign(event.target.files ? event.target.files[0] : null)
            }
          />
          {bulkAssignResult && <p className="panel__meta">{bulkAssignResult}</p>}
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Bulk Remove (CSV)</h2>
            <span className="panel__meta">Columns: partner_id, driverProfileId</span>
          </div>
          <input
            className="login__input"
            type="file"
            accept=".csv"
            onChange={(event) =>
              handleBulkRemove(event.target.files ? event.target.files[0] : null)
            }
          />
          {bulkRemoveResult && <p className="panel__meta">{bulkRemoveResult}</p>}
        </article>
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Partners</h2>
          <span className="panel__meta">{partners.length} partners</span>
        </div>
        <div className="table">
          <div className="table__row table__row--header">
            <span>ID</span>
            <span>Name</span>
            <span>Label</span>
            <span>Active</span>
          </div>
          {partners.map((partner) => (
            <div className="table__row" key={partner.id}>
              <span>{partner.id.slice(0, 8)}</span>
              <span>{partner.name}</span>
              <span>{partner.label}</span>
              <span>{partner.active ? 'Yes' : 'No'}</span>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  )
}
