import { createContext } from 'react'
import type {
  AssetDetail,
  AssetsSummary,
  RefreshResponse,
} from '../types/entities'

export interface AssetsContextValue {
  assets: AssetDetail[]
  summary: AssetsSummary | null
  loading: boolean
  refreshing: boolean
  error: string | null
  includeClosed: boolean
  isFetched: { open: boolean; all: boolean }
  fetchAssets: (opts?: {
    includeClosed?: boolean
    force?: boolean
  }) => Promise<void>
  refreshMarket: () => Promise<RefreshResponse | null>
}

export const AssetsContext = createContext<AssetsContextValue | undefined>(
  undefined,
)
