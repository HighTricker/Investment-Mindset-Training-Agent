import { client } from './client'
import type { ReportRequest, SendReportResponse } from '../../types/api'

/**
 * POST /api/report/preview → 返回完整 HTML 字符串（text/html）
 * 配合 iframe.srcDoc 渲染预览，不解析成 JSON。
 */
export async function previewReport(sendDate?: string): Promise<string> {
  const payload: ReportRequest = sendDate ? { send_date: sendDate } : {}
  const resp = await client.post('/report/preview', payload, {
    responseType: 'text',
    transformResponse: [(data) => data],
  })
  return resp.data as string
}

/**
 * POST /api/report/send → 同步 SMTP 发送
 */
export async function sendReport(
  sendDate?: string,
): Promise<SendReportResponse> {
  const payload: ReportRequest = sendDate ? { send_date: sendDate } : {}
  const resp = await client.post<SendReportResponse>('/report/send', payload)
  return resp.data
}
