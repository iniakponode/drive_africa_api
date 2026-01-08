import { useEffect, useState } from 'react'
import { AppShell } from '../../components/AppShell'
import { useAuth } from '../../auth/AuthContext'
import {
  createAlcoholQuestionnaire,
  getAlcoholQuestionnaires,
} from '../../lib/api'
import type { AlcoholQuestionnaire } from '../../lib/types'

function generateUuid() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return ''
}

export function DriverQuestionnaire() {
  const { apiKey, profile } = useAuth()
  const [questionnaires, setQuestionnaires] = useState<AlcoholQuestionnaire[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [createdId, setCreatedId] = useState('')

  const [form, setForm] = useState({
    id: '',
    driverProfileId: '',
    drankAlcohol: false,
    selectedAlcoholTypes: '',
    beerQuantity: '',
    wineQuantity: '',
    spiritsQuantity: '',
    firstDrinkTime: '',
    lastDrinkTime: '',
    emptyStomach: false,
    caffeinatedDrink: false,
    impairmentLevel: 0,
    plansToDrive: false,
    sync: true,
  })

  useEffect(() => {
    if (profile?.driverProfileId) {
      setForm((prev) => ({ ...prev, driverProfileId: profile.driverProfileId }))
    }
  }, [profile?.driverProfileId])

  const handleLoad = async () => {
    if (!apiKey) return
    setLoading(true)
    setError('')
    try {
      const data = await getAlcoholQuestionnaires(apiKey)
      setQuestionnaires(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load questionnaires')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void handleLoad()
  }, [apiKey])

  const handleCreate = async () => {
    if (!apiKey) return
    if (!form.driverProfileId) {
      setError('DriverProfileId is required.')
      return
    }
    const payload: AlcoholQuestionnaire = {
      id: form.id || generateUuid(),
      driverProfileId: form.driverProfileId,
      drankAlcohol: form.drankAlcohol,
      selectedAlcoholTypes: form.selectedAlcoholTypes || null,
      beerQuantity: form.beerQuantity || null,
      wineQuantity: form.wineQuantity || null,
      spiritsQuantity: form.spiritsQuantity || null,
      firstDrinkTime: form.firstDrinkTime || '',
      lastDrinkTime: form.lastDrinkTime || '',
      emptyStomach: form.emptyStomach,
      caffeinatedDrink: form.caffeinatedDrink,
      impairmentLevel: form.impairmentLevel,
      date: new Date().toISOString(),
      plansToDrive: form.plansToDrive,
      sync: form.sync,
    }
    setLoading(true)
    setError('')
    try {
      const data = await createAlcoholQuestionnaire(apiKey, payload)
      setCreatedId(data.id)
      setForm((prev) => ({
        ...prev,
        id: '',
        selectedAlcoholTypes: '',
        beerQuantity: '',
        wineQuantity: '',
        spiritsQuantity: '',
        firstDrinkTime: '',
        lastDrinkTime: '',
        impairmentLevel: 0,
        plansToDrive: false,
      }))
      await handleLoad()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create questionnaire')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      eyebrow="Driver"
      title="Alcohol Questionnaire"
      subtitle="Submit daily alcohol status and driving intent."
      actions={
        <button className="cta" onClick={handleCreate} disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Questionnaire'}
        </button>
      }
    >
      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>Questionnaire</h2>
          <span className="panel__meta">Provide today’s responses.</span>
        </div>
        <div className="form-row">
          <input
            className="login__input"
            placeholder="Questionnaire ID"
            value={form.id}
            onChange={(event) => setForm({ ...form, id: event.target.value })}
          />
          <button
            className="ghost ghost--light"
            onClick={() => setForm({ ...form, id: generateUuid() })}
            type="button"
          >
            Generate ID
          </button>
          <input
            className="login__input"
            placeholder="Driver Profile ID"
            value={form.driverProfileId}
            onChange={(event) =>
              setForm({ ...form, driverProfileId: event.target.value })
            }
            disabled={!!profile?.driverProfileId && profile.role !== 'admin'}
          />
          <label className="toggle">
            <input
              type="checkbox"
              checked={form.drankAlcohol}
              onChange={(event) =>
                setForm({ ...form, drankAlcohol: event.target.checked })
              }
            />
            Drank alcohol
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={form.plansToDrive}
              onChange={(event) =>
                setForm({ ...form, plansToDrive: event.target.checked })
              }
            />
            Plans to drive
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={form.emptyStomach}
              onChange={(event) =>
                setForm({ ...form, emptyStomach: event.target.checked })
              }
            />
            Empty stomach
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={form.caffeinatedDrink}
              onChange={(event) =>
                setForm({ ...form, caffeinatedDrink: event.target.checked })
              }
            />
            Caffeinated drink
          </label>
          <input
            className="login__input"
            placeholder="Alcohol Types"
            value={form.selectedAlcoholTypes}
            onChange={(event) =>
              setForm({ ...form, selectedAlcoholTypes: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Beer Quantity"
            value={form.beerQuantity}
            onChange={(event) =>
              setForm({ ...form, beerQuantity: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Wine Quantity"
            value={form.wineQuantity}
            onChange={(event) =>
              setForm({ ...form, wineQuantity: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Spirits Quantity"
            value={form.spiritsQuantity}
            onChange={(event) =>
              setForm({ ...form, spiritsQuantity: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="First Drink Time"
            value={form.firstDrinkTime}
            onChange={(event) =>
              setForm({ ...form, firstDrinkTime: event.target.value })
            }
          />
          <input
            className="login__input"
            placeholder="Last Drink Time"
            value={form.lastDrinkTime}
            onChange={(event) =>
              setForm({ ...form, lastDrinkTime: event.target.value })
            }
          />
          <input
            className="login__input"
            type="number"
            min={0}
            max={10}
            placeholder="Impairment Level"
            value={form.impairmentLevel}
            onChange={(event) =>
              setForm({ ...form, impairmentLevel: Number(event.target.value) })
            }
          />
          <label className="toggle">
            <input
              type="checkbox"
              checked={form.sync}
              onChange={(event) =>
                setForm({ ...form, sync: event.target.checked })
              }
            />
            Sync
          </label>
        </div>
        {createdId && (
          <p className="panel__meta">Submitted questionnaire {createdId}.</p>
        )}
        {error && <p className="login__error">{error}</p>}
      </section>

      <section className="panel panel--wide">
        <div className="panel__header">
          <h2>History</h2>
          <span className="panel__meta">{questionnaires.length} records</span>
        </div>
        <div className="table">
          <div className="table__row table__row--header">
            <span>ID</span>
            <span>Driver</span>
            <span>Alcohol</span>
            <span>Plans</span>
            <span>Impairment</span>
            <span>Date</span>
          </div>
          {questionnaires.map((item) => (
            <div className="table__row" key={item.id}>
              <span>{item.id.slice(0, 6)}</span>
              <span>{item.driverProfileId.slice(0, 6)}</span>
              <span>{item.drankAlcohol ? 'Yes' : 'No'}</span>
              <span>{item.plansToDrive ? 'Yes' : 'No'}</span>
              <span>{item.impairmentLevel}</span>
              <span>{new Date(item.date).toLocaleDateString()}</span>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  )
}
