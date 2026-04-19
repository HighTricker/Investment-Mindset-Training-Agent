import { client } from './client'
import type { UserSettings } from '../../types/entities'
import type { UpdateUserSettingsRequest } from '../../types/api'

export async function fetchUserSettings(): Promise<UserSettings> {
  const { data } = await client.get<UserSettings>('/user-settings')
  return data
}

export async function updateUserSettings(
  payload: UpdateUserSettingsRequest,
): Promise<UserSettings> {
  const { data } = await client.put<UserSettings>('/user-settings', payload)
  return data
}
