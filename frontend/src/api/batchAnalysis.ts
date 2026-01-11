/**
 * 批量分析相关API
 */

import apiClient from './client'

export interface StrategyBuySignal {
  strategy_name: string
  has_buy_signal: boolean
  latest_signal_date?: string
  signal_type?: string
  error?: string
}

export interface StockBuySignalResult {
  stock_code: string
  stock_name?: string
  success: boolean
  error?: string
  has_buy_signal: boolean
  strategy_signals: StrategyBuySignal[]
  recommended: boolean
}

export interface BatchBuySignalRequest {
  stock_codes: string[]
  strategy_names: string[]
  strategy_params?: Record<string, Record<string, any>>
}

export interface BatchBuySignalResponse {
  total_count: number
  success_count: number
  failed_count: number
  recommended_count: number
  results: StockBuySignalResult[]
  recommended_stocks: StockBuySignalResult[]
}

export const batchAnalysisAPI = {
  checkBuySignals: async (request: BatchBuySignalRequest): Promise<BatchBuySignalResponse> => {
    // 批量检测可能需要较长时间，增加超时时间到5分钟
    const response = await apiClient.post<BatchBuySignalResponse>(
      '/api/batch-analysis/buy-signals',
      request,
      { timeout: 300000 } // 5分钟超时
    )
    return response.data
  },
}
