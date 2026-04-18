import axios from 'axios'

/**
 * 后端 API 基础 URL。
 * 开发期固定为本地 8000，生产环境由构建时环境变量覆盖（见 V2 部署）。
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
})

/**
 * 响应拦截器占位：阶段 3 具体页面开发时补全错误码分派
 * （按 `开发文档/react_prompt_schema.md` 格子 7「特殊错误码 UI 响应表」）
 */
api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
)
