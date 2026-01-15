/**
 * 参数集管理API
 */

import apiClient from './client'

export interface ParamSet {
    id: number
    stock_code: string
    strategy_name: string
    name: string
    description: string
    params: Record<string, any>
    param_ranges: Record<string, [number, number]> | null
    target_metric: string | null
    best_score: number | null
    optimization_method: string | null
    num_particles: number | null
    max_iter: number | null
    date_range: string | null
    created_at: string
    is_default: number
}

export interface ParamSetCreate {
    stock_code: string
    strategy_name: string
    name: string
    description?: string
    params: Record<string, any>
    param_ranges?: Record<string, [number, number]>
    target_metric?: string
    best_score?: number
    optimization_method?: string
    num_particles?: number
    max_iter?: number
    date_range?: string
    is_default?: boolean
}

export interface ParamSetListResponse {
    param_sets: ParamSet[]
    total: number
}

export const paramSetsAPI = {
    /**
     * 创建参数集
     */
    createParamSet: async (data: ParamSetCreate): Promise<ParamSet> => {
        const response = await apiClient.post<ParamSet>('/api/strategy/param-sets', data)
        return response.data
    },

    /**
     * 获取参数集列表
     */
    getParamSets: async (stockCode: string, strategyName: string): Promise<ParamSetListResponse> => {
        const response = await apiClient.get<ParamSetListResponse>(
            `/api/strategy/param-sets/${stockCode}/${strategyName}`
        )
        return response.data
    },

    /**
     * 根据ID获取参数集
     */
    getParamSetById: async (id: number): Promise<ParamSet> => {
        const response = await apiClient.get<ParamSet>(`/api/strategy/param-sets/id/${id}`)
        return response.data
    },

    /**
     * 删除参数集
     */
    deleteParamSet: async (id: number): Promise<void> => {
        await apiClient.delete(`/api/strategy/param-sets/${id}`)
    },

    /**
     * 设置默认参数集
     */
    setDefaultParamSet: async (
        id: number,
        stockCode: string,
        strategyName: string
    ): Promise<void> => {
        await apiClient.put(`/api/strategy/param-sets/${id}/set-default`, {
            stock_code: stockCode,
            strategy_name: strategyName,
        })
    },

    /**
     * 获取默认参数集
     */
    getDefaultParamSet: async (stockCode: string, strategyName: string): Promise<ParamSet> => {
        const response = await apiClient.get<ParamSet>(
            `/api/strategy/param-sets/${stockCode}/${strategyName}/default`
        )
        return response.data
    },
}
