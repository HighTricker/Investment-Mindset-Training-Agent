import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { fetchWealthFreedom } from '../services/api/metrics'
import { toReadableMessage } from '../utils/errors'
import type { WealthFreedomMetrics } from '../types/entities'
import {
  WealthFreedomContext,
  type WealthFreedomContextValue,
} from './WealthFreedomContext'

export function WealthFreedomProvider({ children }: { children: ReactNode }) {
  const [metrics, setMetrics] = useState<WealthFreedomMetrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fetchedRef = useRef(false)
  const [isFetched, setIsFetched] = useState(false)

  const fetchMetrics = useCallback(async (opts?: { force?: boolean }) => {
    const force = opts?.force ?? false
    if (!force && fetchedRef.current) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchWealthFreedom()
      setMetrics(data)
      fetchedRef.current = true
      setIsFetched(true)
    } catch (err) {
      setError(toReadableMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  const invalidate = useCallback(() => {
    fetchedRef.current = false
    setIsFetched(false)
  }, [])

  const value = useMemo<WealthFreedomContextValue>(
    () => ({
      metrics,
      loading,
      error,
      isFetched,
      fetchMetrics,
      invalidate,
    }),
    [metrics, loading, error, isFetched, fetchMetrics, invalidate],
  )

  return (
    <WealthFreedomContext.Provider value={value}>
      {children}
    </WealthFreedomContext.Provider>
  )
}
