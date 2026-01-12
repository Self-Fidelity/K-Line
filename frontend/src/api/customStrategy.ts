/**
 * 自定义策略 API
 */
import apiClient from './client'

export interface CustomStrategyInfo {
  id: number
  user_id: number
  name: string
  description: string
  detailed_description?: string
  parameter_descriptions?: Record<string, string>
  is_public: boolean
  is_system: boolean
  created_at: string
  updated_at?: string | null
}

export interface CustomStrategyDetail extends CustomStrategyInfo {
  code: string
}

export interface CustomStrategyCreate {
  name: string
  description: string
  detailed_description?: string
  code: string
  parameter_descriptions?: Record<string, string>
  is_public?: boolean
}

export interface CustomStrategyUpdate {
  name?: string
  description?: string
  detailed_description?: string
  code?: string
  parameter_descriptions?: Record<string, string>
  is_public?: boolean
}

export interface ValidateRequest {
  code: string
  test_data?: boolean
}

export interface ValidateResponse {
  valid: boolean
  errors: string[]
  warnings: string[]
  strategy_name?: string
  strategy_description?: string
}

export interface CustomStrategyListResponse {
  strategies: CustomStrategyInfo[]
  total: number
}

// 注意：后端路径前缀为 /api/custom-strategy (连字符)，且遵循RESTful规范
export const customStrategyAPI = {
  // 获取策略列表
  getList: async () => {
    return apiClient.get<CustomStrategyListResponse>('/api/custom-strategy')
  },

  // 获取策略详情
  getDetail: async (id: number) => {
    return apiClient.get<CustomStrategyDetail>(`/api/custom-strategy/${id}`)
  },

  // 创建策略
  create: async (data: CustomStrategyCreate) => {
    return apiClient.post<CustomStrategyInfo>('/api/custom-strategy', data)
  },

  // 更新策略
  update: async (id: number, data: CustomStrategyUpdate) => {
    return apiClient.put<CustomStrategyInfo>(`/api/custom-strategy/${id}`, data)
  },

  // 删除策略
  delete: async (id: number) => {
    return apiClient.delete(`/api/custom-strategy/${id}`)
  },

  // 验证策略代码
  validate: async (data: ValidateRequest) => {
    return apiClient.post<ValidateResponse>('/api/custom-strategy/validate', data)
  }
}
