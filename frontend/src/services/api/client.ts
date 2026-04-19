import axios from 'axios'

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

export const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
})

client.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
)
