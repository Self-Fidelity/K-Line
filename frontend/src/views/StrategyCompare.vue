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
          <el-button type="primary" @click="handleViewChart">
            <el-icon><Picture /></el-icon>
            查看K线图
          </el-button>
        </div>
      </template>

      <!-- 统计对比表 -->
      <div v-if="compareResult.results && compareResult.results.length > 0" class="comparison-section">
        <h3>统计对比</h3>
        <el-table
          :data="comparisonTableData"
          stripe
          border
          style="width: 100%"
          :default-sort="{ prop: 'cumulative_return', order: 'descending' }"
        >
          <el-table-column prop="strategy_name" label="策略名称" width="150" fixed="left" />
          <el-table-column prop="total_signals" label="总信号数" width="100" align="right">
            <template #default="{ row }">{{ formatStatValue(row.total_signals, 'total_signals') }}</template>
          </el-table-column>
          <el-table-column prop="buy_signals" label="买入信号" width="100" align="right">
            <template #default="{ row }">{{ formatStatValue(row.buy_signals, 'buy_signals') }}</template>
          </el-table-column>
          <el-table-column prop="sell_signals" label="卖出信号" width="100" align="right">
            <template #default="{ row }">{{ formatStatValue(row.sell_signals, 'sell_signals') }}</template>
          </el-table-column>
          <el-table-column prop="cumulative_return" label="累计收益率" width="120" align="right" sortable>
            <template #default="{ row }">
              <span :style="getStatValueStyle('cumulative_return')">
                {{ formatStatValue(row.cumulative_return, 'cumulative_return') }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="win_rate" label="胜率" width="100" align="right" sortable>
            <template #default="{ row }">
              <span :style="getStatValueStyle('win_rate')">
                {{ formatStatValue(row.win_rate, 'win_rate') }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="max_drawdown" label="最大回撤" width="120" align="right" sortable>
            <template #default="{ row }">
              <span :style="getStatValueStyle('max_drawdown')">
                {{ formatStatValue(row.max_drawdown, 'max_drawdown') }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="total_trades" label="总交易次数" width="120" align="right">
            <template #default="{ row }">{{ formatStatValue(row.total_trades, 'total_trades') }}</template>
          </el-table-column>
          <el-table-column prop="profitable_trades" label="盈利交易" width="120" align="right">
            <template #default="{ row }">{{ formatStatValue(row.profitable_trades, 'profitable_trades') }}</template>
          </el-table-column>
        </el-table>
      </div>

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
import { Search, Picture } from '@element-plus/icons-vue'
import { strategyAPI, type StrategyInfo, type StrategyCompareRequest, type StrategyCompareResponse } from '@/api/strategy'
import { dataAPI, type StockInfo } from '@/api/data'

const router = useRouter()

const strategies = ref<StrategyInfo[]>([])
const comparing = ref(false)
const compareResult = ref<StrategyCompareResponse | null>(null)
const strategyInfoMap = ref<Record<string, StrategyInfo>>({})
const activeStrategyTab = ref<string>('')

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
    const response = await dataAPI.getStockList('all', false)
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
  
  return String(value)
}

// 获取统计值样式
const getStatValueStyle = (key: string): Record<string, string> => {
  if (key === 'cumulative_return' || key === 'win_rate') {
    return { color: 'red' }
  }
  if (key === 'max_drawdown') {
    return { color: 'green' }
  }
  return {}
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
</style>
