/**
 * 策略相关API
 */

import apiClient from './client'

export interface StrategyInfo {
  name: string
  description: string
  detailed_description?: string
  parameter_descriptions?: Record<string, string>
  parameters?: Record<string, any>
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

export interface TradeRecord {
  date: string
  type: 'buy' | 'sell'
  price: number
  action?: string
  buy_price?: number
  buy_date?: string
  profit?: number
  profit_rate?: number
}

export interface StrategyStatistics {
  initial_capital: number
  final_equity: number
  cumulative_return: number
  annual_return: number
  max_drawdown: number
  sharpe_ratio: number
  sortino_ratio: number
  win_rate: number
  pl_ratio: number
  total_trades: number

  benchmark_return: number
  benchmark_max_drawdown: number

  // 曲线数据
  equity_curve: number[]
  benchmark_curve: number[]
  dates: string[]
  close_prices: number[]
  trades: TradeRecord[]
  daily_returns: number[]
}

export interface StrategyAnalyzeResult {
  strategy_name: string
  stock_code: string
  start_date?: string
  end_date?: string
  result: any[]
  statistics: StrategyStatistics
}

// StrategyAnalyzeResponse 实际上就是 StrategyAnalyzeResult (根据后端接口定义调整)
// 后端 StrategyAnalyzeResponse 包含 result: List[Dict] 和 statistics: StrategyStatisticsModel
// 这里的结构需要匹配后端返回
export interface StrategyAnalyzeResponse {
  strategy_name: string
  stock_code: string
  stock_name?: string
  start_date?: string
  end_date?: string
  result: any[]
  statistics: StrategyStatistics
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
  results: any[] // 实际上是包含多个 analyze response
}

// New interfaces for optimization
export interface OptimizeRequest {
  stock_code: string
  strategy_name: string
  param_ranges: Record<string, any[]>
  start_date?: string
  end_date?: string
  target_metric?: string
  method?: string
  num_particles?: number
  max_iter?: number
}

export const strategyAPI = {
  listStrategies: async (): Promise<StrategyListResponse> => {
    const response = await apiClient.get<StrategyListResponse>('/api/strategy/list')
    return response.data
  },

  getStrategyInfo: async (strategyName: string): Promise<StrategyInfo> => {
    const response = await apiClient.get<StrategyInfo>(`/api/strategy/${encodeURIComponent(strategyName)}/info`)
    return response.data
  },

  analyzeStrategy: async (strategyName: string, request: StrategyAnalyzeRequest): Promise<StrategyAnalyzeResponse> => {
    const response = await apiClient.post<StrategyAnalyzeResponse>(
      '/api/strategy/analyze',
      {
        strategy_name: strategyName,
        stock_code: request.stock_code,
        start_date: request.start_date,
        end_date: request.end_date,
        strategy_params: request.params
      }
    )
    return response.data
  },

  compareStrategies: async (request: StrategyCompareRequest): Promise<StrategyCompareResponse> => {
    const response = await apiClient.post<StrategyCompareResponse>('/api/strategy/compare', request)
    return response.data
  },

  saveParams: async (stockCode: string, strategyName: string, params: Record<string, any>) => {
    const response = await apiClient.post('/api/strategy/params/save', {
      stock_code: stockCode,
      strategy_name: strategyName,
      params,
    })
    return response.data
  },

  getParams: async (stockCode: string, strategyName: string): Promise<Record<string, any> | null> => {
    const response = await apiClient.get<{ params: Record<string, any> | null }>(
      `/api/strategy/params/${stockCode}/${strategyName}`
    )
    return response.data.params
  },

  optimizeStrategy: async (data: OptimizeRequest): Promise<{ task_id: string; status: string }> => {
    const response = await apiClient.post<{ task_id: string; status: string }>('/api/strategy/optimize', data)
    return response.data
  },

  getOptimizationProgress: async (taskId: string): Promise<any> => {
    const response = await apiClient.get<any>(`/api/strategy/optimize/progress/${taskId}`)
    return response.data
  },
}

// ========== Strategy Aggregation ==========

export interface StrategyWithWeight {
  name: string
  params: Record<string, any>
  weight: number  // Range: 0.1-10.0
}

export interface AggregationSettings {
  buy_threshold: number   // Minimum buy weight to trigger buy
  sell_threshold: number  // Minimum sell weight to trigger sell
  required_strategies: string[]  // Must be present (veto power)
}

export interface AggregationRequest {
  stock_code: string
  start_date: string
  end_date: string
  strategies: StrategyWithWeight[]
  settings: AggregationSettings
}

export interface SignalDetail {
  strategy_name: string
  signal: number  // 1=buy, -1=sell, 0=hold
  weight: number
}

export interface AggregatedSignal {
  date: string
  final_signal: number  // 1=buy, -1=sell, 0=hold
  buy_weight: number
  sell_weight: number
  strategy_details: SignalDetail[]
}

export interface AggregationResponse {
  stock_code: string
  stock_name?: string
  start_date: string
  end_date: string
  aggregated_signals: AggregatedSignal[]
  trade_records: TradeRecord[]
  statistics: {
    total_trades: number
    winning_trades: number
    losing_trades: number
    win_rate: number
    total_return: number
    average_return: number
    max_drawdown?: number
    annualized_return?: number
    sharpe_ratio?: number
    sortino_ratio?: number
    pl_ratio?: number
    benchmark_return?: number
    benchmark_drawdown?: number
  }
  total_weight: number
}

export const strategyAggregationAPI = {
  analyzeAggregation: async (request: AggregationRequest): Promise<AggregationResponse> => {
    const response = await apiClient.post<AggregationResponse>(
      '/api/strategy-aggregation/analyze',
      request
    )
    return response.data
  },
}
