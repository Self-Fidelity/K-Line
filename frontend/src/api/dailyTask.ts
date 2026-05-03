/**
 * 每日任务 API（仅管理员）
 */

import apiClient from './client'

export interface DailyTaskStatus {
  last_run: {
    time: string | null
    elapsed_seconds: number
    stocks_scanned: number
    buy_signals: number
    errors: number
    status: string
    error?: string
  } | null
  run_history: Array<{
    time: string
    elapsed_seconds: number
    stocks_scanned: number
    buy_signals: number
    status: string
    error?: string
  }>
  last_buy_signals: Array<{
    stock_code: string
    stock_name: string
    score: number
    strategies: string[]
  }>
  is_running: boolean
  config: { hour: number; minute: number }
  email_enabled: boolean
  progress: {
    phase: string
    stock_index: number
    stock_total: number
    stock_code: string
    strategy_index: number
    strategy_total: number
    strategy_name: string
    elapsed: number
  }
}

export const dailyTaskAPI = {
  getStatus: async (): Promise<DailyTaskStatus> => {
    const response = await apiClient.get<DailyTaskStatus>('/api/admin/daily-task/status')
    return response.data
  },

  triggerRun: async (): Promise<any> => {
    const response = await apiClient.post('/api/admin/daily-task/run')
    return response.data
  },

  getProgress: async (): Promise<DailyTaskStatus['progress']> => {
    const response = await apiClient.get('/api/admin/daily-task/progress')
    return response.data
  },

  toggleEmail: async (enabled: boolean): Promise<{ email_enabled: boolean }> => {
    const response = await apiClient.post('/api/admin/daily-task/toggle-email', { enabled })
    return response.data
  },
}
