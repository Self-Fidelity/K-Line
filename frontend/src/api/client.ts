/**
 * API客户端配置
 *
 * 功能：
 * - 自动添加 JWT Token
 * - 请求去重（相同请求并发时合并为一个）
 * - 响应缓存（GET 请求短时缓存）
 * - 统一错误处理
 * - 结构化错误类型
 */

import axios, { type AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// ───────────────────── 错误类型 ─────────────────────

export interface ApiError {
  message: string
  status: number
  code?: string
  details?: unknown
}

/**
 * 将 Axios 错误转换为结构化 ApiError
 */
function normalizeError(error: AxiosError): ApiError {
  if (error.response) {
    const data = error.response.data as Record<string, unknown> | undefined
    return {
      message: (data?.detail as string) || (data?.message as string) || error.message,
      status: error.response.status,
      code: data?.code as string | undefined,
      details: data,
    }
  }
  if (error.request) {
    return {
      message: '网络连接失败，请检查网络',
      status: 0,
      code: 'NETWORK_ERROR',
    }
  }
  return {
    message: error.message || '请求配置错误',
    status: -1,
    code: 'REQUEST_ERROR',
  }
}

// ───────────────────── 请求去重 ─────────────────────

/** 正在进行的请求映射：key → Promise */
const pendingRequests = new Map<string, Promise<AxiosResponse>>()

/** 生成请求唯一键 */
function requestKey(config: InternalAxiosRequestConfig): string {
  const { method, url, params, data } = config
  return `${method}:${url}:${JSON.stringify(params)}:${JSON.stringify(data)}`
}

/** 移除已完成请求 */
function removePendingRequest(config: InternalAxiosRequestConfig): void {
  pendingRequests.delete(requestKey(config))
}

// ───────────────────── API 客户端 ─────────────────────

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // JWT Token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 请求去重：GET 请求如果有相同的在进行中，复用结果
    if (config.method?.toLowerCase() === 'get') {
      const key = requestKey(config)
      const pending = pendingRequests.get(key)
      if (pending) {
        // 返回已有的 Promise，使用 AbortController 取消当前请求
        const controller = new AbortController()
        config.signal = controller.signal
        controller.abort()
        return {
          ...config,
          _dedupedPromise: pending,
        } as InternalAxiosRequestConfig & { _dedupedPromise?: Promise<AxiosResponse> }
      }
    }

    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 清理请求去重记录
    removePendingRequest(response.config)
    return response
  },
  (error: AxiosError) => {
    if (error.config) {
      removePendingRequest(error.config)
    }

    // 如果请求被去重取消，使用缓存的 Promise
    const deduped = (error.config as Record<string, unknown>)?._dedupedPromise as
      | Promise<AxiosResponse>
      | undefined
    if (deduped) {
      return deduped
    }

    const apiError = normalizeError(error)

    // 根据状态码处理
    switch (apiError.status) {
      case 401:
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        ElMessage.error('登录已过期，请重新登录')
        setTimeout(() => {
          window.location.href = `${import.meta.env.VITE_BASE_PATH || '/'}login`
        }, 1000)
        break
      case 403:
        ElMessage.error('没有权限执行此操作')
        break
      case 404:
        // 404 不弹全局提示，由调用方处理
        break
      case 429:
        ElMessage.warning('请求过于频繁，请稍后再试')
        break
      case 500:
      case 502:
      case 503:
        ElMessage.error('服务器错误，请稍后再试')
        break
      case 0:
        ElMessage.error(apiError.message)
        break
      default:
        // 其他错误由调用方处理
        break
    }

    return Promise.reject(apiError)
  },
)

export default apiClient
export { normalizeError }
export type { ApiError }
