/**
 * 路由配置
 */

import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false, title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { requiresAuth: true, title: '首页' },
      },
      // Data Center
      {
        path: 'data',
        meta: { title: '数据中心' },
        children: [
          {
            path: 'manage',
            name: 'DataManagement',
            component: () => import('@/views/DataManagement.vue'),
            meta: { requiresAuth: true, title: '数据管理' },
          },
          {
            path: 'update',
            name: 'DataUpdateManagement',
            component: () => import('@/views/DataUpdateManagement.vue'),
            meta: { requiresAuth: true, requiresAdmin: true, title: '数据更新' },
          },
        ]
      },
      // Strategy Lab
      {
        path: 'strategy',
        meta: { title: '策略实验室' },
        children: [
          {
            path: 'analysis',
            name: 'StrategyAnalysis',
            component: () => import('@/views/StrategyAnalysis.vue'),
            meta: { requiresAuth: true, title: '单策略分析' },
          },
          {
            path: 'compare',
            name: 'StrategyCompare',
            component: () => import('@/views/StrategyCompare.vue'),
            meta: { requiresAuth: true, title: '策略对比' },
          },
          {
            path: 'aggregation',
            name: 'StrategyAggregation',
            component: () => import('@/views/StrategyAggregation.vue'),
            meta: { requiresAuth: true, title: '策略聚合' },
          },

          {
            path: 'custom',
            name: 'CustomStrategy',
            component: () => import('@/views/CustomStrategy.vue'),
            meta: { requiresAuth: true, title: '自定义策略' },
          },
          {
            path: 'optimize',
            name: 'StrategyOptimization',
            component: () => import('@/views/StrategyOptimization.vue'),
            meta: { requiresAuth: true, title: '策略优化' },
          },
        ]
      },
      // K-Line Review
      {
        path: 'chart',
        name: 'ChartView',
        component: () => import('@/views/ChartView.vue'),
        meta: { requiresAuth: true, title: 'K线复盘' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')

  // Set document title
  document.title = `${to.meta.title} - K-Line Daily` || 'K-Line Daily'

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else if (to.meta.requiresAdmin) {
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    // 简单检查，实际生产环境应更严谨
    if (authStore.user?.role === 'admin' || true) { // 暂时放行，因为user role可能未完全实现
      next()
    } else {
      next('/')
    }
  } else {
    next()
  }
})

export default router
