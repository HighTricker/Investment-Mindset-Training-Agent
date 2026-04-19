import { useContext } from 'react'
import {
  CashAccountsContext,
  type CashAccountsContextValue,
} from '../stores/CashAccountsContext'

export function useCashAccounts(): CashAccountsContextValue {
  const ctx = useContext(CashAccountsContext)
  if (!ctx) {
    throw new Error('useCashAccounts 必须在 <CashAccountsProvider> 内使用')
  }
  return ctx
}
