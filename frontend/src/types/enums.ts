export type TransactionType = 'buy' | 'sell' | 'close'

export type AssetCategory =
  | '美股'
  | '港股'
  | '中概股'
  | '加密货币'
  | '黄金'
  | '美国国债'
  | '中国国债'

export type AssetCurrency = 'CNY' | 'USD' | 'HKD' | 'EUR' | 'GBP' | 'CHF'

export type CashOrIncomeCurrency = 'CNY' | 'USD'

export type IncomeCategory = '纯劳动收入' | '代码&自媒体收入' | '资本收入'

export type ErrorCode =
  | 'INVALID_SYMBOL'
  | 'DUPLICATE_ASSET'
  | 'INSUFFICIENT_POSITION'
  | 'ASSET_NOT_FOUND'
  | 'ACCOUNT_NOT_FOUND'
  | 'EXCHANGE_RATE_MISSING'
  | 'PRICE_MISSING'
  | 'EXTERNAL_SOURCE_FAILED'
  | 'INVALID_EMAIL_FORMAT'
  | 'EMAIL_SEND_FAILED'
  | 'NO_ACTIVE_ASSETS'
  | 'VALIDATION_ERROR'
  | 'INTERNAL_ERROR'
