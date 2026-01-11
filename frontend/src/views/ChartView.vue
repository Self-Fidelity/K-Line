<template>
  <div class="chart-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>K线图查看</span>
        </div>
      </template>

      <!-- 查询表单 -->
      <el-form :model="chartForm" label-width="100px" :inline="true">
        <el-form-item label="股票代码" required>
          <el-autocomplete
            v-model="chartForm.stockCode"
            :fetch-suggestions="searchStocks"
            placeholder="输入股票代码或名称"
            style="width: 200px"
            @select="handleStockSelect"
          />
        </el-form-item>

        <el-form-item label="股票名称">
          <el-input
            v-model="chartForm.stockName"
            placeholder="自动填充"
            style="width: 150px"
            disabled
          />
        </el-form-item>

        <el-form-item label="开始日期">
          <el-date-picker
            v-model="chartForm.startDate"
            type="date"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 150px"
          />
        </el-form-item>

        <el-form-item label="结束日期">
          <el-date-picker
            v-model="chartForm.endDate"
            type="date"
            placeholder="选择结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 150px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleGenerateChart" :loading="generating">
            <el-icon><Search /></el-icon>
            生成图表
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 策略选择（可选） -->
      <el-card v-if="showStrategyOptions" style="margin-top: 20px">
        <template #header>
          <div class="card-header">
            <span>策略分析（可选）</span>
          </div>
        </template>
        <el-form :model="chartForm" label-width="100px" :inline="true">
          <el-form-item label="选择策略">
            <el-select
              v-model="chartForm.strategyName"
              placeholder="选择策略（可选）"
              clearable
              style="width: 200px"
            >
              <el-option
                v-for="strategy in strategies"
                :key="strategy.name"
                :label="strategy.name"
                :value="strategy.name"
              >
                <div>
                  <div style="font-weight: 500">{{ strategy.name }}</div>
                  <div style="font-size: 12px; color: #909399">{{ strategy.description }}</div>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item v-if="chartForm.strategyName" label="图表类型">
            <el-radio-group v-model="chartForm.chartType">
              <el-radio :value="'kline'">K线图</el-radio>
              <el-radio :value="'kline_with_ma'">K线图+均线</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 策略参数配置 -->
      <el-card v-if="chartForm.strategyName && currentStrategyInfo" style="margin-top: 20px">
        <template #header>
          <div class="card-header">
            <span>策略参数配置</span>
          </div>
        </template>
        <p v-if="Object.keys(strategyParams).length === 0" style="color: #909399">
          该策略无需额外参数配置
        </p>
        <el-form
          v-else
          :model="strategyParams"
          label-width="150px"
        >
          <el-form-item
            v-for="(value, key) in strategyParams"
            :key="key"
            :label="getParameterLabel(key)"
          >
            <el-input-number
              v-model="strategyParams[key]"
              :min="getParameterMin(key)"
              :precision="getParameterPrecision(key)"
              style="width: 200px"
            />
            <div v-if="getParameterDescription(key)" class="parameter-description">
              {{ getParameterDescription(key) }}
            </div>
          </el-form-item>
        </el-form>
      </el-card>
    </el-card>

    <!-- 图表显示区域 -->
    <el-card v-if="chartUrl" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>图表</span>
          <el-button type="primary" size="small" @click="handleDownloadChart">
            <el-icon><Download /></el-icon>
            下载图表
          </el-button>
        </div>
      </template>
      <div class="chart-container">
        <iframe
          :src="chartUrl"
          frameborder="0"
          class="chart-iframe"
          @load="handleChartLoad"
        ></iframe>
      </div>
    </el-card>

    <!-- 加载提示 -->
    <el-card v-if="generating" style="margin-top: 20px">
      <el-empty description="正在生成图表，请稍候..." :image-size="100" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import { chartAPI, type ChartGenerateRequest } from '@/api/chart'
import { dataAPI } from '@/api/data'
import { strategyAPI, type StrategyInfo } from '@/api/strategy'

const route = useRoute()
const router = useRouter()

const generating = ref(false)
const chartUrl = ref<string>('')
const chartId = ref<string>('')
const strategies = ref<StrategyInfo[]>([])
const showStrategyOptions = ref(false)
const currentStrategyInfo = ref<StrategyInfo | null>(null)
const strategyParams = reactive<Record<string, any>>({})

