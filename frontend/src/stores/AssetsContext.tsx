import {
  createContext,
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { fetchAssets as fetchAssetsApi } from '../services/api/assets'
import { refreshMarket as refreshMarketApi } from '../services/api/market'
import { toReadableMessage } from '../utils/errors'
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

export function AssetsProvider({ children }: { children: ReactNode }) {
  const [assets, setAssets] = useState<AssetDetail[]>([])
  const [summary, setSummary] = useState<AssetsSummary | null>(null)
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

  const refreshMarket = useCallback(async () => {
    setRefreshing(true)
    setError(null)
    try {
      const result = await refreshMarketApi()
      await fetchAssets({ includeClosed, force: true })
      return result
    } catch (err) {
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
    ],
  )

  return (
    <AssetsContext.Provider value={value}>{children}</AssetsContext.Provider>
  )
}
