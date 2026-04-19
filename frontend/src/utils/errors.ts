import axios from 'axios'
import type { ErrorCode } from '../types/enums'

export interface BusinessError {
  code: ErrorCode
  message: string
  details?: Record<string, unknown>
}

export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  INVALID_SYMBOL: '交易代码无效或未在数据源找到',
  DUPLICATE_ASSET: '该资产已持有，请使用加仓功能',
  INSUFFICIENT_POSITION: '减仓数量超过当前持仓',
  ASSET_NOT_FOUND: '资产不存在',
  ACCOUNT_NOT_FOUND: '账户不存在',
  EXCHANGE_RATE_MISSING: '缺少汇率数据，请先刷新市场',
  PRICE_MISSING: '缺少价格数据，请先刷新市场',
  EXTERNAL_SOURCE_FAILED: '外部数据源暂时无法访问',
  INVALID_EMAIL_FORMAT: '邮箱格式不正确',
  EMAIL_SEND_FAILED: '邮件发送失败',
  NO_ACTIVE_ASSETS: '当前无活跃资产',
  VALIDATION_ERROR: '请求参数不符合要求',
  INTERNAL_ERROR: '服务器内部错误',
}

export function extractBusinessError(err: unknown): BusinessError | null {
  if (!axios.isAxiosError(err)) return null
  const detail = err.response?.data?.detail
  if (
    detail &&
    typeof detail === 'object' &&
    'code' in detail &&
    'message' in detail
  ) {
    return detail as BusinessError
  }
  return null
}

export function toReadableMessage(err: unknown): string {
  const biz = extractBusinessError(err)
  if (biz) {
    return ERROR_MESSAGES[biz.code] ?? biz.message
  }
  if (axios.isAxiosError(err)) {
    if (err.code === 'ERR_NETWORK') return '无法连接后端服务，请确认后端已启动'
    if (err.code === 'ECONNABORTED') return '请求超时，请稍后重试'
  }
  return err instanceof Error ? err.message : '未知错误'
}
