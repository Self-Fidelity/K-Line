/**
 * 股票搜索工具：支持代码、名称、拼音首字母简写搜索
 */

import { pinyin } from 'pinyin-pro'
import type { StockInfo } from '@/api/data'

// 缓存每只股票名称的拼音首字母，避免重复计算
const pinyinCache = new Map<string, string>()

/**
 * 获取股票名称的拼音首字母简写
 * 例如："贵州茅台" -> "gzmt"
 */
export function getPinyinFirstLetters(name: string): string {
  if (pinyinCache.has(name)) {
    return pinyinCache.get(name)!
  }
  try {
    const letters = pinyin(name, {
      pattern: 'first',
      toneType: 'none',
      type: 'array',
    }) as string[]
    const result = letters.join('').toLowerCase()
    pinyinCache.set(name, result)
    return result
  } catch {
    return name.toLowerCase()
  }
}

/**
 * 判断单只股票是否匹配查询条件
 * 支持：代码前缀、名称子串、拼音首字母简写
 */
export function matchStock(stock: StockInfo, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true

  // 1. 代码匹配（前缀或包含）
  if (stock.code.toLowerCase().includes(q)) {
    return true
  }

  // 2. 名称匹配（子串）
  if (stock.name.toLowerCase().includes(q)) {
    return true
  }

  // 3. 拼音首字母简写匹配
  const firstLetters = getPinyinFirstLetters(stock.name)
  if (firstLetters.includes(q)) {
    return true
  }

  return false
}

/**
 * 从股票列表中搜索匹配的股票
 */
export function searchStocks(stocks: StockInfo[], query: string): StockInfo[] {
  const q = query.trim()
  if (!q) return stocks
  return stocks.filter((stock) => matchStock(stock, q))
}
