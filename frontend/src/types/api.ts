import type { AssetCategory, AssetCurrency } from './enums'

export interface SymbolLookupResponse {
  symbol: string
  name: string
  currency: AssetCurrency
  category: AssetCategory
  current_price_original: number
  exchange_rate_to_cny: number
}

export interface AddAssetRequest {
  symbol: string
  name: string
  category: AssetCategory
  currency: AssetCurrency
  quantity: number
  price: number
  exchange_rate_to_cny: number
  date: string
  reason: string | null
}

export interface AddAssetResponse {
  asset_id: number
  transaction_id: number
  symbol: string
  name: string
  is_active: boolean
  created_at: string
}

export interface AddTransactionRequest {
  asset_id: number
  type: 'buy' | 'sell'
  quantity: number
  price: number
  exchange_rate_to_cny: number
  date: string
  reason: string | null
}

export interface TransactionResponse {
  transaction_id: number
  asset_id: number
  type: 'buy' | 'sell' | 'close'
  quantity: number
  price: number
  date: string
  created_at: string
}

export interface CloseAssetRequest {
  reason: string | null
}
