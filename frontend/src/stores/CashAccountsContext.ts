import { createContext } from 'react'
import type { CashAccount } from '../types/entities'
import type {
  AddCashAccountRequest,
  UpdateCashAccountRequest,
} from '../types/api'

export interface CashAccountsContextValue {
  accounts: CashAccount[]
  loading: boolean
  error: string | null
  isFetched: boolean
  fetchAccounts: (opts?: { force?: boolean }) => Promise<void>
  addAccount: (payload: AddCashAccountRequest) => Promise<CashAccount>
  updateAccount: (
    accountId: number,
    payload: UpdateCashAccountRequest,
  ) => Promise<CashAccount>
  deleteAccount: (accountId: number) => Promise<void>
}

export const CashAccountsContext = createContext<
  CashAccountsContextValue | undefined
>(undefined)
