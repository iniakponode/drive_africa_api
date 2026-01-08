import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import { getTrips, updateTrip } from '../../lib/api'
import type { TripResponse } from '../../lib/types'

export function DriverTrips() {
  const { apiKey } = useAuth()
  const [limit, setLimit] = useState(20)
  const [trips, setTrips] = useState<TripResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [updateForm, setUpdateForm] = useState({
    tripId: '',
    tripNotes: '',
    influence: '',
    userAlcoholResponse: '',
    alcoholProbability: '',
  })

  const loadTrips = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getTrips(apiKey, { limit })
      setTrips(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trips')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadTrips()
  }, [apiKey, limit])

  const handleUpdate = async () => {
    if (!apiKey) return
    if (!updateForm.tripId) {
      setError('Provide a trip ID to update.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload: {
        tripNotes?: string
        influence?: string
        userAlcoholResponse?: string
        alcoholProbability?: number
      } = {}
      if (updateForm.tripNotes) payload.tripNotes = updateForm.tripNotes
      if (updateForm.influence) payload.influence = updateForm.influence
      if (updateForm.userAlcoholResponse) {
        payload.userAlcoholResponse = updateForm.userAlcoholResponse
      }
      if (updateForm.alcoholProbability) {
        payload.alcoholProbability = Number(updateForm.alcoholProbability)
      }
      if (Object.keys(payload).length === 0) {
        setError('Provide at least one field to update.')
        setLoading(false)
        return
      }
      await updateTrip(apiKey, updateForm.tripId, payload)
      setUpdateForm({
        tripId: '',
        tripNotes: '',
        influence: '',
        userAlcoholResponse: '',
        alcoholProbability: '',
      })
      await loadTrips()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update trip')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Trip Logs"
      title="Trips"
      subtitle="Recent trips captured for your profile."
      actions={
        <button className="cta" onClick={loadTrips} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Filters</h2>
          <span className="panel__meta">Adjust list size</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            type="number"
            min={1}
            max={200}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
        </div>
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Update Trip Notes</h2>
          <span className="panel__meta">Attach notes or alcohol response.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Trip ID"
            value={updateForm.tripId}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, tripId: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Trip Notes"
            value={updateForm.tripNotes}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, tripNotes: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Influence"
            value={updateForm.influence}
            onChange={(event) =>
              setUpdateForm({ ...updateForm, influence: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Alcohol Response"
            value={updateForm.userAlcoholResponse}
            onChange={(event) =>
              setUpdateForm({
                ...updateForm,
                userAlcoholResponse: event.target.value,
              })
            }
          />
          <input
            className="login__input"
            placeholder="Alcohol Probability"
            value={updateForm.alcoholProbability}
            onChange={(event) =>
              setUpdateForm({
                ...updateForm,
                alcoholProbability: event.target.value,
              })
            }
          />
          <button className="cta" onClick={handleUpdate} disabled={loading}>
            Update Trip
          </button>
        </div>
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Trip List</h2>
          <span className="panel__meta">{trips.length} records</span>
        </div>
        <div className="table">
          <div className="table__row table__row--header">
            <span>Trip</span>
            <span>Start</span>
            <span>End</span>
            <span>Influence</span>
            <span>Sync</span>
          </div>
          {trips.map((trip) => (
            <div className="table__row" key={trip.id}>
              <span>{trip.id.slice(0, 8)}</span>
              <span>
                {trip.start_date ??
                  trip.start_time ??
                  trip.startTime ??
                  '--'}
              </span>
              <span>{trip.end_date ?? trip.end_time ?? '--'}</span>
              <span>{trip.influence ?? 'Unknown'}</span>
              <span>{trip.sync ? 'Synced' : 'Pending'}</span>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  )
}
