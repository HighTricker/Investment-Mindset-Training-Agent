import { createContext } from 'react'
import type {
  AssetDetail,
  AssetsSummary,
  RefreshResponse,
} from '../types/entities'
import type {
  AddAssetRequest,
  AddAssetResponse,
  AddTransactionRequest,
  TransactionResponse,
} from '../types/api'

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
  addAsset: (payload: AddAssetRequest) => Promise<AddAssetResponse>
  addTransaction: (
    payload: AddTransactionRequest,
  ) => Promise<TransactionResponse>
  closeAsset: (assetId: number, reason: string | null) => Promise<void>
}

export const AssetsContext = createContext<AssetsContextValue | undefined>(
  undefined,
)
