import apiClient from './client'

export interface AuditLogInfo {
    id: number
    user_id: number | null
    username: string
    action: string
    details: string | null
    ip_address: string | null
    created_at: string
}

export interface AuditLogListResponse {
    logs: AuditLogInfo[]
    total: number
}

export const logsAPI = {
    // 获取日志列表
    async getLogs(limit: number = 20) {
        const response = await apiClient.get<AuditLogListResponse>('/api/logs', { params: { limit } })
        return response.data
    },
}
