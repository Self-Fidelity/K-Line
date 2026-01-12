<template>
  <div class="strategy-compare">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>策略比较</span>
        </div>
      </template>

      <!-- 策略选择和参数配置 -->
      <el-form :model="compareForm" label-width="120px" :inline="true">
        <el-form-item label="选择策略" required>
          <el-select
            v-model="compareForm.strategy_names"
            placeholder="请选择至少两个策略"
            style="width: 300px"
            multiple
            filterable
            :max-collapse-tags="3"
            @change="handleStrategiesChange"
          >
            <el-option
              v-for="strategy in strategies"
              :key="strategy.name"
              :label="strategy.name"
              :value="strategy.name"
            >
              <div>
                <div>{{ strategy.name }}</div>
                <div style="font-size: 12px; color: #909399">{{ strategy.description }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="股票代码" required>
          <el-autocomplete
            v-model="compareForm.stock_code"
            :fetch-suggestions="searchStocks"
            placeholder="输入股票代码或名称"
            style="width: 200px"
            @select="handleStockSelect"
          >
            <template #default="{ item }">
              <div>{{ item.code }} - {{ item.name }}</div>
            </template>
          </el-autocomplete>
        </el-form-item>

        <el-form-item label="开始日期">
          <el-date-picker
            v-model="compareForm.start_date"
            type="date"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 180px"
          />
        </el-form-item>

        <el-form-item label="结束日期">
          <el-date-picker
            v-model="compareForm.end_date"
            type="date"
            placeholder="选择结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 180px"
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
            <p v-if="Object.keys(strategyParamsMap[strategyName]).length === 0" style="color: #909399">
              该策略无需额外参数配置
            </p>
            <el-form
              v-else
              :model="strategyParamsMap[strategyName]"
              label-width="150px"
            >
              <el-form-item
                v-for="(value, key) in strategyParamsMap[strategyName]"
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
          <div>
            <el-button type="success" @click="handleExportReport" :disabled="!compareResult">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
            <el-button type="primary" @click="handleViewChart" :disabled="!compareResult">
              <el-icon><Picture /></el-icon>
              查看详细K线图
            </el-button>
          </div>
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
              <el-table-column prop="total_trades" label="总交易次数" width="120" align="right" sortable>
                <template #default="{ row }">{{ formatStatValue(row.total_trades, 'total_trades') }}</template>
              </el-table-column>
              <el-table-column prop="profitable_trades" label="盈利交易" width="120" align="right" sortable>
                <template #default="{ row }">{{ formatStatValue(row.profitable_trades, 'profitable_trades') }}</template>
              </el-table-column>
              <el-table-column prop="final_capital" label="最终资金" width="120" align="right" sortable>
                <template #default="{ row }">
                  {{ formatStatValue(row.final_capital, 'final_capital') }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 收益率曲线对比标签页 -->
        <el-tab-pane label="收益率曲线对比" name="equity">
          <div v-if="compareResult.results && compareResult.results.length > 0" class="chart-section">
            <KlineChart
              :data="klineData"
              :lines="equityLines"
              :height="400"
              :key="`equity-${compareResult.stock_code}`"
            />
          </div>
        </el-tab-pane>

        <!-- K线图对比标签页 -->
        <el-tab-pane label="K线图对比" name="kline">
          <div v-if="compareResult.results && compareResult.results.length > 0" class="chart-section">
            <KlineChart
              :data="klineData"
              :markers="combinedMarkers"
              :lines="strategyLines"
              :height="500"
              :key="`kline-${compareResult.stock_code}`"
            />
            <div class="marker-legend" v-if="combinedMarkers.length > 0">
              <div class="legend-title">策略信号图例：</div>
              <div class="legend-items">
                <div
                  v-for="(strategy, index) in compareResult.results.filter(r => r && !('error' in r))"
                  :key="strategy.strategy_name"
                  class="legend-item"
                >
                  <span
                    class="legend-color"
                    :style="{ backgroundColor: getStrategyColor(index) }"
                  ></span>
                  <span>{{ strategy.strategy_name }}</span>
                </div>
              </div>
            </div>
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
import { Search, Picture, Trophy, Download } from '@element-plus/icons-vue'
import { strategyAPI, type StrategyInfo, type StrategyCompareRequest, type StrategyCompareResponse } from '@/api/strategy'
import { dataAPI, type StockInfo } from '@/api/data'
import KlineChart, { type ChartData, type Marker, type LineData } from '@/components/KlineChart.vue'

const router = useRouter()

const strategies = ref<StrategyInfo[]>([])
const comparing = ref(false)
const compareResult = ref<StrategyCompareResponse | null>(null)
const strategyInfoMap = ref<Record<string, StrategyInfo>>({})
const activeStrategyTab = ref<string>('')
const activeResultTab = ref<string>('statistics')
const klineData = ref<ChartData[]>([])
const stockData = ref<any[]>([])

const compareForm = reactive<StrategyCompareRequest>({
  strategy_names: [],
  stock_code: '',
  start_date: '',
  end_date: '',
  strategy_params: {},
})

const strategyParamsMap = reactive<Record<string, Record<string, any>>>({})

// 默认参数配置
const defaultParams: Record<string, Record<string, number>> = {
  'MA Strategy': { short_period: 5, long_period: 20 },
  'RSI Strategy': { period: 14, overbought: 70, oversold: 30 },
  'MACD Strategy': { fast_period: 12, slow_period: 26, signal_period: 9 },
  'Bollinger Strategy': { period: 20, num_std: 2 },
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

// 策略变更处理
const handleStrategiesChange = async (strategyNames: string[]) => {
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

        // 设置默认参数
        if (defaultParams[strategyName]) {
          Object.assign(strategyParamsMap[strategyName], defaultParams[strategyName])
        } else if (info.parameter_descriptions) {
          for (const [key] of Object.entries(info.parameter_descriptions)) {
            strategyParamsMap[strategyName][key] = 1
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
  Object.keys(strategyParamsMap).forEach((key) => delete strategyParamsMap[key])
  compareResult.value = null
  activeStrategyTab.value = ''

  // 设置默认日期（最近30天）
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  compareForm.end_date = end.toISOString().split('T')[0]
  compareForm.start_date = start.toISOString().split('T')[0]
}

// 查看K线图
const handleViewChart = () => {
  if (!compareResult.value || compareResult.value.results.length === 0) return
  // 跳转到图表查看页面，传递第一个策略的信息
  const firstResult = compareResult.value.results[0]
  if (firstResult && !('error' in firstResult)) {
    router.push({
      path: '/chart',
      query: {
        strategy: firstResult.strategy_name,
        stock: compareResult.value.stock_code,
        start: compareResult.value.start_date,
        end: compareResult.value.end_date,
      },
    })
  }
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
  const percentKeys = ['cumulative_return', 'win_rate', 'max_drawdown']
  if (percentKeys.includes(key)) {
    return `${Number(value).toFixed(2)}%`
  }
  
  // 金额类型
  if (key === 'final_capital') {
    return Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
  
  return String(value)
}

// 获取统计值样式
const getStatValueStyle = (row: any, key: string): Record<string, string> => {
  const value = row[key]
  if (value === null || value === undefined) return {}
  
  if (key === 'cumulative_return') {
    const isBest = getBestValue('cumulative_return') === value
    return {
      color: value >= 0 ? '#f56c6c' : '#67c23a',
      fontWeight: isBest ? 'bold' : 'normal',
    }
  }
  if (key === 'win_rate') {
    const isBest = getBestValue('win_rate') === value
    return {
      color: value >= 50 ? '#f56c6c' : '#909399',
      fontWeight: isBest ? 'bold' : 'normal',
    }
  }
  if (key === 'max_drawdown') {
    const isBest = getBestValue('max_drawdown') === value
    // 最大回撤越小越好（绝对值）
    return {
      color: Math.abs(value) <= 10 ? '#67c23a' : Math.abs(value) <= 20 ? '#e6a23c' : '#f56c6c',
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
  
  if (key === 'max_drawdown') {
    // 最大回撤越小越好（绝对值）
    return values.reduce((best, current) => Math.abs(current) < Math.abs(best) ? current : best)
  } else {
    // 其他指标越大越好
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
    const response = await dataAPI.getKlineData(
      compareResult.value.stock_code,
      compareResult.value.start_date || undefined,
      compareResult.value.end_date || undefined
    )
    
    stockData.value = response || []
    
    // 格式化K线数据
    klineData.value = (response || []).map((item: any) => {
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
      }
    }).filter((item: ChartData) => item.time)
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
          shape: 'arrowUp',
          text: `${result.strategy_name} 买入`,
        })
      } else if (item.signal === -1) {
        markers.push({
          time: dateStr,
          position: 'aboveBar',
          color: color,
          shape: 'arrowDown',
          text: `${result.strategy_name} 卖出`,
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
        priceScaleId: 'right',
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

// 导出对比报告
const handleExportReport = () => {
  if (!compareResult.value) return
  
  // 构建CSV内容
  const headers = ['策略名称', '总信号数', '买入信号', '卖出信号', '累计收益率', '胜率', '最大回撤', '总交易次数', '盈利交易', '最终资金']
  const rows = comparisonTableData.value.map(row => [
    row.strategy_name,
    row.total_signals || 0,
    row.buy_signals || 0,
    row.sell_signals || 0,
    `${(row.cumulative_return || 0).toFixed(2)}%`,
    `${(row.win_rate || 0).toFixed(2)}%`,
    `${(row.max_drawdown || 0).toFixed(2)}%`,
    row.total_trades || 0,
    row.profitable_trades || 0,
    row.final_capital || 0,
  ])
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `策略对比报告_${compareResult.value.stock_code}_${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('报告导出成功')
}

onMounted(() => {
  loadStrategies()

  // 设置默认日期（最近30天）
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  compareForm.end_date = end.toISOString().split('T')[0]
  compareForm.start_date = start.toISOString().split('T')[0]
})
</script>

<style scoped>
.strategy-compare {
  padding: 0;
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

.chart-section {
  margin-top: 20px;
  padding: 20px;
  background: #fafafa;
  border-radius: 4px;
}

.marker-legend {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.legend-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: #303133;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  display: inline-block;
}
</style>