// 默认参数配置（可以根据策略类型设置默认值）
const defaultParams: Record<string, Record<string, number>> = {
  'MA Strategy': { short_period: 5, long_period: 20 },
  'RSI Strategy': { period: 14, overbought: 70, oversold: 30 },
  'MACD Strategy': { fast_period: 12, slow_period: 26, signal_period: 9 },
  'Bollinger Strategy': { period: 20, num_std: 2 },
  'Momentum Strategy': { period: 10 },
}

const chartForm = reactive<ChartGenerateRequest & { chartType: string }>({
  stockCode: '',
  stockName: '',
  startDate: '',
  endDate: '',
  strategyName: '',
  strategy_params: {},
  chart_type: 'kline',
  chartType: 'kline',
})

// 从路由参数获取股票信息
onMounted(async () => {
  const stock = route.query.stock as string
  const name = route.query.name as string
  const strategy = route.query.strategy as string
  const start = route.query.start as string
  const end = route.query.end as string

  // 先加载策略列表
  await loadStrategies()

  // 设置日期（从路由参数获取，或使用默认值）
  if (start && end) {
    chartForm.startDate = start
    chartForm.endDate = end
  } else {
    // 设置默认日期（最近30天）
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - 30)
    chartForm.endDate = endDate.toISOString().split('T')[0]
    chartForm.startDate = startDate.toISOString().split('T')[0]
  }

  if (stock) {
    chartForm.stockCode = stock
    chartForm.stockName = name || ''
    
    // 如果从策略分析跳转，设置策略
    if (strategy) {
      chartForm.strategyName = strategy
      showStrategyOptions.value = true
      // 加载策略信息和参数
      await handleStrategyChange(strategy)
    }
    
    // 自动生成图表
    handleGenerateChart()
  }
})

// 加载策略列表
const loadStrategies = async () => {
  try {
    const response = await strategyAPI.listStrategies()
    strategies.value = response.strategies
  } catch (error: any) {
    console.error('加载策略列表失败:', error)
  }
}

// 策略变更处理
const handleStrategyChange = async (strategyName: string) => {
  if (!strategyName) {
    currentStrategyInfo.value = null
    Object.keys(strategyParams).forEach((key) => delete strategyParams[key])
    return
  }

  try {
    // 获取策略详细信息
    const info = await strategyAPI.getStrategyInfo(strategyName)
    currentStrategyInfo.value = info

    // 初始化策略参数
    Object.keys(strategyParams).forEach((key) => delete strategyParams[key])
    
    // 初始化策略参数
    // 注意：后端返回的parameter_descriptions是字符串字典，不是对象字典
    // 我们需要从策略的默认参数中获取默认值
    if (info.parameter_descriptions) {
      for (const [key] of Object.entries(info.parameter_descriptions)) {
        // 设置默认值（可以根据策略类型设置不同的默认值）
        // 这里先使用简单的默认值，后续可以从后端获取
        strategyParams[key] = 1
      }
    }
    
    // 如果有策略实例，可以获取默认参数值
    // 但当前后端返回的是字符串，所以我们需要使用硬编码的默认值
    // 或者从parameter_descriptions字符串中解析默认值（如果字符串中包含默认值信息）
  } catch (error: any) {
    console.error('获取策略信息失败:', error)
    ElMessage.error('获取策略信息失败')
  }
}

// 搜索股票
const searchStocks = async (queryString: string, cb: (suggestions: any[]) => void) => {
  if (!queryString) {
    cb([])
    return
  }

  try {
    const response = await dataAPI.getStockList('all', false)
    const stocks = response.stocks.filter(
      (stock) =>
        stock.code.toLowerCase().includes(queryString.toLowerCase()) ||
        stock.name.toLowerCase().includes(queryString.toLowerCase())
    )
    const suggestions = stocks.slice(0, 10).map((stock) => ({
      value: stock.code,
      label: `${stock.code} - ${stock.name}`,
      stock: stock,
    }))
    cb(suggestions)
  } catch (error: any) {
    console.error('搜索股票失败:', error)
    cb([])
  }
}

// 股票选择
const handleStockSelect = (item: any) => {
  if (item.stock) {
    chartForm.stockCode = item.stock.code
    chartForm.stockName = item.stock.name
  }
}

