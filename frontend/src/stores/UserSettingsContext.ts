import { createContext } from 'react'
import type { UserSettings } from '../types/entities'
import type { UpdateUserSettingsRequest } from '../types/api'

export interface UserSettingsContextValue {
  settings: UserSettings | null
  loading: boolean
  error: string | null
  isFetched: boolean
  fetchSettings: (opts?: { force?: boolean }) => Promise<void>
  updateSettings: (payload: UpdateUserSettingsRequest) => Promise<UserSettings>
}

export const UserSettingsContext = createContext<
  UserSettingsContextValue | undefined
>(undefined)
