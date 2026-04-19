import { client } from './client'
import type {
  AddTransactionRequest,
  TransactionResponse,
} from '../../types/api'

export async function addTransaction(
  payload: AddTransactionRequest,
): Promise<TransactionResponse> {
  const { data } = await client.post<TransactionResponse>(
    '/transactions',
    payload,
  )
  return data
}
