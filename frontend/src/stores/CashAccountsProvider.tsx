import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import {
  addCashAccount as addCashAccountApi,
  deleteCashAccount as deleteCashAccountApi,
  fetchCashAccounts as fetchCashAccountsApi,
  updateCashAccount as updateCashAccountApi,
} from '../services/api/cashAccounts'
import { toReadableMessage } from '../utils/errors'
import type { CashAccount } from '../types/entities'
import type {
  AddCashAccountRequest,
  UpdateCashAccountRequest,
} from '../types/api'
import {
  CashAccountsContext,
  type CashAccountsContextValue,
} from './CashAccountsContext'

export function CashAccountsProvider({ children }: { children: ReactNode }) {
  const [accounts, setAccounts] = useState<CashAccount[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fetchedRef = useRef(false)
  const [isFetched, setIsFetched] = useState(false)

  const fetchAccounts = useCallback(async (opts?: { force?: boolean }) => {
    const force = opts?.force ?? false
    if (!force && fetchedRef.current) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchCashAccountsApi()
      setAccounts(data.accounts)
      fetchedRef.current = true
      setIsFetched(true)
    } catch (err) {
      setError(toReadableMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  const addAccount = useCallback(
    async (payload: AddCashAccountRequest): Promise<CashAccount> => {
      const created = await addCashAccountApi(payload)
      await fetchAccounts({ force: true })
      return created
    },
    [fetchAccounts],
  )

  const updateAccount = useCallback(
    async (
      accountId: number,
      payload: UpdateCashAccountRequest,
    ): Promise<CashAccount> => {
      const updated = await updateCashAccountApi(accountId, payload)
      await fetchAccounts({ force: true })
      return updated
    },
    [fetchAccounts],
  )

  const deleteAccount = useCallback(
    async (accountId: number) => {
      await deleteCashAccountApi(accountId)
      await fetchAccounts({ force: true })
    },
    [fetchAccounts],
  )

  const value = useMemo<CashAccountsContextValue>(
    () => ({
      accounts,
      loading,
      error,
      isFetched,
      fetchAccounts,
      addAccount,
      updateAccount,
      deleteAccount,
    }),
    [
      accounts,
      loading,
      error,
      isFetched,
      fetchAccounts,
      addAccount,
      updateAccount,
      deleteAccount,
    ],
  )

  return (
    <CashAccountsContext.Provider value={value}>
      {children}
    </CashAccountsContext.Provider>
  )
}
