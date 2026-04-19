import { client } from './client'
import type { IncomeListResponse, IncomeRecord } from '../../types/entities'
import type { AddIncomeRequest } from '../../types/api'

export async function fetchIncome(month?: string): Promise<IncomeListResponse> {
  const { data } = await client.get<IncomeListResponse>('/income', {
    params: month ? { month } : undefined,
  })
  return data
}

export async function addIncome(
  payload: AddIncomeRequest,
): Promise<IncomeRecord> {
  const { data } = await client.post<IncomeRecord>('/income', payload)
  return data
}
