import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import {
  fetchUserSettings as fetchUserSettingsApi,
  updateUserSettings as updateUserSettingsApi,
} from '../services/api/userSettings'
import { toReadableMessage } from '../utils/errors'
import type { UserSettings } from '../types/entities'
import type { UpdateUserSettingsRequest } from '../types/api'
import {
  UserSettingsContext,
  type UserSettingsContextValue,
} from './UserSettingsContext'

export function UserSettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fetchedRef = useRef(false)
  const [isFetched, setIsFetched] = useState(false)

  const fetchSettings = useCallback(async (opts?: { force?: boolean }) => {
    const force = opts?.force ?? false
    if (!force && fetchedRef.current) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchUserSettingsApi()
      setSettings(data)
      fetchedRef.current = true
      setIsFetched(true)
    } catch (err) {
      setError(toReadableMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  const updateSettings = useCallback(
    async (payload: UpdateUserSettingsRequest): Promise<UserSettings> => {
      const updated = await updateUserSettingsApi(payload)
      setSettings(updated)
      fetchedRef.current = true
      setIsFetched(true)
      return updated
    },
    [],
  )

  const value = useMemo<UserSettingsContextValue>(
    () => ({
      settings,
      loading,
      error,
      isFetched,
      fetchSettings,
      updateSettings,
    }),
    [settings, loading, error, isFetched, fetchSettings, updateSettings],
  )

  return (
    <UserSettingsContext.Provider value={value}>
      {children}
    </UserSettingsContext.Provider>
  )
}
