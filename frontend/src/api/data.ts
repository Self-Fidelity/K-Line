/**
 * 数据相关API
 */

import apiClient from './client'

export interface StockInfo {
  code: string
  name: string
  market?: string
  latest_date?: string  // 最新数据日期
}

export interface StockListResponse {
  stocks: StockInfo[]
  total: number
}

export interface KlineData {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
  pct_chg?: number
  amount?: number
  change?: number
  turnover?: number
}

export const dataAPI = {
  getStockList: async (market: string = 'main'): Promise<StockListResponse> => {
    // 注意：refresh 参数已移除，普通用户只能从数据库读取
    const response = await apiClient.get<StockListResponse>('/api/data/stocks', {
      params: { market },
    })
    return response.data
  },

  // 管理员专用：刷新股票列表（从 akshare API 获取）
  refreshStockList: async (market: string = 'all'): Promise<StockListResponse> => {
    const response = await apiClient.post<StockListResponse>('/api/data/admin/refresh-stock-list', null, {
      params: { market },
    })
    return response.data
  },

  // 管理员专用：批量更新股票数据
  batchUpdateStocks: async (stockCodes?: string[], market?: string): Promise<any> => {
    const response = await apiClient.post('/api/data/admin/batch-update-stocks', {
      stock_codes: stockCodes,
      market: market,
    })
    return response.data
  },

  getStockInfo: async (stockCode: string): Promise<StockInfo> => {
    const response = await apiClient.get<StockInfo>(`/api/data/stocks/${stockCode}`)
    return response.data
  },

  getKlineData: async (
    stockCode: string,
    startDate?: string,
    endDate?: string
  ): Promise<KlineData[]> => {
    const response = await apiClient.get<KlineData[]>(`/api/data/stocks/${stockCode}/kline`, {
      params: { start_date: startDate, end_date: endDate },
    })
    return response.data
  },

  fetchStockData: async (stockCode: string): Promise<{ task_id: string; message: string }> => {
    const response = await apiClient.post<{ task_id: string; message: string }>('/api/data/fetch', {
      stock_code: stockCode,
    })
    return response.data
  },
}
