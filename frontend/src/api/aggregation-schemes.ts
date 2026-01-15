import apiClient from './client'

export interface AggregationScheme {
    id: number
    name: string
    description: string
    stock_code: string | null
    strategies: Array<{
        name: string
        weight: number
        params: Record<string, any>
    }>
    buy_threshold: number
    sell_threshold: number
    required_strategies: string[]
    created_at: string
    updated_at: string
}

export interface AggregationSchemeCreate {
    name: string
    description: string
    stock_code?: string
    strategies: Array<{
        name: string
        weight: number
        params: Record<string, any>
    }>
    buy_threshold: number
    sell_threshold: number
    required_strategies: string[]
}

export const aggregationSchemesAPI = {
    /**
     * 创建策略聚合方案
     */
    createScheme: async (data: AggregationSchemeCreate): Promise<{ id: number; message: string }> => {
        const response = await apiClient.post('/api/strategy/aggregation-schemes/', data)
        return response.data
    },

    /**
     * 获取策略聚合方案列表
     */
    getSchemes: async (stockCode?: string): Promise<AggregationScheme[]> => {
        const params = stockCode ? { stock_code: stockCode } : {}
        const response = await apiClient.get<AggregationScheme[]>('/api/strategy/aggregation-schemes/', { params })
        return response.data
    },

    /**
     * 删除策略聚合方案
     */
    deleteScheme: async (id: number): Promise<void> => {
        await apiClient.delete(`/api/strategy/aggregation-schemes/${id}`)
    }
}
