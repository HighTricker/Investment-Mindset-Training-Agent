import axios from 'axios'

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

export const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
})

// 响应拦截器：把后端业务错误码 + HTTP 状态 + URL 打到控制台（dev only），
// 帮助定位；业务错误文案的中文化由 utils/errors.ts 的 toReadableMessage 负责。
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV && axios.isAxiosError(error)) {
      const status = error.response?.status ?? 0
      const url = error.config?.url ?? 'unknown'
      const detail = error.response?.data?.detail as
        | { code?: string; message?: string }
        | undefined
      const code = detail?.code ?? error.code ?? 'UNKNOWN'
      const msg = detail?.message ?? error.message
      // eslint-disable-next-line no-console
      console.warn(`[API] ${status} ${url} → ${code}: ${msg}`)
    }
    return Promise.reject(error)
  },
)
