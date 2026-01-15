<template>
  <div class="strategy-analysis">
    <!-- 顶部控制栏 -->
    <el-card class="control-panel" :body-style="{ padding: '15px 20px' }">
      <el-form :model="analysisForm" :inline="true" class="control-form">
        <el-form-item label="策略">
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-popover
              :visible="strategyPopoverVisible"
              placement="bottom-start"
              :width="400"
              trigger="click"
              @show="handlePopoverShow"
              @hide="handlePopoverHide"
            >
              <template #reference>
                <div class="custom-select" @click="strategyPopoverVisible = !strategyPopoverVisible">
                  <span v-if="!analysisForm.strategyName" class="placeholder">
                    请选择策略
                  </span>
                  <span v-else class="selected-text">
                    {{ analysisForm.strategyName }}
                  </span>
                  <el-icon class="arrow-icon" :class="{ 'is-reverse': strategyPopoverVisible }">
                    <ArrowDown />
                  </el-icon>
                </div>
              </template>
              
              <div class="strategy-selector">
                <!-- 搜索栏 -->
                <div class="selector-header">
                  <el-input
                    v-model="strategySearchQuery"
                    placeholder="搜索策略..."
                    size="small"
                    clearable
                    style="flex: 1"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                </div>
                
                <!-- 策略列表 -->
                <div class="strategy-list">
                  <el-radio-group v-model="analysisForm.strategyName" @change="handleStrategyChangeFromSelector">
                    <div
                      v-for="strategy in filteredStrategies"
                      :key="strategy.name"
                      class="strategy-item"
                    >
                      <el-radio :value="strategy.name">
                        <div class="strategy-info">
                          <div class="strategy-name">{{ strategy.name }}</div>
                          <div class="strategy-desc">{{ strategy.description }}</div>
                        </div>
                      </el-radio>
                    </div>
                  </el-radio-group>
                  <div v-if="filteredStrategies.length === 0" class="empty-text">
                    未找到匹配的策略
                  </div>
                </div>
                
                <!-- 底部操作栏 -->
                <div class="selector-footer">
                  <el-button size="small" @click="strategyPopoverVisible = false">
                    确定
                  </el-button>
                </div>
              </div>
            </el-popover>
            <el-tooltip v-if="currentStrategyInfo" :content="currentStrategyInfo.detailed_description || currentStrategyInfo.description" placement="top" :raw-content="true">
              <template #content>
                <div style="max-width: 300px; white-space: pre-wrap;">{{ currentStrategyInfo.detailed_description || currentStrategyInfo.description }}</div>
              </template>
              <el-icon style="margin-left: 5px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
        </el-form-item>

        <el-form-item label="股票">
          <div style="display: flex; gap: 5px; align-items: center;">
            <el-dropdown trigger="click" @command="handleFavoriteSelect">
              <el-button :icon="Collection" circle title="我的收藏" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="favorites.length === 0" disabled>暂无收藏</el-dropdown-item>
                  <el-dropdown-item 
                    v-for="fav in favorites" 
                    :key="fav.id" 
                    :command="fav"
                  >
                    {{ fav.stock_code }} - {{ fav.stock_name || '未知' }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <el-autocomplete
              v-model="analysisForm.stockCode"
              :fetch-suggestions="searchStocks"
              placeholder="代码/名称"
              style="width: 180px"
              @select="handleStockSelect"
            >
              <template #default="{ item }">
                <span class="stock-code">{{ item.code }}</span>
                <span class="stock-name">{{ item.name }}</span>
              </template>
            </el-autocomplete>

            <el-button 
                :type="isFavorite ? 'warning' : 'default'" 
                :icon="isFavorite ? StarFilled : Star" 
                circle 
                @click="toggleFavorite"
                :disabled="!analysisForm.stockCode"
                title="收藏当前股票"
            />
          </div>
        </el-form-item>

        <el-form-item label="时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            style="width: 260px"
            @change="handleDateRangeChange"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleAnalyze" :loading="analyzing">
            <el-icon><DataAnalysis /></el-icon> 分析
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="main-content">
      <!-- 左侧图表区域 -->
      <div class="chart-section">
        <el-card class="chart-card" :body-style="{ padding: '0', height: '100%' }">
          <div class="chart-tabs">
            <el-radio-group v-model="activeChartTab" size="small">
              <el-radio-button value="kline">K线图 & 信号</el-radio-button>
              <el-radio-button value="equity">收益率曲线</el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="chart-wrapper">
            <div v-if="analyzing" class="empty-chart">
              <el-empty description="正在分析中..." />
            </div>
            <div v-else-if="!analysisResult" class="empty-chart">
              <el-empty description="请选择策略和股票进行分析" />
            </div>
            <div v-else-if="activeChartTab === 'kline' && klineData.length === 0" class="empty-chart">
              <el-empty description="暂无K线数据" />
            </div>
            <div v-else-if="activeChartTab === 'equity' && equityLines.length === 0" class="empty-chart">
              <el-empty description="暂无权益曲线数据" />
            </div>
            <KlineChart
              v-if="activeChartTab === 'kline' && klineData.length > 0"
              :key="`kline-${analysisResult?.stock_code}-${analysisResult?.strategy_name}-${Date.now()}`"
              :data="klineData"
              :markers="signalMarkers"
              :lines="indicatorLines"
              autosize
              :watermark="watermarkText"
              :darkMode="isDark"
              :showSubChart="false" 
              :simpleLegend="true"
            />
            <KlineChart
              v-if="activeChartTab === 'equity' && equityLines.length > 0"
              :key="`equity-${analysisResult?.stock_code}-${analysisResult?.strategy_name}-${Date.now()}`"
              :data="[]"
              :lines="equityLines"
              autosize
              :watermark="watermarkText"
              :darkMode="isDark"
              :showSubChart="false" 
              :simpleLegend="true"
            />
          </div>
        </el-card>
      </div>

      <!-- 右侧信息区域 -->
      <div class="info-section">
        <!-- 策略统计 -->
        <el-card class="info-card" v-if="analysisResult?.statistics">
          <template #header>
            <div class="card-title">策略表现</div>
          </template>
          
          <div class="stats-grid">
            <div class="stat-item">
              <div class="label">
                累计收益
                <el-tooltip content="策略在回测区间内的总收益率" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value" :class="getColorClass(analysisResult.statistics.cumulative_return)">
                {{ formatNumber(analysisResult.statistics.cumulative_return) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                最大回撤
                <el-tooltip content="策略净值从最高点回落的最大幅度，反映最大潜在亏损风险" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value down">
                {{ formatNumber(analysisResult.statistics.max_drawdown) }}%
              </div>
            </div>
             <div class="stat-item">
              <div class="label">
                年化收益
                <el-tooltip content="将累计收益率换算成一年的平均收益率" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value" :class="getColorClass(analysisResult.statistics.annual_return)">
                {{ formatNumber(analysisResult.statistics.annual_return) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                夏普比率
                <el-tooltip content="衡量承担单位风险所获得的超额回报，数值越高越好 (>1 较好, >2 优秀)" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value">
                {{ formatNumber(analysisResult.statistics.sharpe_ratio) }}
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                索提诺比率
                <el-tooltip content="类似于夏普比率，但只考虑下行风险（亏损波动），更能反映真实的风险收益比" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value">
                {{ formatNumber(analysisResult.statistics.sortino_ratio) }}
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                盈亏比
                <el-tooltip content="平均盈利金额与平均亏损金额的比值，反映策略赚取的利润是否足以覆盖亏损" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value">
                {{ formatNumber(analysisResult.statistics.pl_ratio) }}
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                胜率
                <el-tooltip content="盈利交易次数占总交易次数的百分比" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value" :class="getColorClass(analysisResult.statistics.win_rate - 50)">
                {{ formatNumber(analysisResult.statistics.win_rate) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                交易次数
                <el-tooltip content="回测区间内产生的总买卖信号对次数" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value">{{ analysisResult.statistics.total_trades }}</div>
            </div>
             <div class="stat-item">
              <div class="label">
                基准收益
                <el-tooltip content="同期持有标的股票（买入并持有）的收益率，用于对比策略表现" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value" :class="getColorClass(analysisResult.statistics.benchmark_return)">
                {{ formatNumber(analysisResult.statistics.benchmark_return) }}%
              </div>
            </div>
             <div class="stat-item">
              <div class="label">
                基准回撤
                <el-tooltip content="同期持有标的股票的最大回撤" placement="top">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="value down">
                {{ formatNumber(analysisResult.statistics.benchmark_max_drawdown) }}%
              </div>
            </div>
          </div>
        </el-card>

        <!-- 参数配置 -->
        <el-card class="info-card" v-if="currentStrategyInfo">
          <template #header>
            <div class="card-title" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
              <div>
                <span>参数配置</span>
                <el-tooltip content="配置策略的运行参数，不同的参数会影响策略的买卖点判断" placement="top">
                  <el-icon><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              
              <el-popover
                placement="bottom"
                :width="400"
                trigger="click"
                @show="loadSavedParams"
              >
                <template #reference>
                  <el-button type="primary" link size="small">
                    <el-icon><Download /></el-icon> 加载优化参数
                  </el-button>
                </template>
                
                <div v-loading="loadingParamSets">
                   <div v-if="availableParamSets.length === 0" style="text-align: center; color: #909399; padding: 10px;">
                      暂无该策略的优化记录
                   </div>
                   <div v-else class="param-sets-list" style="max-height: 300px; overflow-y: auto;">
                      <div v-for="set in availableParamSets" :key="set.id" 
                           style="padding: 8px; cursor: pointer; border-bottom: 1px solid var(--el-border-color-lighter);"
                           @click="applyParamSet(set)"
                           class="param-set-item"
                      >
                         <div style="display: flex; justify-content: space-between;">
                            <span style="font-weight: bold;">{{ set.name }}</span>
                            <span style="color: var(--el-color-success); font-size: 13px;">
                               {{ getParamMetricLabel(set.target_metric) }}: {{ set.best_score?.toFixed(2) }}
                            </span>
                         </div>
                         <div style="font-size: 12px; color: var(--el-text-color-secondary);">
                            {{ set.date_range || '无日期范围' }}
                         </div>
                      </div>
                   </div>
                </div>
              </el-popover>
            </div>
          </template>
          
          <div v-if="Object.keys(strategyParams).length === 0" style="color: #909399; padding: 20px; text-align: center">
            该策略无需额外参数配置
          </div>
          <el-form v-else size="small" label-position="top">
            <el-form-item
              v-for="(_, key) in strategyParams"
              :key="key"
            >
              <template #label>
                 <span>{{ getParameterLabel(key) }}</span>
                 <el-tooltip v-if="currentStrategyInfo?.parameter_descriptions?.[key]" :content="typeof currentStrategyInfo.parameter_descriptions[key] === 'string' ? currentStrategyInfo.parameter_descriptions[key] : (currentStrategyInfo.parameter_descriptions[key] as any)?.description || ''" placement="top">
                   <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                 </el-tooltip>
              </template>
              <el-input-number 
                v-model="strategyParams[key]" 
                style="width: 100%"
                controls-position="right"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 交易记录简表 -->
        <el-card class="info-card trade-list-card" v-if="analysisResult?.statistics?.trades?.length">
          <template #header>
            <div class="card-title">最近交易</div>
          </template>
          <div class="trade-list">
            <div 
              v-for="(trade, index) in reversedTrades.slice(0, 10)" 
              :key="index"
              class="trade-item"
            >
              <div class="trade-header">
                <span class="trade-date">{{ trade.date }}</span>
                <el-tag size="small" :type="trade.type === 'buy' ? 'success' : (trade.profit_rate && trade.profit_rate > 0 ? 'danger' : 'success')">
                  {{ trade.type === 'buy' ? '买入' : `卖出 ${trade.profit_rate?.toFixed(2)}%` }}
                </el-tag>
              </div>
              <div class="trade-details">
                <span>价格: {{ trade.price?.toFixed(2) }}</span>
                <span v-if="trade.type === 'sell' && trade.buy_price">买入价: {{ trade.buy_price?.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, Collection, Star, StarFilled, QuestionFilled, ArrowDown, Search, Download
} from '@element-plus/icons-vue'
import { useDark } from '@vueuse/core'
import { strategyAPI, type StrategyInfo, type StrategyAnalyzeResponse } from '@/api/strategy'
import { paramSetsAPI, type ParamSet } from '@/api/param-sets'
import { customStrategyAPI } from '@/api/customStrategy'
import { dataAPI } from '@/api/data'
import { watchlistAPI, type WatchlistItem } from '@/api/watchlist'
import KlineChart, { type ChartData, type Marker, type LineData } from '@/components/KlineChart.vue'

const isDark = useDark()

// --- State ---
const strategies = ref<StrategyInfo[]>([])
const systemStrategies = ref<StrategyInfo[]>([])
const customStrategies = ref<StrategyInfo[]>([])
const currentStrategyInfo = ref<StrategyInfo | null>(null)
const strategyParams = reactive<Record<string, number>>({})
const strategyPopoverVisible = ref(false)
const strategySearchQuery = ref('')
const analyzing = ref(false)
const analysisResult = ref<StrategyAnalyzeResponse | null>(null)
// Param sets state
const loadingParamSets = ref(false)
const availableParamSets = ref<ParamSet[]>([])

const activeChartTab = ref<'kline' | 'equity'>('kline')
const dateRange = ref<[string, string]>(['', ''])

const analysisForm = reactive({
  strategyName: '',
  stockCode: '',
  startDate: '',
  endDate: ''
})

// Watchlist
const favorites = ref<WatchlistItem[]>([])
const isFavorite = computed(() => {
    if (!analysisForm.stockCode) return false
    return favorites.value.some(f => f.stock_code === analysisForm.stockCode)
})

const loadFavorites = async () => {
    try {
        const res = await watchlistAPI.getWatchlist()
        favorites.value = res
    } catch (e) {
        console.error('加载收藏列表失败', e)
    }
}

const toggleFavorite = async () => {
    if (!analysisForm.stockCode) return
    try {
        if (isFavorite.value) {
            await watchlistAPI.removeFromWatchlist(analysisForm.stockCode)
            ElMessage.success('已取消收藏')
        } else {
            await watchlistAPI.addToWatchlist(analysisForm.stockCode)
            ElMessage.success('已收藏')
        }
        loadFavorites()
    } catch (e: any) {
        ElMessage.error(e.response?.data?.detail || '操作失败')
    }
}

const handleFavoriteSelect = (fav: WatchlistItem) => {
  analysisForm.stockCode = fav.stock_code
}

// 策略选择器相关
const filteredStrategies = computed(() => {
  if (!strategySearchQuery.value) {
    return strategies.value
  }
  const query = strategySearchQuery.value.toLowerCase()
  return strategies.value.filter(s => 
    s.name.toLowerCase().includes(query) || 
    s.description.toLowerCase().includes(query)
  )
})

const handlePopoverShow = () => {
  strategySearchQuery.value = ''
}

const handlePopoverHide = () => {
  strategySearchQuery.value = ''
}

const handleStrategyChangeFromSelector = (strategyName: string) => {
  handleStrategyChange(strategyName)
  strategyPopoverVisible.value = false
}

// --- Computed Props ---

const watermarkText = computed(() => {
  if (!analysisResult.value) return 'K-Line Strategy'
  // Return only stock name (or code if name missing)
  return analysisResult.value.stock_name || analysisResult.value.stock_code
})

const klineData = computed<ChartData[]>(() => {
  if (!analysisResult.value?.result || analysisResult.value.result.length === 0) return []
  
  return analysisResult.value.result.map((item: any) => {
    // 处理日期格式：如果是 datetime 对象或 ISO 字符串，转换为 YYYY-MM-DD 格式
    let dateStr = item.date
    if (dateStr) {
      if (typeof dateStr === 'string') {
        // 如果是 ISO 格式字符串，提取日期部分
        if (dateStr.includes('T')) {
          dateStr = dateStr.split('T')[0]
        }
      } else if (dateStr instanceof Date) {
        dateStr = dateStr.toISOString().split('T')[0]
      }
    }
    
    return {
      time: dateStr || '',
      open: Number(item.open) || 0,
      high: Number(item.high) || 0,
      low: Number(item.low) || 0,
      close: Number(item.close) || 0,
      volume: Number(item.volume) || 0,
      pct_chg: item.pct_chg !== undefined && item.pct_chg !== null ? Number(item.pct_chg) : undefined
    }
  }).filter(item => item.time) // 过滤掉没有时间的项
})

const signalMarkers = computed<Marker[]>(() => {
  if (!analysisResult.value?.result) return []
  const markers: Marker[] = []
  
  analysisResult.value.result.forEach((item: any) => {
    // 处理日期格式
    let dateStr = item.date
    if (dateStr) {
      if (typeof dateStr === 'string') {
        if (dateStr.includes('T')) {
          dateStr = dateStr.split('T')[0]
        }
      } else if (dateStr instanceof Date) {
        dateStr = dateStr.toISOString().split('T')[0]
      }
    }
    
    if (!dateStr) return
    
    if (item.signal === 1 || item.signal === '1') {
      markers.push({
        time: dateStr,
        position: 'belowBar',
        color: '#4CAF50',
        shape: 'arrowUp',
        text: 'B'
      })
    } else if (item.signal === -1 || item.signal === '-1') {
      markers.push({
        time: dateStr,
        position: 'aboveBar',
        color: '#F44336',
        shape: 'arrowDown',
        text: 'S'
      })
    }
  })
  return markers
})

const indicatorLines = computed<LineData[]>(() => {
  if (!analysisResult.value?.result || analysisResult.value.result.length === 0) return []
  const data = analysisResult.value.result
  const lines: LineData[] = []
  
  // 自动检测MA等指标列
  const keys = Object.keys(data[0] || {})
  const indicatorKeys = keys.filter(k => {
    const upper = k.toUpperCase()
    return upper.startsWith('MA') || upper.startsWith('EMA') || 
           upper.startsWith('UPPER') || upper.startsWith('LOWER') ||
           upper.startsWith('MIDDLE') || upper.includes('BAND')
  })
  
  const colors = ['#2962FF', '#E91E63', '#FF6D00', '#00B8D4']
  
    indicatorKeys.forEach((key, index) => {
    let lineData = data.map((d: any) => {
      // 处理日期格式
      let dateStr = d.date
      if (dateStr) {
        if (typeof dateStr === 'string') {
          if (dateStr.includes('T')) {
            dateStr = dateStr.split('T')[0]
          }
        } else if (dateStr instanceof Date) {
          dateStr = dateStr.toISOString().split('T')[0]
        }
      }
      
      return {
        time: dateStr || '',
        value: Number(d[key]) || 0
      }
    }).filter((d: any) => d.time && d.value !== null && d.value !== undefined && !isNaN(d.value))
    
    // Filter out leading zero values (common in initial calculation period)
    // Find the first index where value is not 0 (or close to 0)
    const firstValidIndex = lineData.findIndex(d => Math.abs(d.value) > 0.0001);
    if (firstValidIndex > 0) {
      lineData = lineData.slice(firstValidIndex);
    }
    
    if (lineData.length > 0) {
      lines.push({
        name: key,
        data: lineData,
        color: colors[index % colors.length],
        lineWidth: 1
      })
    }
  })
  
  return lines
})

const equityLines = computed<LineData[]>(() => {
  if (!analysisResult.value?.statistics) return []
  const stats = analysisResult.value.statistics
  const dates = stats.dates || []
  const equity = stats.equity_curve || []
  const benchmark = stats.benchmark_curve || []
  
  if (!Array.isArray(dates) || dates.length === 0) return []
  
  const formatDate = (d: string) => {
    if (typeof d === 'string') {
      if (d.includes('T')) {
        return d.split('T')[0]
      }
      return d
    }
    return String(d)
  }
  
  const formatValue = (val: any) => Number(val) || 0
  
  return [
    {
      name: '策略权益',
      data: dates.map((d: string, i: number) => ({
        time: formatDate(d),
        value: formatValue(equity[i])
      })).filter(d => d.time && !isNaN(d.value)),
      color: '#FFD700',
      lineWidth: 2
    },
    {
      name: '基准收益 (Buy&Hold)',
      data: dates.map((d: string, i: number) => ({
        time: formatDate(d),
        value: formatValue(benchmark[i])
      })).filter(d => d.time && !isNaN(d.value)),
      color: '#78909c',
      lineWidth: 1
    }
  ]
})

const reversedTrades = computed(() => {
  if (!analysisResult.value?.statistics?.trades) return []
  return [...analysisResult.value.statistics.trades].reverse()
})



// --- Param Sets Methods ---
const loadSavedParams = async () => {
  if (!analysisForm.strategyName) return
  if (!analysisForm.stockCode) {
    ElMessage.warning('请先选择股票')
    return
  }
  
  loadingParamSets.value = true
  try {
    const res = await paramSetsAPI.getParamSets(analysisForm.stockCode, analysisForm.strategyName)
    availableParamSets.value = res.param_sets
    if (res.param_sets.length === 0) {
      ElMessage.info('暂无该策略的优化参数记录')
    }
  } catch (e: any) {
    ElMessage.error('加载参数记录失败')
  } finally {
    loadingParamSets.value = false
  }
}

const applyParamSet = (set: ParamSet) => {
  // Clear existing params first to ensure clean state
  Object.keys(strategyParams).forEach(k => delete strategyParams[k])
  // Apply new params
  Object.assign(strategyParams, set.params)
  ElMessage.success(`已应用参数: ${set.name}`)
}

const getParamMetricLabel = (val: string | null) => {
  if (!val) return '得分'
  const map: Record<string, string> = {
    'sharpe_ratio': '夏普比率',
    'cumulative_return': '累计收益',
    'sortino_ratio': '索提诺',
    'win_rate': '胜率',
  }
  return map[val] || val
}

// --- Methods ---

const formatNumber = (num: number) => {
  return typeof num === 'number' ? num.toFixed(2) : '--'
}

const getColorClass = (val: number) => {
  return val > 0 ? 'up' : (val < 0 ? 'down' : '')
}

const getParameterLabel = (key: string): string => {
   const labelMap: Record<string, string> = {
    'short_period': '短期周期',
    'long_period': '长期周期',
    'period': '周期',
    'std_dev': '标准差倍数',
    'oversold': '超卖阈值',
    'overbought': '超买阈值',
    'fast_period': '快线周期',
    'slow_period': '慢线周期',
    'signal_period': '信号线周期',
    'shadow_ratio': '影线比例',
    'lookback': '回看周期',
    'doji_threshold': '十字星阈值',
    'up_tolerance': '上涨容忍值',
    'down_tolerance': '下跌容忍值',
  }
  
  // 如果参数描述中有标签，优先使用
  if (currentStrategyInfo.value?.parameter_descriptions?.[key]) {
    const paramDesc = currentStrategyInfo.value.parameter_descriptions[key]
    if (typeof paramDesc === 'object' && (paramDesc as any)?.label) {
      return (paramDesc as any).label
    }
  }
  
  return labelMap[key] || key
}

// 默认参数配置
const defaultParams: Record<string, Record<string, number>> = {
  'MA Strategy': { short_period: 5, long_period: 20 },
  'RSI Strategy': { period: 14, overbought: 70, oversold: 30 },
  'MACD Strategy': { fast_period: 12, slow_period: 26, signal_period: 9 },
  'Bollinger Strategy': { period: 20, std_dev: 2 },
  'Momentum Strategy': { period: 10 },
  'Hammer': { shadow_ratio: 2.0 },
  'Hanging Man': { shadow_ratio: 2.0 },
  'Doji': { lookback: 5, doji_threshold: 0.1 },
  'Bullish Engulfing': {},
  'Bearish Engulfing': {},
  'Morning Star': {},
  'Evening Star': {},
  'Harami': {},
}

// 日期快捷选项
const dateShortcuts = [
  { text: '最近1个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 1); return [start, end]; } },
  { text: '最近3个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 3); return [start, end]; } },
  { text: '最近6个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 6); return [start, end]; } },
  { text: '最近1年', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 12); return [start, end]; } },
]

const loadStrategies = async () => {
  try {
    // 加载所有策略（系统策略 + 自定义策略）
    const sysRes = await strategyAPI.listStrategies()
    
    // 根据 is_system 字段分类
    systemStrategies.value = sysRes.strategies.filter(s => s.is_system === true)
    
    // 加载自定义策略（从自定义策略API获取，确保数据一致性）
    try {
      const customRes = await customStrategyAPI.getList()
      customStrategies.value = customRes.data.strategies.map(s => ({
        ...s,
        is_system: false
      }))
      
      // 去重：如果自定义策略在系统策略列表中也存在（同名），则从系统策略中移除
      const customStrategyNames = new Set(customStrategies.value.map(s => s.name))
      systemStrategies.value = systemStrategies.value.filter(s => !customStrategyNames.has(s.name))
    } catch (e) {
      console.warn('加载自定义策略失败', e)
      // 如果自定义策略API失败，从系统策略列表中过滤出自定义策略
      customStrategies.value = sysRes.strategies.filter(s => s.is_system === false)
    }

    strategies.value = [...systemStrategies.value, ...customStrategies.value]
  } catch (error: any) {
    ElMessage.error('加载策略失败')
  }
}

// 从参数描述中提取默认值
const extractDefaultValue = (paramName: string, description: string): number => {
  // 尝试从描述中提取默认值（例如："默认0.01（1%）"）
  const defaultMatch = description.match(/默认[:\s]*([0-9.]+)/)
  if (defaultMatch) {
    const value = parseFloat(defaultMatch[1])
    if (!isNaN(value)) {
      return value
    }
  }
  
  // 根据参数名推断默认值
  if (paramName.includes('tolerance') || paramName.includes('threshold')) {
    return 0.01  // 容忍值/阈值通常默认0.01
  }
  if (paramName.includes('period')) {
    return 20  // 周期通常默认20
  }
  if (paramName.includes('ratio') || paramName.includes('dev')) {
    return 2.0  // 比率/标准差通常默认2.0
  }
  
  return 1  // 其他参数默认1
}

const handleStrategyChange = async (strategyName: string) => {
  // 重置参数
  Object.keys(strategyParams).forEach(k => delete strategyParams[k])
  
  try {
    // 先在列表中查找，看是系统策略还是自定义策略
    const strategy = strategies.value.find(s => s.name === strategyName)
    
    if (strategy) {
       // 如果已有了详细信息则直接使用，否则请求API
       // 注意：列表返回的信息可能不全，最好还是请求一次详情
       if (strategy.is_system) {
          const info = await strategyAPI.getStrategyInfo(strategyName)
          currentStrategyInfo.value = info
       } else {
          // 自定义策略需要找到ID来获取详情，或者直接使用列表中的信息（如果够的话）
          // 这里假设 name 是唯一的
          // customStrategyAPI.getDetail 需要 id，所以我们得从列表中找到 id
          const customStrategy = customStrategies.value.find(s => s.name === strategyName)
          
          if (customStrategy && 'id' in customStrategy) {
             const res = await customStrategyAPI.getDetail((customStrategy as any).id)
             
             // 转换为 StrategyInfo 格式
             currentStrategyInfo.value = {
                name: res.data.name,
                description: res.data.description,
                detailed_description: res.data.detailed_description,
                parameter_descriptions: res.data.parameter_descriptions,
                is_system: false
             }
          }
       }
    }

    // 设置默认参数
    if (defaultParams[strategyName]) {
      // 系统策略使用预定义的默认参数
      Object.assign(strategyParams, defaultParams[strategyName])
    } else if (currentStrategyInfo.value?.parameter_descriptions) {
      // 自定义策略：从parameter_descriptions中提取参数并设置默认值
      const paramDescs = currentStrategyInfo.value.parameter_descriptions
      
      for (const [key, desc] of Object.entries(paramDescs)) {
        const description = typeof desc === 'string' ? desc : (desc as any)?.description || ''
        strategyParams[key] = extractDefaultValue(key, description)
      }
    }
  } catch (e) {
    console.error('加载策略信息失败:', e)
  }
}

const searchStocks = async (query: string, cb: any) => {
  if (!query) return cb([])
  try {
    const res = await dataAPI.getStockList('all')
    const results = res.stocks
      .filter(s => s.code.includes(query) || s.name.includes(query))
      .slice(0, 10)
      .map(s => ({ value: s.code, code: s.code, name: s.name }))
    cb(results)
  } catch (e) {
    cb([])
  }
}

const handleStockSelect = (item: any) => {
  analysisForm.stockCode = item.code
}

const handleDateRangeChange = (val: any) => {
  if (!val) {
    analysisForm.startDate = ''
    analysisForm.endDate = ''
  } else {
    analysisForm.startDate = val[0]
    analysisForm.endDate = val[1]
  }
}

const handleAnalyze = async () => {
  if (!analysisForm.strategyName || !analysisForm.stockCode) {
    return ElMessage.warning('请补全分析条件')
  }
  
  analyzing.value = true
  try {
    const res = await strategyAPI.analyzeStrategy(analysisForm.strategyName, {
      stock_code: analysisForm.stockCode,
      start_date: analysisForm.startDate || undefined,
      end_date: analysisForm.endDate || undefined,
      params: Object.keys(strategyParams).length ? strategyParams : undefined
    })
    analysisResult.value = res
    ElMessage.success('分析完成')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '分析失败')
  } finally {
    analyzing.value = false
  }
}

const handleReset = () => {
  analysisForm.strategyName = ''
  analysisForm.stockCode = ''
  dateRange.value = ['', '']
  analysisResult.value = null
  currentStrategyInfo.value = null
}

const route = useRoute()

onMounted(async () => {
  await loadStrategies()
  loadFavorites()
  // Default date range: last 6 months
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - 6)
  dateRange.value = [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
  analysisForm.startDate = dateRange.value[0]
  analysisForm.endDate = dateRange.value[1]
  
  // Check query params
  if (route.query.strategy_name) {
    analysisForm.strategyName = route.query.strategy_name as string
    await handleStrategyChange(analysisForm.strategyName)
  }
  if (route.query.stock_code) {
    analysisForm.stockCode = route.query.stock_code as string
  }
  
  // Auto-analyze if both present
  if (analysisForm.strategyName && analysisForm.stockCode) {
    handleAnalyze()
  }
})
</script>

<style scoped>
.strategy-analysis {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.control-panel {
  flex-shrink: 0;
}

.control-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.control-form :deep(.el-form-item) {
  margin-bottom: 0;
  display: flex;
  align-items: center;
}

.control-form :deep(.el-form-item__label) {
  line-height: 32px;
  margin-bottom: 0;
}

.control-form :deep(.el-form-item__content) {
  line-height: 32px;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 15px;
  min-height: 0; /* Important for scroll */
}

.chart-section {
  flex: 3;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chart-section :deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-section :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}
.chart-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-tabs {
  padding: 10px 20px;
  border-bottom: 1px solid #eee;
}

html.dark .chart-tabs {
  border-bottom: 1px solid #333;
}

.chart-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.empty-chart {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-section {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
}

.info-card {
  flex-shrink: 0;
}

.card-title {
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-item .label {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-icon {
  cursor: pointer;
  font-size: 12px;
  color: #909399;
}

.stat-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

html.dark .stat-item .value {
  color: #e0e0e0;
}

.up { color: #f56c6c !important; }
.down { color: #67c23a !important; }

.stock-code {
  float: left;
  color: #909399;
  font-size: 12px;
  margin-right: 10px;
}

.stock-name {
  float: right;
  color: #303133;
}

.trade-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trade-item {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

html.dark .trade-item {
  background: #2d2d2d;
}

.trade-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 12px;
}

.trade-details {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
}

html.dark .trade-details {
  color: #a0a0a0;
}

/* Custom strategy selector styles */
.custom-select {
  width: 300px;
  height: 32px;
  padding: 0 30px 0 12px;
  display: flex;
  align-items: center;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  background-color: var(--el-fill-color-blank);
}

.custom-select:hover {
  border-color: var(--el-border-color-hover);
  background-color: var(--el-fill-color-light);
}

.custom-select .placeholder {
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}

.custom-select .selected-text {
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.custom-select .arrow-icon {
  position: absolute;
  right: 10px;
  transition: transform 0.3s;
  color: var(--el-text-color-secondary);
}

.custom-select .arrow-icon.is-reverse {
  transform: rotate(180deg);
  color: var(--el-color-primary);
}

/* 策略选择器弹出层 */
.strategy-selector {
  display: flex;
  flex-direction: column;
  max-height: 400px;
  background-color: var(--el-bg-color-overlay);
  border-radius: 4px;
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.strategy-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  max-height: 300px;
}

.strategy-list::-webkit-scrollbar {
  width: 6px;
}

.strategy-list::-webkit-scrollbar-thumb {
  background-color: var(--el-border-color-darker);
  border-radius: 3px;
}

.strategy-list::-webkit-scrollbar-thumb:hover {
  background-color: var(--el-border-color-dark);
}

.strategy-item {
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  width: 100%;
}

.strategy-item:hover {
  background-color: var(--el-fill-color-light);
}

.strategy-item :deep(.el-radio) {
  width: 100%;
  height: auto;
  display: block;
}

.strategy-item :deep(.el-radio__input) {
  vertical-align: top;
}

.strategy-item :deep(.el-radio__label) {
  width: 100%;
  white-space: normal;
  line-height: 1.4;
  color: var(--el-text-color-regular);
  display: inline-block;
  vertical-align: top;
}

.strategy-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.strategy-name {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.strategy-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.3;
}

.empty-text {
  text-align: center;
  padding: 20px;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}

.selector-footer {
  padding: 8px 12px;
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  justify-content: flex-end;
}
</style>