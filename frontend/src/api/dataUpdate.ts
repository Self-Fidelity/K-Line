/**
 * 数据更新管理API（仅管理员）
 */

import apiClient from './client'

export interface DataUpdateConfig {
  auto_update_enabled: boolean
  daily_update_hour: number
  daily_update_minute: number
  stock_list_update_enabled: boolean
  stock_list_update_hour: number
  stock_list_update_minute: number
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
}
