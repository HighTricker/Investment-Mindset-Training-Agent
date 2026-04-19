import { client } from './client'
import type { RefreshResponse } from '../../types/entities'

export async function refreshMarket(): Promise<RefreshResponse> {
  const { data } = await client.post<RefreshResponse>('/market/refresh')
  return data
}
