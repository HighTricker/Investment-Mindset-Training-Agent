import { client } from './client'
import type { WealthFreedomMetrics } from '../../types/entities'

export async function fetchWealthFreedom(): Promise<WealthFreedomMetrics> {
  const { data } = await client.get<WealthFreedomMetrics>(
    '/metrics/wealth-freedom',
  )
  return data
}
