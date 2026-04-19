import { useContext } from 'react'
import {
  UserSettingsContext,
  type UserSettingsContextValue,
} from '../stores/UserSettingsContext'

export function useUserSettings(): UserSettingsContextValue {
  const ctx = useContext(UserSettingsContext)
  if (!ctx) {
    throw new Error('useUserSettings 必须在 <UserSettingsProvider> 内使用')
  }
  return ctx
}
