import { client } from './client'
import type {
  CashAccount,
  CashAccountsListResponse,
} from '../../types/entities'
import type {
  AddCashAccountRequest,
  UpdateCashAccountRequest,
} from '../../types/api'

export async function fetchCashAccounts(): Promise<CashAccountsListResponse> {
  const { data } = await client.get<CashAccountsListResponse>('/cash-accounts')
  return data
}

export async function addCashAccount(
  payload: AddCashAccountRequest,
): Promise<CashAccount> {
  const { data } = await client.post<CashAccount>('/cash-accounts', payload)
  return data
}

export async function updateCashAccount(
  accountId: number,
  payload: UpdateCashAccountRequest,
): Promise<CashAccount> {
  const { data } = await client.put<CashAccount>(
    `/cash-accounts/${accountId}`,
    payload,
  )
  return data
}

export async function deleteCashAccount(accountId: number): Promise<void> {
  await client.delete(`/cash-accounts/${accountId}`)
}
