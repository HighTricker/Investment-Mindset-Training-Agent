export type InputUnit = 'shares' | 'USD' | 'CNY'

export interface ConvertParams {
  input: number
  unit: InputUnit
  price: number
  rateToCny: number
  usdToCny: number
}

/**
 * 将用户输入的"股数 / USD 金额 / CNY 金额"换算成 DB 所需的 quantity（股数）。
 *
 * shares: quantity = input
 * USD   : quantity = (input × usdToCny) ÷ rateToCny ÷ price
 * CNY   : quantity = input ÷ rateToCny ÷ price
 */
export function inputToQuantity({
  input,
  unit,
  price,
  rateToCny,
  usdToCny,
}: ConvertParams): number {
  if (!Number.isFinite(input) || input <= 0) return 0
  if (!Number.isFinite(price) || price <= 0) return 0
  if (!Number.isFinite(rateToCny) || rateToCny <= 0) return 0
  if (unit === 'shares') return input
  if (unit === 'USD') {
    if (!Number.isFinite(usdToCny) || usdToCny <= 0) return 0
    return (input * usdToCny) / rateToCny / price
  }
  if (unit === 'CNY') return input / rateToCny / price
  return 0
}

export const UNIT_LABELS: Record<InputUnit, string> = {
  shares: '股',
  USD: 'USD',
  CNY: 'CNY',
}

/**
 * 给定 unit 返回输入框的 label 文案。
 */
export function quantityFieldLabel(unit: InputUnit, action: 'buy' | 'sell' = 'buy'): string {
  if (unit === 'shares') {
    return action === 'buy' ? '数量（股）' : '数量（股）'
  }
  const verb = action === 'buy' ? '投入' : '减持'
  return `${verb}金额（${unit}）`
}
