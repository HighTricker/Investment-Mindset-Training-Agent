export const DASH = '—'

const CURRENCY_SYMBOL: Record<string, string> = {
  CNY: '¥',
  USD: '$',
  HKD: 'HK$',
  EUR: '€',
  GBP: '£',
  CHF: 'CHF ',
}

export function formatCurrency(
  value: number | null | undefined,
  currency: string = 'CNY',
): string {
  if (value == null) return DASH
  const symbol = CURRENCY_SYMBOL[currency] ?? ''
  return `${symbol}${value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

export function formatPercent(
  value: number | null | undefined,
  signed = false,
): string {
  if (value == null) return DASH
  const pct = value * 100
  const sign = signed && pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

export function formatNumber(
  value: number | null | undefined,
  decimals = 4,
): string {
  if (value == null) return DASH
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return DASH
  return value.length >= 10 ? value.slice(0, 10) : value
}
