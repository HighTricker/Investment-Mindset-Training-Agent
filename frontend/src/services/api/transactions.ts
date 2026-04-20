import { client } from './client'
import type {
  AddTransactionRequest,
  TransactionResponse,
} from '../../types/api'
import type { AssetTransactionsResponse } from '../../types/entities'

export async function addTransaction(
  payload: AddTransactionRequest,
): Promise<TransactionResponse> {
  const { data } = await client.post<TransactionResponse>(
    '/transactions',
    payload,
  )
  return data
}

export async function fetchAssetTransactions(
  assetId: number,
): Promise<AssetTransactionsResponse> {
  const { data } = await client.get<AssetTransactionsResponse>(
    `/assets/${assetId}/transactions`,
  )
  return data
}
