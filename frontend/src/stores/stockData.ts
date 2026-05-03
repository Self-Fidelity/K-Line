/**
 * 股票数据缓存 Store
 *
 * 缓存股票列表避免每次页面导航都重新请求 3000+ 只股票数据。
 * 默认 TTL 5 分钟，管理员刷新时强制更新。
 */

import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'
import { dataAPI, type StockInfo } from '@/api/data'

interface StockListCache {
  stocks: StockInfo[]
  total: number
  fetchedAt: number
}

const CACHE_TTL_MS = 5 * 60 * 1000 // 5 分钟

export const useStockDataStore = defineStore('stockData', () => {
  /** 按市场缓存的股票列表 */
  const cache = ref<Record<string, StockListCache>>({})

  /** 当前加载中 */
  const loading = ref(false)

  /**
   * 获取股票列表（优先使用缓存）
   */
  async function getStockList(market = 'main', forceRefresh = false): Promise<StockListCache> {
    const cached = cache.value[market]

    // 缓存有效且未过期
    if (
      !forceRefresh &&
      cached &&
      cached.stocks.length > 0 &&
      Date.now() - cached.fetchedAt < CACHE_TTL_MS
    ) {
      return cached
    }

    loading.value = true
    try {
      const response = await dataAPI.getStockList(market)
      const entry: StockListCache = {
        stocks: response.stocks,
        total: response.total,
        fetchedAt: Date.now(),
      }
      cache.value[market] = entry
      return entry
    } finally {
      loading.value = false
    }
  }

  /**
   * 管理员刷新股票列表（强制从 API 拉取）
   */
  async function refreshStockList(market = 'main'): Promise<StockListCache> {
    loading.value = true
    try {
      const response = await dataAPI.refreshStockList(market)
      const entry: StockListCache = {
        stocks: response.stocks,
        total: response.total,
        fetchedAt: Date.now(),
      }
      cache.value[market] = entry
      return entry
    } finally {
      loading.value = false
    }
  }

  /** 清除所有缓存 */
  function clearCache() {
    cache.value = {}
  }

  return { cache, loading, getStockList, refreshStockList, clearCache }
})
