import type {
  AssetCategory,
  AssetCurrency,
  CashOrIncomeCurrency,
  IncomeCategory,
} from './enums'

export interface SymbolLookupResponse {
  symbol: string
  name: string
  currency: AssetCurrency
  category: AssetCategory
  current_price_original: number
  exchange_rate_to_cny: number
  usd_to_cny: number
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

export interface UpdateUserSettingsRequest {
  target_monthly_living?: number
  target_living_currency?: CashOrIncomeCurrency
  target_passive_income?: number
  target_passive_currency?: CashOrIncomeCurrency
  target_cash_savings?: number
  target_cash_currency?: CashOrIncomeCurrency
  email?: string | null
}

export interface AddCashAccountRequest {
  name: string
  amount: number
  currency: CashOrIncomeCurrency
}

export interface UpdateCashAccountRequest {
  name?: string
  amount?: number
  currency?: CashOrIncomeCurrency
}

export interface AddIncomeRequest {
  date: string
  name: string
  category: IncomeCategory
  amount: number
  currency: CashOrIncomeCurrency
  note: string | null
}