// 生成图表
const handleGenerateChart = async () => {
  if (!chartForm.stockCode) {
    ElMessage.warning('请输入股票代码')
    return
  }

  generating.value = true
  chartUrl.value = ''

  try {
    // 更新策略参数（从表单中获取）
    if (chartForm.strategyName && Object.keys(strategyParams).length > 0) {
      chartForm.strategy_params = { ...strategyParams }
    }
    
    // 构建请求
    const request: ChartGenerateRequest = {
      stock_code: chartForm.stockCode,
      stock_name: chartForm.stockName,
      start_date: chartForm.startDate || undefined,
      end_date: chartForm.endDate || undefined,
      strategy_name: chartForm.strategyName || undefined,
      strategy_params: chartForm.strategy_params || {},
      chart_type: chartForm.chartType === 'kline_with_ma' ? 'kline_with_ma' : 'kline',
      ma_periods: chartForm.chartType === 'kline_with_ma' ? [5, 20, 60] : undefined,
    }

    const response = await chartAPI.generateChart(request)
    chartId.value = response.chart_id
    
    // 获取图表URL（后端已配置静态文件服务）
    chartUrl.value = response.chart_url
    
    // 如果chart_url是相对路径，转换为完整URL（使用后端API地址）
    if (chartUrl.value.startsWith('/')) {
      // 使用后端API地址（从apiClient获取）
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      chartUrl.value = `${apiBaseUrl}${chartUrl.value}`
    }
    
    ElMessage.success('图表生成成功')
    showStrategyOptions.value = true
  } catch (error: any) {
    console.error('生成图表失败:', error)
    ElMessage.error(error.response?.data?.detail || '生成图表失败')
  } finally {
    generating.value = false
  }
}

// 图表加载完成
const handleChartLoad = () => {
  console.log('图表加载完成')
}

// 下载图表
const handleDownloadChart = () => {
  if (chartUrl.value) {
    // 打开新窗口下载
    window.open(chartUrl.value, '_blank')
  }
}

// 获取参数标签（将下划线命名转换为中文标签）
const getParameterLabel = (key: string): string => {
  const labelMap: Record<string, string> = {
    'short_period': '短期周期',
    'long_period': '长期周期',
    'period': '周期',
    'num_std': '标准差倍数',
    'std_dev': '标准差倍数',
    'oversold': '超卖阈值',
    'overbought': '超买阈值',
    'fast_period': '快线周期',
    'slow_period': '慢线周期',
    'signal_period': '信号线周期',
    'shadow_ratio': '影线比例',
    'lookback': '回看周期',
    'doji_threshold': '十字星阈值',
  }
  return labelMap[key] || key
}

// 获取参数描述
const getParameterDescription = (key: string): string => {
  if (!currentStrategyInfo.value?.parameter_descriptions) return ''
  // 后端返回的是字符串字典，直接返回字符串
  const desc = currentStrategyInfo.value.parameter_descriptions[key]
  return typeof desc === 'string' ? desc : ''
}

// 获取参数最小值
const getParameterMin = (key: string): number => {
  if (!currentStrategyInfo.value?.parameter_descriptions) return 1
  const paramDesc = currentStrategyInfo.value.parameter_descriptions[key] as any
  return paramDesc?.min ?? 1
}

// 获取参数精度
const getParameterPrecision = (key: string): number => {
  if (!currentStrategyInfo.value?.parameter_descriptions) return 0
  // 如果参数名包含std、oversold、overbought等，使用1位小数
  if (key.includes('std') || key.includes('oversold') || key.includes('overbought')) {
    return 1
  }
  return 0
}

// 重置表单
const handleReset = () => {
  chartForm.stockCode = ''
  chartForm.stockName = ''
  chartForm.startDate = ''
  chartForm.endDate = ''
  chartForm.strategyName = ''
  chartForm.chartType = 'kline'
  chartUrl.value = ''
  chartId.value = ''
  showStrategyOptions.value = false
  currentStrategyInfo.value = null
  Object.keys(strategyParams).forEach((key) => delete strategyParams[key])
  
  // 设置默认日期
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  chartForm.endDate = end.toISOString().split('T')[0]
  chartForm.startDate = start.toISOString().split('T')[0]
}
</script>

<style scoped>
.chart-view {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
}

.chart-container {
  width: 100%;
  min-height: 900px;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.chart-iframe {
  display: block;
  width: 100%;
  max-width: 100%;
  height: 900px;
  border: none;
  overflow: hidden;
}

.parameter-description {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}
</style>
