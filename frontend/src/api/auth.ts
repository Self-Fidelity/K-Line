/**
 * 认证相关API
 */

import apiClient from './client'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  email: string
  role: string
  max_watchlist_count: number
  is_active: boolean
  created_at: string
}

export const authAPI = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('username', data.username)
    formData.append('password', data.password)
    const response = await apiClient.post<LoginResponse>('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/auth/logout')
  },

  getCurrentUser: async (): Promise<UserInfo> => {
    const response = await apiClient.get<UserInfo>('/api/auth/me')
    return response.data
  },
}
