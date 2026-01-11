<template>
  <div class="strategy-analysis">
    <!-- 顶部控制栏 -->
    <el-card class="control-panel" :body-style="{ padding: '15px 20px' }">
      <el-form :model="analysisForm" :inline="true" class="control-form">
        <el-form-item label="策略">
          <el-select
            v-model="analysisForm.strategyName"
            placeholder="选择策略"
            style="width: 180px"
            filterable
            @change="handleStrategyChange"
          >
            <el-option
              v-for="strategy in strategies"
              :key="strategy.name"
              :label="strategy.name"
              :value="strategy.name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="股票">
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
        </el-form-item>

        <el-form-item label="时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
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
            <div v-if="!analysisResult && !analyzing" class="empty-chart">
              <el-empty description="请选择策略和股票进行分析" />
            </div>
            
            <KlineChart
              v-else-if="activeChartTab === 'kline'"
              :data="klineData"
              :markers="signalMarkers"
              :lines="indicatorLines"
              :height="600"
              :watermark="watermarkText"
            />
            
            <KlineChart
              v-else-if="activeChartTab === 'equity'"
              :data="equityChartData"
              :lines="equityLines"
              :height="600"
              :watermark="watermarkText"
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
              <div class="label">累计收益</div>
              <div class="value" :class="getColorClass(analysisResult.statistics.cumulative_return)">
                {{ formatNumber(analysisResult.statistics.cumulative_return) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">最大回撤</div>
              <div class="value down">
                {{ formatNumber(analysisResult.statistics.max_drawdown) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">胜率</div>
              <div class="value" :class="getColorClass(analysisResult.statistics.win_rate - 50)">
                {{ formatNumber(analysisResult.statistics.win_rate) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">交易次数</div>
              <div class="value">{{ analysisResult.statistics.total_trades }}</div>
            </div>
             <div class="stat-item">
              <div class="label">基准收益</div>
              <div class="value" :class="getColorClass(analysisResult.statistics.benchmark_return)">
                {{ formatNumber(analysisResult.statistics.benchmark_return) }}%
              </div>
            </div>
             <div class="stat-item">
              <div class="label">基准回撤</div>
              <div class="value down">
                {{ formatNumber(analysisResult.statistics.benchmark_max_drawdown) }}%
              </div>
            </div>
          </div>
        </el-card>

        <!-- 参数配置 -->
        <el-card class="info-card" v-if="currentStrategyInfo">
          <template #header>
            <div class="card-title">
              <span>参数配置</span>
              <el-tooltip :content="currentStrategyInfo.description" placement="top">
                <el-icon><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          
          <el-form size="small" label-position="top">
            <el-form-item
              v-for="(val, key) in strategyParams"
              :key="key"
              :label="getParameterLabel(key)"
            >
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
                <el-tag size="small" :type="trade.profit_rate > 0 ? 'danger' : 'success'">
                  {{ trade.profit_rate?.toFixed(2) }}%
                </el-tag>
              </div>
              <div class="trade-details">
                <span>买: {{ trade.buy_price?.toFixed(2) }}</span>
                <span>卖: {{ trade.price?.toFixed(2) }}</span>
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
import { ElMessage } from 'element-plus'
import { DataAnalysis, InfoFilled } from '@element-plus/icons-vue'
import { strategyAPI, type StrategyInfo, type StrategyAnalyzeResponse } from '@/api/strategy'
import { dataAPI } from '@/api/data'
import KlineChart, { type ChartData, type Marker, type LineData } from '@/components/KlineChart.vue'

// --- State ---
const strategies = ref<StrategyInfo[]>([])
const currentStrategyInfo = ref<StrategyInfo | null>(null)
const strategyParams = reactive<Record<string, number>>({})
const analyzing = ref(false)
const analysisResult = ref<StrategyAnalyzeResponse | null>(null)
const activeChartTab = ref<'kline' | 'equity'>('kline')
const dateRange = ref<[string, string]>(['', ''])

const analysisForm = reactive({
  strategyName: '',
  stockCode: '',
})

// --- Computed Props ---

const watermarkText = computed(() => {
  if (!analysisResult.value) return 'K-Line Strategy'
  return `${analysisResult.value.stock_code} ${analysisResult.value.strategy_name}`
})

const klineData = computed<ChartData[]>(() => {
  if (!analysisResult.value?.result) return []
  return analysisResult.value.result.map((item: any) => ({
    time: item.date,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
    volume: item.volume
  }))
})

const signalMarkers = computed<Marker[]>(() => {
  if (!analysisResult.value?.result) return []
  const markers: Marker[] = []
  
  analysisResult.value.result.forEach((item: any) => {
    if (item.signal === 1) {
      markers.push({
        time: item.date,
        position: 'belowBar',
        color: '#e91e63',
        shape: 'arrowUp',
        text: 'Buy'
      })
    } else if (item.signal === -1) {
      markers.push({
        time: item.date,
        position: 'aboveBar',
        color: '#2196F3',
        shape: 'arrowDown',
        text: 'Sell'
      })
    }
  })
  return markers
})

const indicatorLines = computed<LineData[]>(() => {
  if (!analysisResult.value?.result) return []
  const data = analysisResult.value.result
  const lines: LineData[] = []
  
  // 自动检测MA等指标列
  const keys = Object.keys(data[0] || {})
  const indicatorKeys = keys.filter(k => 
    k.startsWith('MA') || k.startsWith('EMA') || k.startsWith('UPPER') || k.startsWith('LOWER')
  )
  
  const colors = ['#2962FF', '#E91E63', '#FF6D00', '#00B8D4']
  
  indicatorKeys.forEach((key, index) => {
    lines.push({
      name: key,
      data: data.map((d: any) => ({ time: d.date, value: d[key] })).filter((d: any) => d.value),
      color: colors[index % colors.length],
      lineWidth: 1
    })
  })
  
  return lines
})

const equityChartData = computed<ChartData[]>(() => {
  // 权益图本质上是线图，但KlineChart组件复用了K线结构
  // 这里我们用K线图组件画Equity Curve有点奇怪，但可以用LineSeries
  // 为了复用组件，我们构造一个只有close价格的数据集
  if (!analysisResult.value?.statistics?.dates) return []
  
  const dates = analysisResult.value.statistics.dates
  const equity = analysisResult.value.statistics.equity_curve
  
  return dates.map((date: string, i: number) => ({
    time: date,
    open: equity[i],
    high: equity[i],
    low: equity[i],
    close: equity[i],
    volume: 0
  }))
})

const equityLines = computed<LineData[]>(() => {
  if (!analysisResult.value?.statistics) return []
  const stats = analysisResult.value.statistics
  const dates = stats.dates
  
  return [
    {
      name: '策略权益',
      data: dates.map((d: string, i: number) => ({ time: d, value: stats.equity_curve[i] })),
      color: '#e91e63',
      lineWidth: 2
    },
    {
      name: '基准收益 (Buy&Hold)',
      data: dates.map((d: string, i: number) => ({ time: d, value: stats.benchmark_curve[i] })),
      color: '#78909c',
      lineWidth: 1
    }
  ]
})

const reversedTrades = computed(() => {
  if (!analysisResult.value?.statistics?.trades) return []
  return [...analysisResult.value.statistics.trades].reverse()
})

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
  }
  return labelMap[key] || key
}

// 默认参数配置
const defaultParams: Record<string, Record<string, number>> = {
  'MA Strategy': { short_period: 5, long_period: 20 },
  'RSI Strategy': { period: 14, overbought: 70, oversold: 30 },
  'MACD Strategy': { fast_period: 12, slow_period: 26, signal_period: 9 },
  'Bollinger Strategy': { period: 20, num_std: 2 },
  'Momentum Strategy': { period: 10 },
}

const loadStrategies = async () => {
  try {
    const response = await strategyAPI.listStrategies()
    strategies.value = response.strategies
  } catch (error: any) {
    ElMessage.error('加载策略失败')
  }
}

const handleStrategyChange = async (strategyName: string) => {
  // 重置参数
  Object.keys(strategyParams).forEach(k => delete strategyParams[k])
  
  try {
    const info = await strategyAPI.getStrategyInfo(strategyName)
    currentStrategyInfo.value = info
    if (defaultParams[strategyName]) {
      Object.assign(strategyParams, defaultParams[strategyName])
    }
  } catch (e) {
    console.error(e)
  }
}

const searchStocks = async (query: string, cb: any) => {
  if (!query) return cb([])
  try {
    const res = await dataAPI.getStockList('all', false)
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

onMounted(() => {
  loadStrategies()
  // Default date range: last 6 months
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - 6)
  dateRange.value = [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
  analysisForm.startDate = dateRange.value[0]
  analysisForm.endDate = dateRange.value[1]
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

.chart-wrapper {
  flex: 1;
  position: relative;
  min-height: 500px;
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
}

.stat-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
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
</style>
