import { createContext } from 'react'
import type { IncomeListResponse, IncomeRecord } from '../types/entities'
import type { AddIncomeRequest } from '../types/api'

export interface IncomeContextValue {
  data: IncomeListResponse | null
  loading: boolean
  error: string | null
  isFetched: boolean
  fetchIncome: (opts?: { month?: string; force?: boolean }) => Promise<void>
  addIncome: (payload: AddIncomeRequest) => Promise<IncomeRecord>
}

export const IncomeContext = createContext<IncomeContextValue | undefined>(
  undefined,
)
