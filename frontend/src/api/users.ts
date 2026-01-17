import apiClient from './client'
import type { UserInfo } from '@/api/auth'

export interface UserCreateParams {
    username: string
    email: string
    password: string
    role?: string
    max_watchlist_count?: number
}

export interface UserUpdateParams {
    email?: string
    password?: string
    role?: string
    max_watchlist_count?: number
    is_active?: boolean
}

export const userAPI = {
    // 获取用户列表 (仅管理员)
    listUsers: async (skip: number = 0, limit: number = 100): Promise<UserInfo[]> => {
        const response = await apiClient.get<UserInfo[]>('/api/admin/users/', { params: { skip, limit } })
        return response.data
    },

    // 更新用户 (仅管理员)
    updateUser: async (userId: number, data: UserUpdateParams): Promise<UserInfo> => {
        const response = await apiClient.put<UserInfo>(`/api/admin/users/${userId}`, data)
        return response.data
    },

    // 创建用户 (仅管理员)
    createUser: async (data: UserCreateParams): Promise<UserInfo> => {
        const response = await apiClient.post<UserInfo>('/api/auth/register', data)
        return response.data
    },

    // 删除用户 (仅管理员)
    deleteUser: async (userId: number): Promise<void> => {
        await apiClient.delete(`/api/admin/users/${userId}`)
    }
}
