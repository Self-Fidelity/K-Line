/**
 * 自定义策略API
 */

import apiClient from './client'
import type { AxiosResponse } from 'axios'

// 自定义策略信息
export interface CustomStrategyInfo {
  id: number
  user_id: number
  name: string
  description: string
  detailed_description: string
  parameter_descriptions: Record<string, string>
  is_public: boolean
  is_system: boolean
  created_at: string
  updated_at: string | null
}

// 自定义策略详情（包含代码）
export interface CustomStrategyDetail extends CustomStrategyInfo {
  code: string
}

// 创建策略请求
export interface CustomStrategyCreate {
  name: string
  description: string
  detailed_description: string
  code: string
  parameter_descriptions: Record<string, string>
}

// 更新策略请求
export interface CustomStrategyUpdate {
  name?: string
  description?: string
  detailed_description?: string
  code?: string
  parameter_descriptions?: Record<string, string>
}

// 策略列表响应
export interface CustomStrategyListResponse {
  strategies: CustomStrategyInfo[]
  total: number
}

// 策略验证请求
export interface CustomStrategyValidateRequest {
  code: string
  test_data?: boolean
}

// 策略验证响应
export interface CustomStrategyValidateResponse {
  valid: boolean
  errors: string[]
  warnings: string[]
  strategy_name?: string
  strategy_description?: string
}

export const customStrategyAPI = {
  // 获取策略列表
  getList(): Promise<AxiosResponse<CustomStrategyListResponse>> {
    return apiClient.get('/api/custom-strategy')
  },

  // 获取策略详情
  getDetail(strategyId: number): Promise<AxiosResponse<CustomStrategyDetail>> {
    return apiClient.get(`/api/custom-strategy/${strategyId}`)
  },

  // 创建策略
  create(data: CustomStrategyCreate): Promise<AxiosResponse<CustomStrategyInfo>> {
    return apiClient.post('/api/custom-strategy', data)
  },

  // 更新策略
  update(strategyId: number, data: CustomStrategyUpdate): Promise<AxiosResponse<CustomStrategyInfo>> {
    return apiClient.put(`/api/custom-strategy/${strategyId}`, data)
  },

  // 删除策略
  delete(strategyId: number): Promise<AxiosResponse<void>> {
    return apiClient.delete(`/api/custom-strategy/${strategyId}`)
  },

  // 验证策略代码
  validate(data: CustomStrategyValidateRequest): Promise<AxiosResponse<CustomStrategyValidateResponse>> {
    return apiClient.post('/api/custom-strategy/validate', data)
  },
}
