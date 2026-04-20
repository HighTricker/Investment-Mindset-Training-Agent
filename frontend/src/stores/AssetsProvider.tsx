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
  // isFetched 与 fetchedRef.current 独立初始化（虽然值等价），
  // 避免 React 19 的 react-hooks/refs 规则告警（render 时读 ref.current）
  const [isFetched, setIsFetched] = useState<{ open: boolean; all: boolean }>({
    open: false,
    all: false,
  })

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
        // force 时同时 invalidate 另一个桶：写操作后另一桶的缓存已陈旧，
        // 下次跨页访问会自动重拉，避免 P1 加资产 → 切 P3.1 看到旧列表
        const otherBucket: 'open' | 'all' = bucket === 'open' ? 'all' : 'open'
        fetchedRef.current = {
          ...fetchedRef.current,
          [bucket]: true,
          ...(force ? { [otherBucket]: false } : {}),
        }
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
