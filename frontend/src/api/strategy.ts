/**
 * 策略相关API
 */

import apiClient from './client'

export interface StrategyInfo {
  name: string
  description: string
  detailed_description?: string
  parameter_descriptions?: Record<string, string>
  is_system: boolean
}

export interface StrategyListResponse {
  strategies: StrategyInfo[]
  total: number
}

export interface StrategyAnalyzeRequest {
  stock_code: string
  start_date?: string
  end_date?: string
  params?: Record<string, any>
}

export interface StrategyAnalyzeResult {
  result: any[]
  statistics: Record<string, any>
}

export interface StrategyAnalyzeResponse {
  strategy_name: string
  stock_code: string
  result: StrategyAnalyzeResult
}

export interface StrategyCompareRequest {
  strategy_names: string[]
  stock_code: string
  start_date?: string
  end_date?: string
  strategy_params?: Record<string, Record<string, any>>
}

export interface StrategyCompareResponse {
  stock_code: string
  start_date?: string
  end_date?: string
  results: StrategyAnalyzeResponse[]
}

export const strategyAPI = {
  listStrategies: async (): Promise<StrategyListResponse> => {
    const response = await apiClient.get<StrategyListResponse>('/api/strategy/list')
    return response.data
  },

  getStrategyInfo: async (strategyName: string): Promise<StrategyInfo> => {
    const response = await apiClient.get<StrategyInfo>(`/api/strategy/${strategyName}/info`)
    return response.data
  },

  analyzeStrategy: async (strategyName: string, request: StrategyAnalyzeRequest): Promise<StrategyAnalyzeResponse> => {
    const response = await apiClient.post<StrategyAnalyzeResponse>(
      '/api/strategy/analyze',
      {
        strategy_name: strategyName,
        ...request,
      }
    )
    return response.data
  },

  compareStrategies: async (request: StrategyCompareRequest): Promise<StrategyCompareResponse> => {
    const response = await apiClient.post<StrategyCompareResponse>('/api/strategy/compare', request)
    return response.data
  },
}
