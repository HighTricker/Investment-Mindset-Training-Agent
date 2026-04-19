import type {
  AssetCategory,
  AssetCurrency,
  TransactionType,
} from './enums'

export interface Asset {
  asset_id: number
  symbol: string
  name: string
  category: AssetCategory
  currency: AssetCurrency
  is_active: boolean
}

export interface AssetDetail extends Asset {
  initial_investment_cny: number | null
  quantity: number | null
  cost_price_original: number | null
  current_price_original: number | null
  position_ratio: number | null
  exchange_rate_to_cny: number | null
  current_value_cny: number | null
  cumulative_return_rate: number | null
  monthly_return_rate: number | null
}

export interface Transaction {
  transaction_id: number
  asset_id: number
  type: TransactionType
  quantity: number
  price: number
  exchange_rate_to_cny: number
  reason: string | null
  date: string
  created_at: string
}

export interface BestWorstAsset {
  asset_id: number
  symbol: string
  name: string
  category: AssetCategory
  monthly_return_rate: number | null
}

export interface AssetsSummary {
  total_initial_investment_cny: number
  total_current_value_cny: number
  total_return_rate: number | null
  total_profit_loss_cny: number
  best_asset: BestWorstAsset | null
  worst_asset: BestWorstAsset | null
}

export interface AssetsListResponse {
  summary: AssetsSummary
  assets: AssetDetail[]
}

export interface RefreshFailedAsset {
  asset_id: number
  symbol: string
  error: string
}

export interface RefreshFailedCurrency {
  currency: string
  error: string
}

export interface RefreshResponse {
  prices_updated: number
  rates_updated: number
  failed_assets: RefreshFailedAsset[]
  failed_currencies: RefreshFailedCurrency[]
  refreshed_at: string
}
