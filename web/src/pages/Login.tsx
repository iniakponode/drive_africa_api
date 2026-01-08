import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function Login() {
  const { login, loading, error } = useAuth()
  const [apiKey, setApiKey] = useState('')
  const [localError, setLocalError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!apiKey.trim()) {
      setLocalError('Enter a valid API key.')
      return
    }
    setLocalError('')
    try {
      await login(apiKey)
      navigate('/', { replace: true })
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  return (
    <div className="login">
      <div className="login__panel">
        <p className="eyebrow">SafeDrive Africa</p>
        <h1>Fleet Intelligence Console</h1>
        <p className="subtext">
          Sign in with your API key to access fleet, driver, researcher, or
          insurance dashboards.
        </p>
        <form className="login__form" onSubmit={handleSubmit}>
          <label className="login__label" htmlFor="apiKey">
            API Key
          </label>
          <input
            id="apiKey"
            className="login__input"
            placeholder="Paste your X-API-Key value"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
          />
          <button className="cta login__submit" type="submit" disabled={loading}>
            {loading ? 'Authenticating...' : 'Sign in'}
          </button>
          {(localError || error) && (
            <p className="login__error">{localError || error}</p>
          )}
        </form>
      </div>
      <div className="login__side">
        <div className="login__card">
          <h3>What you can do</h3>
          <ul>
            <li>Monitor driver safety in near real time.</li>
            <li>Track UBPK and bad-day spikes with percentile logic.</li>
            <li>Export reports for compliance and coaching.</li>
          </ul>
        </div>
        <div className="login__card login__card--dark">
          <h3>Need an API key?</h3>
          <p>Ask your admin to generate one from the Admin dashboard.</p>
        </div>
      </div>
    </div>
  )
}
