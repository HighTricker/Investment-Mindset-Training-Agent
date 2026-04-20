import type {
  AssetCategory,
  AssetCurrency,
  CashOrIncomeCurrency,
  IncomeCategory,
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

export interface AssetHeader {
  asset_id: number
  symbol: string
  name: string
  is_active: boolean
}

export interface TransactionDetailItem {
  transaction_id: number
  type: TransactionType
  date: string
  quantity: number
  price: number
  exchange_rate_to_cny: number
  reason: string | null
}

export interface AssetTransactionsResponse {
  asset: AssetHeader
  transactions: TransactionDetailItem[]
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

export interface UserSettings {
  target_monthly_living: number
  target_living_currency: CashOrIncomeCurrency
  target_passive_income: number
  target_passive_currency: CashOrIncomeCurrency
  target_cash_savings: number
  target_cash_currency: CashOrIncomeCurrency
  email: string | null
  updated_at: string
}

export interface CashAccount {
  account_id: number
  name: string
  amount: number
  currency: CashOrIncomeCurrency
  created_at?: string
  updated_at: string
}

export interface CashAccountsListResponse {
  accounts: CashAccount[]
}

export interface IncomeRecord {
  income_id: number
  date: string
  name: string
  category: IncomeCategory
  amount: number
  currency: CashOrIncomeCurrency
  note: string | null
  created_at: string
}

export interface IncomeCategorySummary {
  category: IncomeCategory
  current_month_total_cny: number
  last_month_total_cny: number
  growth_rate: number | null
}

export interface IncomeListResponse {
  view_month: string
  summary: IncomeCategorySummary[]
  records: IncomeRecord[]
}

export interface WealthFreedomAnalysisText {
  line1: string
  line2: string
}

export interface WealthFreedomMetrics {
  achievement_rate: number
  current_hourly_income_cny: number
  target_hourly_income_cny: number
  current_annualized_return_rate: number | null
  required_investment_principal_cny: number | null
  target_total_assets_cny: number
  current_total_cash_cny: number
  current_total_investment_cny: number
  current_total_assets_cny: number
  asset_gap_cny: number
  monthly_savings_cny: number
  predicted_freedom_date: string | null
  years_months_remaining: string | null
  analysis_text: WealthFreedomAnalysisText | null
  has_prediction: boolean
}
