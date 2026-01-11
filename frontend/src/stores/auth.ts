/**
 * 认证状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authAPI, type UserInfo } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserInfo | null>(null)
  const isAuthenticated = ref<boolean>(!!token.value)

  const login = async (username: string, password: string) => {
    try {
      const response = await authAPI.login({ username, password })
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      isAuthenticated.value = true
      
      // 获取用户信息
      await fetchUserInfo()
      return true
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      isAuthenticated.value = false
    }
  }

  const fetchUserInfo = async () => {
    try {
      const userInfo = await authAPI.getCurrentUser()
      user.value = userInfo
    } catch (error) {
      console.error('获取用户信息失败:', error)
      token.value = null
      localStorage.removeItem('token')
      isAuthenticated.value = false
    }
  }

  // 初始化时获取用户信息
  if (token.value) {
    fetchUserInfo()
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    fetchUserInfo,
  }
})
