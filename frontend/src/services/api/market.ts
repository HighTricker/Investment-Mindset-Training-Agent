import { client } from './client'
import type { RefreshResponse } from '../../types/entities'
import type { SymbolLookupResponse } from '../../types/api'

export async function refreshMarket(): Promise<RefreshResponse> {
  const { data } = await client.post<RefreshResponse>('/market/refresh')
  return data
}

export async function lookupSymbol(
  symbol: string,
): Promise<SymbolLookupResponse> {
  const { data } = await client.get<SymbolLookupResponse>(
    '/market/symbol-lookup',
    { params: { symbol } },
  )
  return data
}
