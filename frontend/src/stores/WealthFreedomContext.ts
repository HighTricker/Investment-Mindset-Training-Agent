import { createContext } from 'react'
import type { WealthFreedomMetrics } from '../types/entities'

export interface WealthFreedomContextValue {
  metrics: WealthFreedomMetrics | null
  loading: boolean
  error: string | null
  isFetched: boolean
  fetchMetrics: (opts?: { force?: boolean }) => Promise<void>
  invalidate: () => void
}

export const WealthFreedomContext = createContext<
  WealthFreedomContextValue | undefined
>(undefined)
