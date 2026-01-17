<template>
  <div class="strategy-compare">
    <!-- 顶部控制栏 -->
    <el-card class="control-panel" :body-style="{ padding: '15px 20px' }">
      <el-form :model="compareForm" :inline="true" class="control-form">
        <el-form-item label="选择策略" required>
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
                  <span v-if="compareForm.strategy_names.length === 0" class="placeholder">
                    请选择至少两个策略
                  </span>
                  <span v-else class="selected-text">
                    已选择 <span class="count">{{ compareForm.strategy_names.length }}</span> 项策略
                  </span>
                  <el-icon class="arrow-icon" :class="{ 'is-reverse': strategyPopoverVisible }">
                    <ArrowDown />
                  </el-icon>
                </div>
              </template>
              
              <div class="strategy-selector">
                <!-- 搜索和操作栏 -->
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
                  <el-button
                    size="small"
                    type="primary"
                    link
                    @click="handleToggleAll"
                  >
                    {{ compareForm.strategy_names.length === filteredStrategies.length && filteredStrategies.length > 0 ? '全不选' : '全选' }}
                  </el-button>
                </div>
                
                <!-- 策略列表 -->
                <div class="strategy-list">
                  <el-checkbox-group v-model="compareForm.strategy_names" @change="handleStrategiesChange">
                    <div
                      v-for="strategy in filteredStrategies"
                      :key="strategy.name"
                      class="strategy-item"
                    >
                      <el-checkbox :value="strategy.name">
                        <div class="strategy-info">
                          <div class="strategy-name">{{ strategy.name }}</div>
                          <div class="strategy-desc">{{ strategy.description }}</div>
                        </div>
                      </el-checkbox>
                    </div>
                  </el-checkbox-group>
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
          </div>
        </el-form-item>

        <el-form-item label="股票" required>
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
              v-model="compareForm.stock_code"
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
              :disabled="!compareForm.stock_code"
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
          <el-button type="primary" @click="handleCompare" :loading="comparing">
            <el-icon><Search /></el-icon>
            开始比较
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 策略参数配置 -->
    <el-card v-if="compareForm.strategy_names && compareForm.strategy_names.length > 0" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>策略参数配置</span>
        </div>
      </template>
      <el-tabs v-model="activeStrategyTab" type="border-card" v-if="compareForm.strategy_names && compareForm.strategy_names.length > 0">
        <el-tab-pane
          v-for="strategyName in compareForm.strategy_names"
          :key="strategyName"
          :label="strategyName"
          :name="strategyName"
        >
          <div v-if="strategyParamsMap[strategyName]">
             <div class="params-header">
               <el-popover
                 placement="bottom"
                 :width="350"
                 trigger="click"
                 @show="loadSavedParams(strategyName)"
               >
                 <template #reference>
                   <el-button size="small" type="primary" link>
                     <el-icon><Download /></el-icon> 加载优化参数
                   </el-button>
                 </template>
                 
                 <div v-loading="loadingParamSets[strategyName]">
                   <div v-if="availableParamSets[strategyName] && availableParamSets[strategyName].length > 0">
                     <div 
                       v-for="set in availableParamSets[strategyName]" 
                       :key="set.id" 
                       class="param-set-item"
                       style="padding: 8px; cursor: pointer; border-bottom: 1px solid var(--el-border-color-lighter);"
                       @click="applyParamSet(strategyName, set)"
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
                   <el-empty v-else description="暂无优化记录" :image-size="60" />
                 </div>
               </el-popover>
               <el-button size="small" type="success" link @click="goToOptimization(strategyName)">
                 <el-icon><Setting /></el-icon> 智能参数优化
               </el-button>
             </div>
            <p v-if="Object.keys(strategyParamsMap[strategyName]).length === 0" style="color: #909399">
              该策略无需额外参数配置
            </p>
            <el-form
              v-else
              :model="strategyParamsMap[strategyName]"
              label-width="150px"
            >
              <el-form-item
                v-for="(_, key) in strategyParamsMap[strategyName]"
                :key="key"
                :label="getParameterLabel(key, strategyName)"
              >
                <el-input-number
                  v-model="strategyParamsMap[strategyName][key]"
                  :min="getParameterMin(key, strategyName)"
                  :precision="getParameterPrecision(key)"
                  style="width: 200px"
                />
                <div v-if="getParameterDescription(key, strategyName)" class="parameter-description">
                  {{ getParameterDescription(key, strategyName) }}
                </div>
              </el-form-item>
            </el-form>
          </div>
          <div v-else style="color: #909399; padding: 20px; text-align: center">
            加载中...
          </div>
        </el-tab-pane>
      </el-tabs>
      <div v-else style="color: #909399; padding: 20px; text-align: center">
        请先选择策略
      </div>
    </el-card>



    <!-- 比较结果 -->
    <el-card v-if="compareResult" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>比较结果</span>

        </div>
      </template>

      <!-- 标签页：统计对比和图表 -->
      <el-tabs v-model="activeResultTab" type="border-card">
        <!-- 统计对比标签页 -->
        <el-tab-pane label="统计对比" name="statistics">
          <div v-if="compareResult.results && compareResult.results.length > 0" class="comparison-section">
            <el-table
              :data="comparisonTableData"
              stripe
              border
              style="width: 100%"
              :default-sort="{ prop: 'cumulative_return', order: 'descending' }"
              highlight-current-row
            >
              <el-table-column prop="strategy_name" label="策略名称" width="150" fixed="left">
                <template #default="{ row }">
                  <el-tag :type="getStrategyTagType(row)" size="small">
                    {{ row.strategy_name }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="total_signals" label="总信号数" width="100" align="right" sortable>
                <template #default="{ row }">{{ formatStatValue(row.total_signals, 'total_signals') }}</template>
              </el-table-column>
              <el-table-column prop="buy_signals" label="买入信号" width="100" align="right" sortable>
                <template #default="{ row }">{{ formatStatValue(row.buy_signals, 'buy_signals') }}</template>
              </el-table-column>
              <el-table-column prop="sell_signals" label="卖出信号" width="100" align="right" sortable>
                <template #default="{ row }">{{ formatStatValue(row.sell_signals, 'sell_signals') }}</template>
              </el-table-column>
              <el-table-column prop="cumulative_return" label="累计收益率" width="130" align="right" sortable>
                <template #default="{ row }">
                  <span :style="getStatValueStyle(row, 'cumulative_return')">
                    <el-icon v-if="getBestValue('cumulative_return') === row.cumulative_return" style="margin-right: 4px;">
                      <Trophy />
                    </el-icon>
                    {{ formatStatValue(row.cumulative_return, 'cumulative_return') }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="win_rate" label="胜率" width="110" align="right" sortable>
                <template #default="{ row }">
                  <span :style="getStatValueStyle(row, 'win_rate')">
                    <el-icon v-if="getBestValue('win_rate') === row.win_rate" style="margin-right: 4px;">
                      <Trophy />
                    </el-icon>
                    {{ formatStatValue(row.win_rate, 'win_rate') }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="max_drawdown" label="最大回撤" width="130" align="right" sortable>
                <template #default="{ row }">
                  <span :style="getStatValueStyle(row, 'max_drawdown')">
                    <el-icon v-if="getBestValue('max_drawdown') === row.max_drawdown" style="margin-right: 4px;">
                      <Trophy />
                    </el-icon>
                    {{ formatStatValue(row.max_drawdown, 'max_drawdown') }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="annual_return" label="年化收益" width="110" align="right" sortable>
                <template #default="{ row }">
                  <span :style="getStatValueStyle(row, 'annual_return')">
                    <el-icon v-if="getBestValue('annual_return') === row.annual_return" style="margin-right: 4px;">
                      <Trophy />
                    </el-icon>
                    {{ formatStatValue(row.annual_return, 'annual_return') }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="sharpe_ratio" label="夏普比率" width="110" align="right" sortable>
                <template #default="{ row }">
                  <span :style="getStatValueStyle(row, 'sharpe_ratio')">
                    <el-icon v-if="getBestValue('sharpe_ratio') === row.sharpe_ratio" style="margin-right: 4px;">
                      <Trophy />
                    </el-icon>
                    {{ formatStatValue(row.sharpe_ratio, 'sharpe_ratio') }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="sortino_ratio" label="索提诺比率" width="120" align="right" sortable>
                <template #default="{ row }">
                  <span :style="getStatValueStyle(row, 'sortino_ratio')">
                    <el-icon v-if="getBestValue('sortino_ratio') === row.sortino_ratio" style="margin-right: 4px;">
                      <Trophy />
                    </el-icon>
                    {{ formatStatValue(row.sortino_ratio, 'sortino_ratio') }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="pl_ratio" label="盈亏比" width="100" align="right" sortable>
                <template #default="{ row }">
                  <span :style="getStatValueStyle(row, 'pl_ratio')">
                    <el-icon v-if="getBestValue('pl_ratio') === row.pl_ratio" style="margin-right: 4px;">
                      <Trophy />
                    </el-icon>
                    {{ formatStatValue(row.pl_ratio, 'pl_ratio') }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="total_trades" label="总交易次数" width="120" align="right" sortable>
                <template #default="{ row }">{{ formatStatValue(row.total_trades, 'total_trades') }}</template>
              </el-table-column>
              <el-table-column prop="profitable_trades" label="盈利交易" width="120" align="right" sortable>
                <template #default="{ row }">{{ formatStatValue(row.profitable_trades, 'profitable_trades') }}</template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- K线图对比标签页 -->
        <el-tab-pane label="K线图 & 信号" name="kline">
          <div v-if="compareResult.results && compareResult.results.length > 0" class="chart-section">
            <div v-if="klineData.length === 0" class="empty-chart">
              <el-empty description="暂无K线数据" />
            </div>
            <KlineChart
              v-else
              :data="klineData"
              :markers="combinedMarkers"
              :lines="strategyLines"
              :height="600"
              :watermark="stockName"
              :darkMode="isDark"
              :showSubChart="false"
              :simpleLegend="true"
              :key="`kline-${compareResult.stock_code}-${Date.now()}`"
            />
            <!-- 策略信号图例 -->
            <div class="marker-legend" v-if="combinedMarkers.length > 0">
              <div class="legend-title">策略信号图例：</div>
              <div class="legend-items">
                <div
                  v-for="(strategy, index) in compareResult.results.filter(r => r && !('error' in r))"
                  :key="strategy.strategy_name"
                  class="legend-item"
                >
                  <span class="legend-color" :style="{ backgroundColor: getStrategyColor(index) }"></span>
                  <span class="legend-label">{{ strategy.strategy_name }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 收益率曲线对比标签页 -->
        <el-tab-pane label="收益率曲线" name="equity">
          <div v-if="compareResult.results && compareResult.results.length > 0" class="chart-section">
            <div v-if="equityLines.length === 0" class="empty-chart">
              <el-empty description="暂无权益曲线数据" />
            </div>
            <KlineChart
              v-else
              :data="[]"
              :lines="equityLines"
              :height="500"
              :watermark="`${compareResult.stock_code} 策略对比`"
              :darkMode="isDark"
              :showSubChart="false"
              :simpleLegend="true"
              :key="`equity-${compareResult.stock_code}-${Date.now()}`"
            />
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- 错误信息 -->
      <el-alert
        v-for="errorResult in errorResults"
        :key="errorResult.strategy_name"
        :title="`策略 ${errorResult.strategy_name} 分析失败`"
        :description="errorResult.error"
        type="error"
        :closable="false"
        style="margin-top: 20px"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Trophy, Download, Collection, Star, StarFilled, Setting } from '@element-plus/icons-vue'
import { useDark } from '@vueuse/core'
import { strategyAPI, type StrategyInfo, type StrategyCompareRequest, type StrategyCompareResponse } from '@/api/strategy'
import { dataAPI } from '@/api/data'
import { watchlistAPI, type WatchlistItem } from '@/api/watchlist'
import { paramSetsAPI, type ParamSet } from '@/api/param-sets'
import KlineChart, { type ChartData, type Marker, type LineData } from '@/components/KlineChart.vue'

const router = useRouter()
const isDark = useDark()

const strategies = ref<StrategyInfo[]>([])
const comparing = ref(false)
const compareResult = ref<StrategyCompareResponse | null>(null)
const strategyInfoMap = ref<Record<string, StrategyInfo>>({})
const activeStrategyTab = ref<string>('')
const activeResultTab = ref<string>('statistics') // statistics, kline, equity
const klineData = ref<ChartData[]>([])
const stockData = ref<any[]>([])
const dateRange = ref<[string, string]>(['', ''])
const stockName = ref<string>('')

const compareForm = reactive<StrategyCompareRequest>({
  strategy_names: [],
  stock_code: '',
  start_date: '',
  end_date: '',
  strategy_params: {},
})

const strategyParamsMap = reactive<Record<string, Record<string, any>>>({})
const loadingParamSets = ref<Record<string, boolean>>({})
const availableParamSets = ref<Record<string, ParamSet[]>>({})

// 日期快捷选项
const dateShortcuts = [
  { text: '最近1个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 1); return [start, end]; } },
  { text: '最近3个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 3); return [start, end]; } },
  { text: '最近6个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 6); return [start, end]; } },
  { text: '最近1年', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 12); return [start, end]; } },
]

// 默认参数配置
const defaultParams: Record<string, Record<string, number>> = {
  'MA Strategy': { short_period: 5, long_period: 20 },
  'RSI Strategy': { period: 14, overbought: 70, oversold: 30 },
  'MACD Strategy': { fast_period: 12, slow_period: 26, signal_period: 9 },
  'Bollinger Strategy': { period: 20, std_dev: 2 },
  'Momentum Strategy': { period: 10 },
}

// 加载策略列表
const loadStrategies = async () => {
  try {
    const response = await strategyAPI.listStrategies()
    strategies.value = response.strategies
  } catch (error: any) {
    console.error('加载策略列表失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载策略列表失败')
  }
}


// 收藏功能
const favorites = ref<WatchlistItem[]>([])
const isFavorite = computed(() => {
  if (!compareForm.stock_code) return false
  return favorites.value.some(f => f.stock_code === compareForm.stock_code)
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
  if (!compareForm.stock_code) return
  try {
    if (isFavorite.value) {
      await watchlistAPI.removeFromWatchlist(compareForm.stock_code)
      ElMessage.success('已取消收藏')
    } else {
      await watchlistAPI.addToWatchlist(compareForm.stock_code)
      ElMessage.success('已收藏')
    }
    loadFavorites()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const handleFavoriteSelect = (fav: WatchlistItem) => {
  compareForm.stock_code = fav.stock_code
}

// 策略选择器状态
const strategyPopoverVisible = ref(false)
const strategySearchQuery = ref('')

// 过滤后的策略列表
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

// 处理全选/全不选
const handleToggleAll = () => {
  const allFilteredNames = filteredStrategies.value.map(s => s.name)
  const allSelected = allFilteredNames.every(name => compareForm.strategy_names.includes(name))
  
  if (allSelected) {
    // 全不选：移除所有过滤后的策略
    compareForm.strategy_names = compareForm.strategy_names.filter(
      name => !allFilteredNames.includes(name)
    )
  } else {
    // 全选：添加所有过滤后的策略（去重）
    const newNames = new Set([...compareForm.strategy_names, ...allFilteredNames])
    compareForm.strategy_names = Array.from(newNames)
  }
  handleStrategiesChange(compareForm.strategy_names)
}

// Popover 显示/隐藏处理
const handlePopoverShow = () => {
  strategySearchQuery.value = ''
}

const handlePopoverHide = () => {
  strategySearchQuery.value = ''
}

// 策略变更处理
const handleStrategiesChange = async (strategyNames: string[]) => {
  compareForm.strategy_names = strategyNames
  
  // 清除之前的参数
  Object.keys(strategyParamsMap).forEach((key) => {
    if (!strategyNames.includes(key)) {
      delete strategyParamsMap[key]
    }
  })

  // 加载每个策略的信息和参数
  for (const strategyName of strategyNames) {
    if (!strategyInfoMap.value[strategyName]) {
      try {
        const info = await strategyAPI.getStrategyInfo(strategyName)
        strategyInfoMap.value[strategyName] = info

        // 初始化策略参数
        if (!strategyParamsMap[strategyName]) {
          strategyParamsMap[strategyName] = {}
        }
        Object.keys(strategyParamsMap[strategyName]).forEach((key) => delete strategyParamsMap[strategyName][key])

        // 尝试加载保存的参数
        try {
          if (compareForm.stock_code) {
             const savedParams = await strategyAPI.getParams(compareForm.stock_code, strategyName)
             if (savedParams) {
               Object.assign(strategyParamsMap[strategyName], savedParams)
               continue
             }
          }
        } catch (e) { console.error(e) }

        // 设置默认参数
        if (defaultParams[strategyName]) {
          Object.assign(strategyParamsMap[strategyName], defaultParams[strategyName])
        } else if (info.parameter_descriptions) {
          // 自定义策略或无默认配置
          for (const [key, desc] of Object.entries(info.parameter_descriptions)) {
            // 简单解析默认值
             let defVal = 1
             if (typeof desc === 'string' && desc.includes('默认')) {
                const match = desc.match(/默认[:\s]*([0-9.]+)/)
                if (match) defVal = parseFloat(match[1])
             }
            strategyParamsMap[strategyName][key] = defVal
          }
        }

        // 设置第一个策略为活动标签
        if (!activeStrategyTab.value && strategyNames.length > 0) {
          activeStrategyTab.value = strategyNames[0]
        }
      } catch (error: any) {
        console.error(`加载策略 ${strategyName} 信息失败:`, error)
      }
    }
  }
}

// 搜索股票
const searchStocks = async (queryString: string, cb: (results: any[]) => void) => {
  if (!queryString) {
    cb([])
    return
  }

  try {
    const response = await dataAPI.getStockList('all')
    const results = response.stocks
      .filter(
        (stock) =>
          stock.code.includes(queryString) || stock.name.includes(queryString)
      )
      .slice(0, 10)
      .map((stock) => ({
        value: stock.code,
        code: stock.code,
        name: stock.name,
      }))
    cb(results)
  } catch (error) {
    cb([])
  }
}

// 股票选择
const handleStockSelect = (item: { code: string; name: string }) => {
  compareForm.stock_code = item.code
  // Reload params for selected strategies if stock changes
  if (compareForm.strategy_names.length > 0) {
      handleStrategiesChange(compareForm.strategy_names)
  }
}

// 日期范围变更处理
const handleDateRangeChange = (val: any) => {
  if (!val) {
    compareForm.start_date = ''
    compareForm.end_date = ''
  } else {
    compareForm.start_date = val[0]
    compareForm.end_date = val[1]
  }
}

// 执行比较
const handleCompare = async () => {
  if (compareForm.strategy_names.length < 2) {
    ElMessage.warning('至少选择两个策略进行比较')
    return
  }
  if (!compareForm.stock_code) {
    ElMessage.warning('请输入股票代码')
    return
  }

  comparing.value = true
  try {
    // 构建请求参数
    const request: StrategyCompareRequest = {
      strategy_names: compareForm.strategy_names,
      stock_code: compareForm.stock_code,
      start_date: compareForm.start_date || undefined,
      end_date: compareForm.end_date || undefined,
      strategy_params: {},
    }

    // 添加策略参数
    for (const strategyName of compareForm.strategy_names) {
      if (strategyParamsMap[strategyName] && Object.keys(strategyParamsMap[strategyName]).length > 0) {
        request.strategy_params![strategyName] = { ...strategyParamsMap[strategyName] }
      }
    }

    const result = await strategyAPI.compareStrategies(request)
    compareResult.value = result
    
    // 加载K线数据用于图表显示
    await loadKlineDataForCompare()
    
    ElMessage.success('比较完成')
  } catch (error: any) {
    console.error('策略比较失败:', error)
    ElMessage.error(error.response?.data?.detail || '策略比较失败')
  } finally {
    comparing.value = false
  }
}

// 重置表单
const handleReset = () => {
  compareForm.strategy_names = []
  compareForm.stock_code = ''
  compareForm.start_date = ''
  compareForm.end_date = ''
  compareForm.strategy_params = {}
  dateRange.value = ['', '']
  Object.keys(strategyParamsMap).forEach((key) => delete strategyParamsMap[key])
  compareResult.value = null
  activeStrategyTab.value = ''

  // 设置默认日期（最近30天）
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  dateRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]
  compareForm.end_date = end.toISOString().split('T')[0]
  compareForm.start_date = start.toISOString().split('T')[0]
}



// 加载保存的参数
const loadSavedParams = async (strategyName: string) => {
  if (!compareForm.stock_code) {
    ElMessage.warning('请先选择股票')
    return
  }
  
  loadingParamSets.value[strategyName] = true
  try {
    const res = await paramSetsAPI.getParamSets(compareForm.stock_code, strategyName)
    availableParamSets.value[strategyName] = res.param_sets
  } catch (e: any) {
    ElMessage.error('加载参数记录失败')
  } finally {
    loadingParamSets.value[strategyName] = false
  }
}

// 应用参数集
const applyParamSet = (strategyName: string, set: ParamSet) => {
  if (!strategyParamsMap[strategyName]) {
    strategyParamsMap[strategyName] = {}
  }
  Object.keys(strategyParamsMap[strategyName]).forEach(k => delete strategyParamsMap[strategyName][k])
  Object.assign(strategyParamsMap[strategyName], set.params)
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

// 跳转到优化页面
const goToOptimization = (strategyName: string) => {
    if (!compareForm.stock_code) {
        ElMessage.warning('请先选择股票')
        return
    }
    router.push({
        name: 'StrategyOptimization',
        query: {
            strategy: strategyName,
            stock: compareForm.stock_code
        }
    })
}

// 格式化统计值
const formatStatValue = (value: any, key: string): string => {
  if (value === null || value === undefined) return '-'
  
  // 整数类型不显示小数
  const intKeys = ['total_signals', 'buy_signals', 'sell_signals', 'total_trades', 'profitable_trades']
  if (intKeys.includes(key)) {
    return Math.round(Number(value)).toString()
  }
  
  // 百分比类型
  const percentKeys = ['cumulative_return', 'win_rate', 'max_drawdown', 'annual_return']
  if (percentKeys.includes(key)) {
    return `${Number(value).toFixed(2)}%`
  }
  
  // 比率类型（保留3位小数）
  const ratioKeys = ['sharpe_ratio', 'sortino_ratio', 'pl_ratio']
  if (ratioKeys.includes(key)) {
    return Number(value).toFixed(3)
  }
  
  return String(value)
}

// 获取统计值样式
const getStatValueStyle = (row: any, key: string): Record<string, string> => {
  const value = row[key]
  if (value === null || value === undefined) return {}
  
  const isBest = getBestValue(key) === value
  
  // 收益类指标（越高越好）
  if (['cumulative_return', 'annual_return'].includes(key)) {
    return {
      color: value >= 0 ? '#f56c6c' : '#67c23a',
      fontWeight: isBest ? 'bold' : 'normal',
    }
  }
  
  // 胜率（越高越好）
  if (key === 'win_rate') {
    return {
      color: value >= 50 ? '#f56c6c' : '#909399',
      fontWeight: isBest ? 'bold' : 'normal',
    }
  }
  
  // 最大回撤（越小越好，绝对值）
  if (key === 'max_drawdown') {
    return {
      color: Math.abs(value) <= 10 ? '#67c23a' : Math.abs(value) <= 20 ? '#e6a23c' : '#f56c6c',
      fontWeight: isBest ? 'bold' : 'normal',
    }
  }
  
  // 比率类指标（越高越好）
  if (['sharpe_ratio', 'sortino_ratio', 'pl_ratio'].includes(key)) {
    return {
      color: value > 1 ? '#f56c6c' : value > 0 ? '#e6a23c' : '#909399',
      fontWeight: isBest ? 'bold' : 'normal',
    }
  }
  
  return {}
}

// 获取最佳值（用于显示奖杯图标）
const getBestValue = (key: string): number | null => {
  if (!comparisonTableData.value || comparisonTableData.value.length === 0) return null
  
  const values = comparisonTableData.value
    .map(row => row[key])
    .filter(v => v !== null && v !== undefined)
    .map(v => Number(v))
  
  if (values.length === 0) return null
  
  // 最大回撤越小越好（绝对值）
  if (key === 'max_drawdown') {
    return values.reduce((best, current) => Math.abs(current) < Math.abs(best) ? current : best)
  } 
  // 其他所有指标都是越大越好
  else {
    return Math.max(...values)
  }
}

// 获取策略标签类型（根据排名）
const getStrategyTagType = (row: any): string => {
  const sortedByReturn = [...comparisonTableData.value]
    .sort((a, b) => (b.cumulative_return || 0) - (a.cumulative_return || 0))
  const rank = sortedByReturn.findIndex(r => r.strategy_name === row.strategy_name) + 1
  
  if (rank === 1) return 'success'
  if (rank === 2) return 'warning'
  return 'info'
}

// 获取参数标签
const getParameterLabel = (key: string, strategyName: string): string => {
  const strategyInfo = strategyInfoMap.value[strategyName]
  if (!strategyInfo?.parameter_descriptions) return key
  const paramDesc = strategyInfo.parameter_descriptions[key] as any
  return paramDesc?.label || key
}

// 获取参数描述
const getParameterDescription = (key: string, strategyName: string): string => {
  const strategyInfo = strategyInfoMap.value[strategyName]
  if (!strategyInfo?.parameter_descriptions) return ''
  const desc = strategyInfo.parameter_descriptions[key]
  return typeof desc === 'string' ? desc : ''
}

// 获取参数最小值
const getParameterMin = (key: string, strategyName: string): number => {
  const strategyInfo = strategyInfoMap.value[strategyName]
  if (!strategyInfo?.parameter_descriptions) return 1
  const paramDesc = strategyInfo.parameter_descriptions[key] as any
  return paramDesc?.min ?? 1
}

// 获取参数精度
const getParameterPrecision = (key: string): number => {
  if (key.includes('std') || key.includes('oversold') || key.includes('overbought')) {
    return 1
  }
  return 0
}

// 比较结果表格数据
const comparisonTableData = computed(() => {
  if (!compareResult.value?.results) return []
  return compareResult.value.results
    .filter((result) => result && !('error' in result) && result.statistics)
    .map((result) => ({
      strategy_name: result.strategy_name,
      ...result.statistics,
    }))
})

// 错误结果
const errorResults = computed(() => {
  if (!compareResult.value?.results) return []
  return compareResult.value.results.filter((result) => result && 'error' in result)
})

// 策略颜色列表（用于区分不同策略的信号）
const strategyColors = [
  '#26a69a', // 绿色
  '#ef5350', // 红色
  '#42a5f5', // 蓝色
  '#ab47bc', // 紫色
  '#ffa726', // 橙色
  '#66bb6a', // 浅绿色
  '#ec407a', // 粉色
  '#26c6da', // 青色
]

const getStrategyColor = (index: number): string => {
  return strategyColors[index % strategyColors.length]
}

// 加载K线数据用于图表显示
const loadKlineDataForCompare = async () => {
  if (!compareResult.value || !compareResult.value.stock_code) return
  
  try {
    // 获取股票信息（包含名称）
    try {
      const stockInfo = await dataAPI.getStockInfo(compareResult.value.stock_code)
      stockName.value = stockInfo.name || compareResult.value.stock_code
    } catch (e) {
      stockName.value = compareResult.value.stock_code
    }
    
    const response = await dataAPI.getKlineData(
      compareResult.value.stock_code,
      compareResult.value.start_date || undefined,
      compareResult.value.end_date || undefined
    )
    
    stockData.value = response || []
    
    // 格式化K线数据，使用后端返回的涨跌幅
    const formattedData = (response || []).map((item: any) => {
      let dateStr = item.trade_date || item.date
      if (dateStr && typeof dateStr === 'string' && dateStr.includes('T')) {
        dateStr = dateStr.split('T')[0]
      }
      
      return {
        time: dateStr || '',
        open: Number(item.open) || 0,
        high: Number(item.high) || 0,
        low: Number(item.low) || 0,
        close: Number(item.close) || 0,
        volume: Number(item.volume) || 0,
        pct_chg: item.pct_chg !== null && item.pct_chg !== undefined ? Number(item.pct_chg) : undefined,
      }
    }).filter((item: ChartData) => item.time)
    
    klineData.value = formattedData
  } catch (error: any) {
    console.error('加载K线数据失败:', error)
  }
}

// 合并所有策略的标记（用于K线图显示）
const combinedMarkers = computed<Marker[]>(() => {
  if (!compareResult.value?.results) return []
  
  const markers: Marker[] = []
  const validResults = compareResult.value.results.filter(r => r && !('error' in r))
  
  validResults.forEach((result, strategyIndex) => {
    if (!result.result) return
    
    const color = getStrategyColor(strategyIndex)
    
    result.result.forEach((item: any) => {
      let dateStr = item.date
      if (dateStr) {
        if (typeof dateStr === 'string' && dateStr.includes('T')) {
          dateStr = dateStr.split('T')[0]
        }
      }
      
      if (!dateStr) return
      
      if (item.signal === 1) {
        markers.push({
          time: dateStr,
          position: 'belowBar',
          color: color,
          shape: 'circle',
          text: 'B',
        })
      } else if (item.signal === -1) {
        markers.push({
          time: dateStr,
          position: 'aboveBar',
          color: color,
          shape: 'circle',
          text: 'S',
        })
      }
    })
  })
  
  return markers
})

// 收益率曲线数据
const equityLines = computed<LineData[]>(() => {
  if (!compareResult.value?.results) return []
  
  const lines: LineData[] = []
  const validResults = compareResult.value.results.filter(r => r && !('error' in r))
  
  validResults.forEach((result, index) => {
    if (!result.result || !result.statistics) return
    
    const color = getStrategyColor(index)
    
    // 从 statistics 中获取 equity_curve
    let equityData: { time: string; value: number }[] = []
    
    if (result.statistics.equity_curve && Array.isArray(result.statistics.equity_curve)) {
      // 使用后端计算的权益曲线
      // equity_curve 的长度应该与 result 的长度一致
      const equityCurve = result.statistics.equity_curve
      equityData = result.result.map((item: any, idx: number) => {
        let dateStr = item.date
        if (dateStr && typeof dateStr === 'string' && dateStr.includes('T')) {
          dateStr = dateStr.split('T')[0]
        }
        
        // 确保索引不越界
        const equity = idx < equityCurve.length ? equityCurve[idx] : (equityCurve[equityCurve.length - 1] || 100000)
        return {
          time: dateStr || '',
          value: Number(equity) || 100000,
        }
      }).filter((d: any) => d.time && d.value !== null && d.value !== undefined)
    } else {
      // 如果没有权益曲线，使用累计收益率计算（线性增长）
      const initialCapital = 100000
      const finalReturn = (result.statistics.cumulative_return || 0) / 100
      const totalDays = result.result.length
      
      equityData = result.result.map((item: any, idx: number) => {
        let dateStr = item.date
        if (dateStr && typeof dateStr === 'string' && dateStr.includes('T')) {
          dateStr = dateStr.split('T')[0]
        }
        
        // 线性插值计算每日权益
        const progress = totalDays > 1 ? idx / (totalDays - 1) : 0
        const equity = initialCapital * (1 + finalReturn * progress)
        
        return {
          time: dateStr || '',
          value: Number(equity) || initialCapital,
        }
      }).filter((d: any) => d.time && d.value !== null && d.value !== undefined)
    }
    
    if (equityData.length > 0) {
      lines.push({
        name: result.strategy_name,
        data: equityData,
        color: color,
        lineWidth: 2,
      })
    }
  })
  
  return lines
})

// 策略指标线（如均线等）
const strategyLines = computed<LineData[]>(() => {
  // 可以根据需要添加策略的指标线，如MA、MACD等
  return []
})



onMounted(() => {
  loadStrategies()
  loadFavorites()

  // 设置默认日期（最近30天）
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  dateRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]
  compareForm.end_date = end.toISOString().split('T')[0]
  compareForm.start_date = start.toISOString().split('T')[0]
})
</script>

<style scoped>
.strategy-compare {
  display: flex;
  flex-direction: column;
  padding: 0;
}

.control-panel {
  flex-shrink: 0;
}

/* 确保卡片内容完全展示，不限制高度 */
.strategy-compare :deep(.el-card__body) {
  max-height: none !important;
  overflow: visible !important;
}

.strategy-compare :deep(.el-tabs) {
  max-height: none !important;
  overflow: visible !important;
}

.strategy-compare :deep(.el-tabs__content) {
  max-height: none !important;
  overflow: visible !important;
}

.strategy-compare :deep(.el-tab-pane) {
  max-height: none !important;
  overflow: visible !important;
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
}

.comparison-section {
  margin-top: 20px;
}

.comparison-section h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.parameter-description {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}

.params-header {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 15px;
}

.range-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.chart-section {
  padding: 20px;
  min-height: 500px;
}

.empty-chart {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.marker-legend {
  margin-top: 20px;
  padding: 15px;
  background-color: #1d1e1f;
  border-radius: 4px;
}

.legend-title {
  font-size: 14px;
  font-weight: 600;
  color: #e5eaf3;
  margin-bottom: 10px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #a8abb2;
}

.legend-marker {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.marker-text {
  color: #ffffff;
  font-size: 12px;
  line-height: 1;
}

.legend-label {
  margin-left: 4px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  display: inline-block;
}

.stock-code {
  font-weight: bold;
  margin-right: 8px;
}

.stock-name {
  color: #909399;
  font-size: 12px;
}

/* 自定义选择框 */
.custom-select {
  width: 300px;
  height: 32px;
  padding: 0 30px 0 12px;
  display: flex;
  align-items: center;
  border: 1px solid #4c4d4f;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  background-color: #1d1e1f;
}

.custom-select:hover {
  border-color: #606266;
  background-color: #262727;
}

.custom-select .placeholder {
  color: #6c6e72;
  font-size: 14px;
}

.custom-select .selected-text {
  color: #a8abb2;
  font-size: 14px;
}

.custom-select .selected-text .count {
  color: #409eff;
  font-weight: 500;
  margin: 0 3px;
}

.custom-select .arrow-icon {
  position: absolute;
  right: 10px;
  transition: transform 0.3s;
  color: #909399;
}

.custom-select .arrow-icon.is-reverse {
  transform: rotate(180deg);
  color: #409eff;
}

/* 策略选择器弹出层 */
.strategy-selector {
  display: flex;
  flex-direction: column;
  max-height: 400px;
  background-color: #262727;
  border-radius: 4px;
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid #3a3a3c;
}

.selector-header :deep(.el-input__wrapper) {
  background-color: #1d1e1f;
  box-shadow: 0 0 0 1px #4c4d4f inset;
}

.selector-header :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #606266 inset;
}

.selector-header :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset !important;
}

.selector-header :deep(.el-input__inner) {
  color: #a8abb2;
}

.selector-header :deep(.el-input__inner::placeholder) {
  color: #6c6e72;
}

.selector-header :deep(.el-icon) {
  color: #909399;
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
  background-color: #4c4d4f;
  border-radius: 3px;
}

.strategy-list::-webkit-scrollbar-thumb:hover {
  background-color: #606266;
}

.strategy-item {
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.strategy-item:hover {
  background-color: #2d2d2d;
}

.strategy-item :deep(.el-checkbox) {
  width: 100%;
  height: auto;
}

.strategy-item :deep(.el-checkbox__label) {
  width: 100%;
  white-space: normal;
  line-height: 1.4;
  color: #a8abb2;
}

.strategy-item :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #409eff;
  border-color: #409eff;
}

.strategy-item :deep(.el-checkbox__inner) {
  background-color: #1d1e1f;
  border-color: #4c4d4f;
}

.strategy-item :deep(.el-checkbox__inner:hover) {
  border-color: #409eff;
}

.strategy-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.strategy-name {
  font-size: 14px;
  color: #e5eaf3;
  font-weight: 500;
}

.strategy-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.3;
}

.empty-text {
  text-align: center;
  padding: 20px;
  color: #6c6e72;
  font-size: 14px;
}

.selector-footer {
  padding: 8px 12px;
  border-top: 1px solid #3a3a3c;
  display: flex;
  justify-content: flex-end;
}

.selector-footer :deep(.el-button) {
  background-color: #409eff;
  border-color: #409eff;
  color: #fff;
}

.selector-footer :deep(.el-button:hover) {
  background-color: #66b1ff;
  border-color: #66b1ff;
}
</style>
