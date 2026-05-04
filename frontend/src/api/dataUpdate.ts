/**
 * 数据更新管理API（仅管理员）
 */

import apiClient from './client'

export interface DataUpdateConfig {
  // 日K线数据更新
  auto_update_enabled: boolean
  daily_update_hour: number
  daily_update_minute: number

  // 股票列表更新
  stock_list_update_enabled: boolean
  stock_list_update_frequency: 'weekly' | 'daily'
  stock_list_update_hour: number
  stock_list_update_minute: number

  // 爬虫策略
  update_speed_preset: 'slow' | 'normal' | 'fast'
  batch_size: number
  batch_rest_seconds: number
  pre_update_random_wait: number
  incremental_update: boolean

  // 数据源配置
  data_source: 'akshare' | 'tushare'
}

export interface SchedulerStatus {
  running: boolean
  jobs: Array<{
    id: string
    name: string
    next_run_time: string | null
  }>
}

export interface ManualUpdateRequest {
  update_type: 'stock_list' | 'daily_data' | 'all'
  market?: string
  stock_codes?: string[]
}

export interface DataSourceConfig {
  data_source: 'akshare' | 'tushare'
  tushare_token: string
}

export interface DataSourceTestResult {
  success: boolean
  message: string
}

export const dataUpdateAPI = {
  // 获取配置
  getConfig: async (): Promise<DataUpdateConfig> => {
    const response = await apiClient.get<DataUpdateConfig>('/api/admin/data-update/config')
    return response.data
  },

  // 更新配置
  updateConfig: async (config: Partial<DataUpdateConfig>): Promise<DataUpdateConfig> => {
    const response = await apiClient.put<DataUpdateConfig>('/api/admin/data-update/config', config)
    return response.data
  },

  // 获取调度器状态
  getSchedulerStatus: async (): Promise<SchedulerStatus> => {
    const response = await apiClient.get<SchedulerStatus>('/api/admin/data-update/scheduler/status')
    return response.data
  },

  // 手动触发更新
  manualUpdate: async (request: ManualUpdateRequest): Promise<any> => {
    const response = await apiClient.post('/api/admin/data-update/manual-update', request)
    return response.data
  },

  // 获取数据源配置
  getDataSourceConfig: async (): Promise<DataSourceConfig> => {
    const response = await apiClient.get<DataSourceConfig>('/api/admin/data-update/data-source')
    return response.data
  },

  // 更新数据源配置
  updateDataSourceConfig: async (config: Partial<DataSourceConfig>): Promise<DataSourceConfig> => {
    const response = await apiClient.put<DataSourceConfig>('/api/admin/data-update/data-source', config)
    return response.data
  },

  // 测试数据源连接
  testDataSource: async (data_source: string): Promise<DataSourceTestResult> => {
    const response = await apiClient.post<DataSourceTestResult>(`/api/admin/data-update/data-source/test?data_source=${data_source}`)
    return response.data
  },

  // 清空指定数据源的历史数据
  clearDataBySource: async (data_source: string): Promise<{ message: string; data_source: string; deleted_count: number }> => {
    const response = await apiClient.post(`/api/admin/data-update/data-source/clear?data_source=${data_source}`)
    return response.data
  },
}

// 速度档位预设（与后端保持一致）
export const SPEED_PRESETS = {
  slow: { base: 5.0, jitterMin: 2.0, jitterMax: 5.0, label: '慢速（N100推荐）', desc: '约 7~10 秒/只' },
  normal: { base: 2.0, jitterMin: 1.0, jitterMax: 2.0, label: '标准', desc: '约 3~4 秒/只' },
  fast: { base: 0.5, jitterMin: 0.2, jitterMax: 0.5, label: '快速', desc: '约 0.7~1 秒/只' },
}

// 预估全量更新耗时（5512只股票）
export function estimateDuration(
  preset: 'slow' | 'normal' | 'fast',
  batchSize: number,
  batchRest: number,
): string {
  const totalStocks = 5512
  const speed = SPEED_PRESETS[preset]
  const avgInterval = speed.base + (speed.jitterMin + speed.jitterMax) / 2
  const totalInterval = totalStocks * avgInterval
  const batchCount = Math.floor(totalStocks / batchSize)
  const totalRest = batchCount * batchRest
  const totalSeconds = totalInterval + totalRest
  const hours = totalSeconds / 3600

  if (hours >= 10) {
    return `约 ${hours.toFixed(1)} 小时（建议夜间运行）`
  } else if (hours >= 1) {
    return `约 ${hours.toFixed(1)} 小时`
  } else {
    return `约 ${(totalSeconds / 60).toFixed(0)} 分钟`
  }
}
