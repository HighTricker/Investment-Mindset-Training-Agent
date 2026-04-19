import { useContext } from 'react'
import {
  IncomeContext,
  type IncomeContextValue,
} from '../stores/IncomeContext'

export function useIncome(): IncomeContextValue {
  const ctx = useContext(IncomeContext)
  if (!ctx) {
    throw new Error('useIncome 必须在 <IncomeProvider> 内使用')
  }
  return ctx
}
