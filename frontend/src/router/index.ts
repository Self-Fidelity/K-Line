/**
 * 路由配置
 */

import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/components/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'data',
        name: 'DataManagement',
        component: () => import('@/views/DataManagement.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'strategy',
        name: 'StrategyAnalysis',
        component: () => import('@/views/StrategyAnalysis.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'chart',
        name: 'ChartView',
        component: () => import('@/views/ChartView.vue'),
        meta: { requiresAuth: true },
      },
          {
            path: 'compare',
            name: 'StrategyCompare',
            component: () => import('@/views/StrategyCompare.vue'),
            meta: { requiresAuth: true },
          },
          {
            path: 'batch',
            name: 'BatchAnalysis',
            component: () => import('@/views/BatchAnalysis.vue'),
            meta: { requiresAuth: true },
          },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    // 需要认证但未登录，跳转到登录页
    next('/login')
  } else if (to.path === '/login' && token) {
    // 已登录但访问登录页，跳转到首页
    next('/')
  } else {
    next()
  }
})

export default router
