import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import {
  addAsset as addAssetApi,
  closeAsset as closeAssetApi,
  fetchAssets as fetchAssetsApi,
} from '../services/api/assets'
import { refreshMarket as refreshMarketApi } from '../services/api/market'
import { addTransaction as addTransactionApi } from '../services/api/transactions'
import { toReadableMessage } from '../utils/errors'
import type { RefreshResponse } from '../types/entities'
import type {
  AddAssetRequest,
  AddAssetResponse,
  AddTransactionRequest,
  TransactionResponse,
} from '../types/api'
import {
  AssetsContext,
  type AssetsContextValue,
} from './AssetsContext'

const MIN_REFRESH_LOADING_MS = 600

export function AssetsProvider({ children }: { children: ReactNode }) {
  const [assets, setAssets] = useState<AssetsContextValue['assets']>([])
  const [summary, setSummary] = useState<AssetsContextValue['summary']>(null)
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [includeClosed, setIncludeClosed] = useState(false)
  const fetchedRef = useRef<{ open: boolean; all: boolean }>({
    open: false,
    all: false,
  })
  const [isFetched, setIsFetched] = useState(fetchedRef.current)

  const fetchAssets = useCallback(
    async (opts?: { includeClosed?: boolean; force?: boolean }) => {
      const wantClosed = opts?.includeClosed ?? false
      const force = opts?.force ?? false
      const bucket: 'open' | 'all' = wantClosed ? 'all' : 'open'
      if (!force && fetchedRef.current[bucket]) return
      setLoading(true)
      setError(null)
      try {
        const data = await fetchAssetsApi(wantClosed)
        setAssets(data.assets)
        setSummary(data.summary)
        setIncludeClosed(wantClosed)
        fetchedRef.current = { ...fetchedRef.current, [bucket]: true }
        setIsFetched(fetchedRef.current)
      } catch (err) {
        setError(toReadableMessage(err))
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const addAsset = useCallback(
    async (payload: AddAssetRequest): Promise<AddAssetResponse> => {
      const result = await addAssetApi(payload)
      await fetchAssets({ includeClosed, force: true })
      return result
    },
    [fetchAssets, includeClosed],
  )

  const addTransaction = useCallback(
    async (payload: AddTransactionRequest): Promise<TransactionResponse> => {
      const result = await addTransactionApi(payload)
      await fetchAssets({ includeClosed, force: true })
      return result
    },
    [fetchAssets, includeClosed],
  )

  const closeAsset = useCallback(
    async (assetId: number, reason: string | null): Promise<void> => {
      await closeAssetApi(assetId, { reason })
      await fetchAssets({ includeClosed, force: true })
    },
    [fetchAssets, includeClosed],
  )

  const refreshMarket = useCallback(async (): Promise<RefreshResponse | null> => {
    setRefreshing(true)
    setError(null)
    const minDelay = new Promise<void>((resolve) =>
      setTimeout(resolve, MIN_REFRESH_LOADING_MS),
    )
    try {
      const [result] = await Promise.all([refreshMarketApi(), minDelay])
      await fetchAssets({ includeClosed, force: true })
      return result
    } catch (err) {
      await minDelay
      setError(toReadableMessage(err))
      return null
    } finally {
      setRefreshing(false)
    }
  }, [fetchAssets, includeClosed])

  const value = useMemo<AssetsContextValue>(
    () => ({
      assets,
      summary,
      loading,
      refreshing,
      error,
      includeClosed,
      isFetched,
      fetchAssets,
      refreshMarket,
      addAsset,
      addTransaction,
      closeAsset,
    }),
    [
      assets,
      summary,
      loading,
      refreshing,
      error,
      includeClosed,
      isFetched,
      fetchAssets,
      refreshMarket,
      addAsset,
      addTransaction,
      closeAsset,
    ],
  )

  return (
    <AssetsContext.Provider value={value}>{children}</AssetsContext.Provider>
  )
}
