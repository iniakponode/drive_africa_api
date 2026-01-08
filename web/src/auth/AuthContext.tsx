import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import { getAuthMe } from '../lib/api'
import type { AuthMe } from '../lib/types'

type AuthState = {
  apiKey: string
  profile: AuthMe | null
  loading: boolean
  error: string | null
  login: (key: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | undefined>(undefined)

const STORAGE_KEY = 'safedrive_api_key'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKey] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) ?? ''
  })
  const [profile, setProfile] = useState<AuthMe | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadProfile = useCallback(
    async (key: string) => {
      if (!key) {
        setProfile(null)
        setLoading(false)
        return
      }
      setLoading(true)
      try {
        const data = await getAuthMe(key)
        setProfile(data)
        setError(null)
        return data
      } catch (err) {
        setProfile(null)
        const message = err instanceof Error ? err.message : 'Login failed'
        setError(message)
        throw new Error(message)
      } finally {
        setLoading(false)
      }
    },
    [setProfile],
  )

  useEffect(() => {
    if (!apiKey) {
      setLoading(false)
      return
    }
    loadProfile(apiKey).catch(() => undefined)
  }, [apiKey, loadProfile])

  const login = useCallback(
    async (key: string) => {
      const trimmed = key.trim()
      setApiKey(trimmed)
      localStorage.setItem(STORAGE_KEY, trimmed)
      try {
        await loadProfile(trimmed)
      } catch (err) {
        localStorage.removeItem(STORAGE_KEY)
        setApiKey('')
        throw err
      }
    },
    [loadProfile],
  )

  const logout = useCallback(() => {
    setApiKey('')
    setProfile(null)
    setError(null)
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  const value = useMemo(
    () => ({
      apiKey,
      profile,
      loading,
      error,
      login,
      logout,
    }),
    [apiKey, profile, loading, error, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
