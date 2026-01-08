import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  batchCreateFleetVehicleGroups,
  batchUpdateFleetVehicleGroups,
  createFleet,
  createFleetVehicleGroup,
  getFleetVehicleGroups,
  getFleets,
  updateFleetVehicleGroup,
} from '../../lib/api'
import type { Fleet, VehicleGroup } from '../../lib/types'
import { getRowValue, parseCsvRecords } from '../../lib/csv'

export function FleetManagement() {
  const { apiKey, profile } = useAuth()
  const [fleets, setFleets] = useState<Fleet[]>([])
  const [groups, setGroups] = useState<VehicleGroup[]>([])
  const [selectedFleetId, setSelectedFleetId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [fleetForm, setFleetForm] = useState({
    name: '',
    description: '',
    region: '',
  })
  const [groupForm, setGroupForm] = useState({
    name: '',
    description: '',
  })
  const [groupUpdateForm, setGroupUpdateForm] = useState({
    groupId: '',
    name: '',
    description: '',
  })
  const [bulkCreateResult, setBulkCreateResult] = useState('')
  const [bulkUpdateResult, setBulkUpdateResult] = useState('')

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getFleets(apiKey)
      setFleets(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load fleets')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void handleLoad()
  }, [apiKey])

  const handleCreateFleet = async () => {
    if (!apiKey) return
    if (!fleetForm.name.trim()) {
      setError('Fleet name is required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await createFleet(apiKey, {
        name: fleetForm.name.trim(),
        description: fleetForm.description || undefined,
        region: fleetForm.region || undefined,
      })
      setFleetForm({ name: '', description: '', region: '' })
      await handleLoad()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create fleet')
    } finally {
      setLoading(false)
    }
  }

  const handleLoadGroups = async () => {
    if (!apiKey || !selectedFleetId) return
    setLoading(true)
    setError('')
    try {
      const data = await getFleetVehicleGroups(apiKey, selectedFleetId)
      setGroups(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load groups')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateGroup = async () => {
    if (!apiKey || !selectedFleetId) {
      setError('Select a fleet to create a vehicle group.')
      return
    }
    if (!groupForm.name.trim()) {
      setError('Group name is required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await createFleetVehicleGroup(apiKey, selectedFleetId, {
        name: groupForm.name.trim(),
        description: groupForm.description || undefined,
      })
      setGroupForm({ name: '', description: '' })
      await handleLoadGroups()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create group')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateGroup = async () => {
    if (!apiKey) return
    if (!groupUpdateForm.groupId) {
      setError('Provide a vehicle group ID to update.')
      return
    }
    if (!groupUpdateForm.name && !groupUpdateForm.description) {
      setError('Provide a name or description to update.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await updateFleetVehicleGroup(apiKey, groupUpdateForm.groupId, {
        name: groupUpdateForm.name || undefined,
        description: groupUpdateForm.description || undefined,
      })
      setGroupUpdateForm({ groupId: '', name: '', description: '' })
      if (selectedFleetId) {
        await handleLoadGroups()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update group')
    } finally {
      setLoading(false)
    }
  }

  const handleBulkCreate = async (file: File | null) => {
    if (!apiKey || !file) return
    setBulkCreateResult('')
    setLoading(true)
    setError('')
    try {
      const text = await file.text()
      const { rows } = parseCsvRecords(text)
      const errors: string[] = []
      const payload = rows
        .map((row, index) => {
          const fleetId =
            getRowValue(row, ['fleet_id', 'fleetId']) || selectedFleetId
          const name = getRowValue(row, ['name'])
          const description = getRowValue(row, ['description'])
          if (!fleetId || !name) {
            errors.push(`Row ${index + 2}: missing fleet_id or name`)
            return null
          }
          return {
            fleet_id: fleetId,
            name,
            description: description || undefined,
          }
        })
        .filter(
          (
            row,
          ): row is { fleet_id: string; name: string; description?: string } =>
            Boolean(row),
        )
      if (!payload.length) {
        setError('CSV has no valid rows.')
        setLoading(false)
        return
      }
      const result = await batchCreateFleetVehicleGroups(apiKey, payload)
      const combinedErrors = [...errors, ...(result.errors ?? [])]
      setBulkCreateResult(
        `Created ${result.created ?? 0}/${payload.length} vehicle groups.${result.skipped ? ` Skipped: ${result.skipped}` : ''}${combinedErrors.length ? ` Errors: ${combinedErrors.length}` : ''}`,
      )
      if (combinedErrors.length) {
        setError(combinedErrors.slice(0, 5).join(' | '))
      }
      await handleLoadGroups()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bulk create failed')
    } finally {
      setLoading(false)
    }
  }

  const handleBulkUpdate = async (file: File | null) => {
    if (!apiKey || !file) return
    setBulkUpdateResult('')
    setLoading(true)
    setError('')
    try {
      const text = await file.text()
      const { rows } = parseCsvRecords(text)
      const errors: string[] = []
      const payload = rows
        .map((row, index) => {
          const groupId = getRowValue(row, [
            'group_id',
            'groupId',
            'vehicle_group_id',
          ])
          const name = getRowValue(row, ['name'])
          const description = getRowValue(row, ['description'])
          if (!groupId) {
            errors.push(`Row ${index + 2}: missing group_id`)
            return null
          }
          if (!name && !description) {
            errors.push(`Row ${index + 2}: no updates provided`)
            return null
          }
          return {
            group_id: groupId,
            name: name || undefined,
            description: description || undefined,
          }
        })
        .filter(
          (
            row,
          ): row is { group_id: string; name?: string; description?: string } =>
            Boolean(row),
        )
      if (!payload.length) {
        setError('CSV has no valid rows.')
        setLoading(false)
        return
      }
      const result = await batchUpdateFleetVehicleGroups(apiKey, payload)
      const combinedErrors = [...errors, ...(result.errors ?? [])]
      setBulkUpdateResult(
        `Updated ${result.updated ?? 0}/${payload.length} vehicle groups.${result.skipped ? ` Skipped: ${result.skipped}` : ''}${combinedErrors.length ? ` Errors: ${combinedErrors.length}` : ''}`,
      )
      if (combinedErrors.length) {
        setError(combinedErrors.slice(0, 5).join(' | '))
      }
      await handleLoadGroups()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bulk update failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Fleet Setup"
      title="Fleet Management"
      subtitle="Manage fleets and vehicle groups."
      actions={
        <button className="cta" onClick={handleLoad} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      }
    >
      {profile?.role === 'admin' && (
        <section className="panel panel--wide">
          <div className="panel__header">
            <h2>Create Fleet</h2>
            <span className="panel__meta">Admin-only action</span>
          </div>
          <div className="form-row">
            <input
              className="login__input"
              placeholder="Fleet Name"
              value={fleetForm.name}
              onChange={(event) =>
                setFleetForm({ ...fleetForm, name: event.target.value })
              }
            />
            <input
              className="login__input"
              placeholder="Region"
              value={fleetForm.region}
              onChange={(event) =>
                setFleetForm({ ...fleetForm, region: event.target.value })
              }
            />
            <input
              className="login__input"
              placeholder="Description"
              value={fleetForm.description}
              onChange={(event) =>
                setFleetForm({ ...fleetForm, description: event.target.value })
              }
            />
            <button className="cta" onClick={handleCreateFleet} disabled={loading}>
              Create Fleet
            </button>
          </div>
        </section>
      )}

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Fleets</h2>
            <span className="panel__meta">{fleets.length} fleets</span>
          </div>
          <div className="stack">
            {fleets.map((fleet) => (
              <div className="stack__row" key={fleet.id}>
                <div>
                  <p className="stack__title">{fleet.name}</p>
                  <p className="stack__meta">
                    {fleet.region ?? 'No region'} · {fleet.description ?? 'No description'}
                  </p>
                </div>
                <button
                  className="ghost ghost--light"
                  onClick={() => {
                    setSelectedFleetId(fleet.id)
                    void handleLoadGroups()
                  }}
                >
                  View groups
                </button>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Vehicle Groups</h2>
            <span className="panel__meta">
              {selectedFleetId ? `Fleet ${selectedFleetId.slice(0, 8)}` : 'Select a fleet'}
            </span>
          </div>
          <div className="stack">
            {groups.length ? (
              groups.map((group) => (
                <div className="stack__row" key={group.id}>
                  <div>
                    <p className="stack__title">{group.name}</p>
                    <p className="stack__meta">{group.description ?? 'No description'}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="panel__meta">No groups loaded.</p>
            )}
          </div>
        </article>
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Create Vehicle Group</h2>
          <span className="panel__meta">Select a fleet first.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Fleet ID"
            value={selectedFleetId}
            onChange={(event) => setSelectedFleetId(event.target.value)}
          />
          <input
            className="login__input"
            placeholder="Group Name"
            value={groupForm.name}
            onChange={(event) =>
              setGroupForm({ ...groupForm, name: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Description"
            value={groupForm.description}
            onChange={(event) =>
              setGroupForm({ ...groupForm, description: event.target.value })
            }
          />
          <button className="cta" onClick={handleCreateGroup} disabled={loading}>
            Create Group
          </button>
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Update Vehicle Group</h2>
          <span className="panel__meta">Group ID required.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Group ID"
            value={groupUpdateForm.groupId}
            onChange={(event) =>
              setGroupUpdateForm({ ...groupUpdateForm, groupId: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Group Name"
            value={groupUpdateForm.name}
            onChange={(event) =>
              setGroupUpdateForm({ ...groupUpdateForm, name: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Description"
            value={groupUpdateForm.description}
            onChange={(event) =>
              setGroupUpdateForm({
                ...groupUpdateForm,
                description: event.target.value,
              })
            }
          />
          <button className="cta" onClick={handleUpdateGroup} disabled={loading}>
            Update Group
          </button>
        </div>
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Bulk Create Groups (CSV)</h2>
            <span className="panel__meta">
              Columns: fleet_id, name, description
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
          {bulkCreateResult && <p className="panel__meta">{bulkCreateResult}</p>}
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Bulk Update Groups (CSV)</h2>
            <span className="panel__meta">
              Columns: group_id, name, description
            </span>
          </div>
          <input
            className="login__input"
            type="file"
            accept=".csv"
            onChange={(event) =>
              handleBulkUpdate(event.target.files ? event.target.files[0] : null)
            }
          />
          {bulkUpdateResult && <p className="panel__meta">{bulkUpdateResult}</p>}
        </article>
      </section>
    </AppShell>
  )
}
