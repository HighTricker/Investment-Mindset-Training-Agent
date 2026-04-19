import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import {
  addIncome as addIncomeApi,
  fetchIncome as fetchIncomeApi,
} from '../services/api/income'
import { toReadableMessage } from '../utils/errors'
import type { IncomeListResponse, IncomeRecord } from '../types/entities'
import type { AddIncomeRequest } from '../types/api'
import { IncomeContext, type IncomeContextValue } from './IncomeContext'

export function IncomeProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<IncomeListResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fetchedMonthRef = useRef<string | null>(null)
  const [isFetched, setIsFetched] = useState(false)

  const fetchIncome = useCallback(
    async (opts?: { month?: string; force?: boolean }) => {
      const month = opts?.month ?? null
      const force = opts?.force ?? false
      if (!force && fetchedMonthRef.current === month && isFetched) return
      setLoading(true)
      setError(null)
      try {
        const result = await fetchIncomeApi(month ?? undefined)
        setData(result)
        fetchedMonthRef.current = month
        setIsFetched(true)
      } catch (err) {
        setError(toReadableMessage(err))
      } finally {
        setLoading(false)
      }
    },
    [isFetched],
  )

  const addIncome = useCallback(
    async (payload: AddIncomeRequest): Promise<IncomeRecord> => {
      const created = await addIncomeApi(payload)
      await fetchIncome({
        month: fetchedMonthRef.current ?? undefined,
        force: true,
      })
      return created
    },
    [fetchIncome],
  )

  const value = useMemo<IncomeContextValue>(
    () => ({
      data,
      loading,
      error,
      isFetched,
      fetchIncome,
      addIncome,
    }),
    [data, loading, error, isFetched, fetchIncome, addIncome],
  )

  return (
    <IncomeContext.Provider value={value}>{children}</IncomeContext.Provider>
  )
}
