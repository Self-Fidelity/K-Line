/**
 * 图表相关API
 */

import apiClient from './client'

export interface ChartGenerateRequest {
  stock_code: string
  stock_name?: string
  start_date?: string
  end_date?: string
  strategy_name?: string
  strategy_params?: Record<string, any>
  chart_type?: string  // 'kline' or 'kline_with_ma'
  ma_periods?: number[]
}

export interface ChartGenerateResponse {
  chart_id: string
  chart_url: string
  message: string
}

export interface ChartEmbedResponse {
  chart_url: string
  embed_code: string
}

export const chartAPI = {
  /**
   * 生成图表
   */
  generateChart: async (request: ChartGenerateRequest): Promise<ChartGenerateResponse> => {
    const response = await apiClient.post<ChartGenerateResponse>('/api/chart/generate', request)
    return response.data
  },

  /**
   * 获取图表嵌入代码
   */
  getChartEmbedCode: async (chartId: string): Promise<ChartEmbedResponse> => {
    const response = await apiClient.get<ChartEmbedResponse>(`/api/chart/embed/${chartId}`)
    return response.data
  },
}
