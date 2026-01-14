<template>
  <div class="strategy-aggregation">
    <!-- 顶部控制栏 -->
    <el-card class="control-panel" :body-style="{ padding: '15px 20px' }">
      <el-form :model="aggregationForm" :inline="true" class="control-form">
        <el-form-item label="选择策略" required>
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-popover
              v-model:visible="strategyPopoverVisible"
              placement="bottom-start"
              :width="400"
              trigger="click"
              @show="handlePopoverShow"
              @hide="handlePopoverHide"
            >
              <template #reference>
                <div class="custom-select">
                  <span v-if="aggregationForm.strategy_names.length === 0" class="placeholder">
                    请选择至少一个策略
                  </span>
                  <span v-else class="selected-text">
                    已选择 <span class="count">{{ aggregationForm.strategy_names.length }}</span> 项策略
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
                    {{ aggregationForm.strategy_names.length === filteredStrategies.length && filteredStrategies.length > 0 ? '全不选' : '全选' }}
                  </el-button>
                </div>
                
                <!-- 策略列表 -->
                <div class="strategy-list">
                  <el-checkbox-group v-model="aggregationForm.strategy_names" @change="handleStrategiesChange">
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
              v-model="aggregationForm.stock_code"
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
              :disabled="!aggregationForm.stock_code"
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
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleAnalyze" :loading="analyzing">
            <el-icon><DataAnalysis /></el-icon>
            开始分析
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Row 2: 策略配置面板 (选完策略即显示) -->
    <el-card v-if="aggregationForm.strategy_names.length > 0" class="config-panel" :body-style="{ padding: '15px 20px' }">
      <div class="config-container">
        <!-- 左侧：策略详细配置 (Tab页) -->
        <div class="config-section tabs-section">
          <div class="section-title">策略参数及权重配置</div>
          <el-tabs v-model="activeStrategyTab" type="border-card" class="strategy-tabs">
            <el-tab-pane
              v-for="strategyName in aggregationForm.strategy_names"
              :key="strategyName"
              :label="strategyName"
              :name="strategyName"
            >
              <div class="tab-content">
                <!-- 权重设置 -->
                <div class="param-group">
                  <span class="param-label">策略权重</span>
                  <div class="weight-control">
                    <el-slider
                      v-model="strategyWeightsMap[strategyName]"
                      :min="0.1" :max="10.0" :step="0.1"
                      :format-tooltip="(val: number) => val.toFixed(1)"
                      style="flex: 1; margin-right: 15px"
                    />
                    <el-input-number
                      v-model="strategyWeightsMap[strategyName]"
                      :min="0.1" :max="10.0" :step="0.1"
                      :precision="1"
                      size="small"
                      style="width: 100px"
                    />
                  </div>
                </div>

                <el-divider style="margin: 15px 0" />

                <!-- 策略参数 -->
                <div class="params-list">
                  <template v-if="strategyParamsMap[strategyName] && Object.keys(strategyParamsMap[strategyName]).length > 0">
                    <div class="param-group" v-for="(_, key) in strategyParamsMap[strategyName]" :key="key">
                      <div class="label-wrapper" style="display: flex; align-items: center; gap: 4px;">
                        <span class="param-label">{{ key }}</span>
                        <el-tooltip
                          v-if="strategyParamDescsMap[strategyName] && strategyParamDescsMap[strategyName][key]"
                          :content="strategyParamDescsMap[strategyName][key]"
                          placement="top"
                        >
                          <el-icon class="info-icon" style="cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                        </el-tooltip>
                      </div>
                      <el-input-number
                        v-model="strategyParamsMap[strategyName][key]"
                        size="small"
                        style="width: 150px"
                      />
                    </div>
                  </template>
                  <div v-else class="empty-params">该策略无需额外参数</div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 右侧：聚合阈值 (保持不变，垂直对齐) -->
        <div class="config-section thresholds-section">
          <div class="section-title">
            聚合阈值设置 
            <el-tag size="small" type="info">总权重: {{ totalWeight.toFixed(1) }}</el-tag>
          </div>
          <div class="thresholds-container">
            <div class="threshold-row">
              <span class="label">买入阈值</span>
              <div class="control">
                <el-slider v-model="aggregationSettings.buy_threshold" :min="0" :max="totalWeight" :step="0.1" size="small" style="width: 225px; margin-right: 15px;" />
                <el-input-number v-model="aggregationSettings.buy_threshold" :min="0" :max="totalWeight" :step="0.1" :precision="1" size="small" style="width: 100px" />
              </div>
            </div>
            <div class="threshold-row">
              <span class="label">卖出阈值</span>
              <div class="control">
                <el-slider v-model="aggregationSettings.sell_threshold" :min="0" :max="totalWeight" :step="0.1" size="small" style="width: 225px; margin-right: 15px;" />
                <el-input-number v-model="aggregationSettings.sell_threshold" :min="0" :max="totalWeight" :step="0.1" :precision="1" size="small" style="width: 100px" />
              </div>
            </div>
            <div class="threshold-row vertical">
              <span class="label">必需策略 (否决权)</span>
              <el-select
                v-model="aggregationSettings.required_strategies"
                multiple
                placeholder="选择策略..."
                size="small"
                style="width: 100%"
              >
                <el-option v-for="name in aggregationForm.strategy_names" :key="name" :label="name" :value="name" />
              </el-select>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Row 3: 分析核心区 (图表 & 统计) -->
    <div class="analysis-container">
      <!-- 左侧：图表区域 -->
      <div class="chart-section">
        <el-card class="chart-card" :body-style="{ padding: '0', height: '100%' }">
          <div class="chart-wrapper">
            <div v-if="analyzing" class="empty-chart">
              <el-empty description="正在分析中..." />
            </div>
            <div v-else-if="!analysisResult" class="empty-chart">
              <el-empty description="请选择策略和股票进行分析" />
            </div>
            <div v-else-if="klineData.length === 0" class="empty-chart">
              <el-empty description="暂无K线数据" />
            </div>
            <KlineChart
              v-if="klineData.length > 0"
              :data="klineData"
              :markers="signalMarkers"
              autosize
              :watermark="`${analysisResult.stock_code} - 策略聚合`"
              :dark-mode="isDark"
              :show-sub-chart="false"
              :simple-legend="true"
            />
          </div>
        </el-card>
      </div>

      <!-- 右侧：聚合表现统计 -->
      <div class="performance-section">
        <el-card class="performance-card" :body-style="{ padding: '15px' }">
          <template #header>
            <div class="card-header"><span>聚合表现</span></div>
          </template>
          
          <div v-if="analysisResult" class="stats-grid">
            <!-- Row 1 -->
            <div class="stat-item">
              <div class="label">
                累计收益
                <el-tooltip content="策略总收益率" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value" :class="getValueColor(analysisResult.statistics.total_return)">
                {{ (analysisResult.statistics.total_return || 0).toFixed(2) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                最大回撤
                <el-tooltip content="策略最大回撤幅度" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value down">
                {{ (analysisResult.statistics.max_drawdown || 0).toFixed(2) }}%
              </div>
            </div>

            <!-- Row 2 -->
            <div class="stat-item">
              <div class="label">
                年化收益
                <el-tooltip content="折算为年化收益率" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value" :class="getValueColor(analysisResult.statistics.annualized_return)">
                {{ (analysisResult.statistics.annualized_return || 0).toFixed(2) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                夏普比率
                <el-tooltip content="衡量风险调整后收益的指标" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value">{{ (analysisResult.statistics.sharpe_ratio || 0).toFixed(2) }}</div>
            </div>

            <!-- Row 3 -->
            <div class="stat-item">
              <div class="label">
                索提诺比率
                <el-tooltip content="衡量下行风险调整后收益的指标" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value">{{ (analysisResult.statistics.sortino_ratio || 0).toFixed(2) }}</div>
            </div>
            <div class="stat-item">
              <div class="label">
                盈亏比
                <el-tooltip content="平均盈利 / 平均亏损" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value">{{ (analysisResult.statistics.pl_ratio || 0).toFixed(2) }}</div>
            </div>

            <!-- Row 4 -->
            <div class="stat-item">
              <div class="label">
                胜率
                <el-tooltip content="盈利交易次数占比" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value down">{{ (analysisResult.statistics.win_rate || 0).toFixed(2) }}%</div>
            </div>
            <div class="stat-item">
              <div class="label">
                交易次数
                <el-tooltip content="总交易次数" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value">{{ analysisResult.statistics.total_trades }}</div>
            </div>

            <!-- Row 5 -->
            <div class="stat-item">
              <div class="label">
                基准收益
                <el-tooltip content="同期基准指数收益率" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value" :class="getValueColor(analysisResult.statistics.benchmark_return)">
                {{ (analysisResult.statistics.benchmark_return || 0).toFixed(2) }}%
              </div>
            </div>
            <div class="stat-item">
              <div class="label">
                基准回撤
                <el-tooltip content="同期基准指数最大回撤" placement="top"><el-icon class="info-icon"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="value down">
                {{ (analysisResult.statistics.benchmark_drawdown || 0).toFixed(2) }}%
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="60" />
        </el-card>
      </div>
    </div>

    <!-- 底部信号详情 -->
    <el-card v-if="analysisResult" class="details-card">
      <template #header>
        <div class="card-header">
          <span>信号详情</span>
        </div>
      </template>
      <el-table :data="aggregatedSignalsTable" stripe style="width: 100%" height="400">
        <el-table-column prop="date" label="日期" width="120" sortable />
        <el-table-column label="最终信号" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.final_signal === 1" type="success">买入</el-tag>
            <el-tag v-else-if="row.final_signal === -1" type="danger">卖出</el-tag>
            <span v-else style="color: #909399">持有</span>
          </template>
        </el-table-column>
        <el-table-column label="买入权重" width="140">
          <template #default="{ row }">
            <span :style="{ color: row.buy_weight >= aggregationSettings.buy_threshold ? '#67c23a' : '#909399' }">
              {{ row.buy_weight.toFixed(1) }} / {{ aggregationSettings.buy_threshold.toFixed(1) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="卖出权重" width="140">
          <template #default="{ row }">
            <span :style="{ color: row.sell_weight >= aggregationSettings.sell_threshold ? '#f56c6c' : '#909399' }">
              {{ row.sell_weight.toFixed(1) }} / {{ aggregationSettings.sell_threshold.toFixed(1) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="策略详情" min-width="300">
          <template #default="{ row }">
            <el-tag
              v-for="detail in row.strategy_details"
              :key="detail.strategy_name"
              :type="detail.signal === 1 ? 'success' : detail.signal === -1 ? 'danger' : 'info'"
              size="small"
              style="margin-right: 5px; margin-bottom: 5px"
            >
              {{ detail.strategy_name }} ({{ detail.weight.toFixed(1) }})
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, Search, DataAnalysis, Collection, Star, StarFilled, QuestionFilled } from '@element-plus/icons-vue'
import { useDark } from '@vueuse/core'
import { strategyAPI, strategyAggregationAPI, type StrategyInfo, type AggregationResponse } from '@/api/strategy'
import KlineChart from '@/components/KlineChart.vue'
import type { ChartData, Marker } from '@/components/KlineChart.vue'
import { dataAPI } from '@/api/data'
import { watchlistAPI } from '@/api/watchlist'

const isDark = useDark()

// State
const strategies = ref<StrategyInfo[]>([])
const analyzing = ref(false)
const analysisResult = ref<AggregationResponse | null>(null)
const klineData = ref<ChartData[]>([])
const signalMarkers = ref<Marker[]>([])
const favorites = ref<any[]>([])

// Popover state
const strategyPopoverVisible = ref(false)
const strategySearchQuery = ref('')
const activeStrategyTab = ref('')

// Form data
const aggregationForm = reactive({
  strategy_names: [] as string[],
  stock_code: '',
})

const dateRange = ref<[string, string]>(['', ''])

// Strategy weights map (strategy_name -> weight)
const strategyWeightsMap = reactive<Record<string, number>>({})

// Strategy params map (strategy_name -> params)
const strategyParamsMap = reactive<Record<string, Record<string, any>>>({})

// Strategy param descriptions map (strategy_name -> param_descriptions)
const strategyParamDescsMap = reactive<Record<string, Record<string, string>>>({})

// Aggregation settings
const aggregationSettings = reactive({
  buy_threshold: 2.0,
  sell_threshold: 2.0,
  required_strategies: [] as string[],
})

// Date shortcuts
const dateShortcuts = [
  {
    text: '最近1月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 1)
      return [start, end]
    },
  },
  {
    text: '最近3月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 3)
      return [start, end]
    },
  },
  {
    text: '最近半年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 6)
      return [start, end]
    },
  },
  {
    text: '最近一年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setFullYear(start.getFullYear() - 1)
      return [start, end]
    },
  },
]

// Computed
const filteredStrategies = computed(() => {
  if (!strategySearchQuery.value) return strategies.value
  const query = strategySearchQuery.value.toLowerCase()
  return strategies.value.filter(
    (s) => s.name.toLowerCase().includes(query) || s.description?.toLowerCase().includes(query)
  )
})

const totalWeight = computed(() => {
  return aggregationForm.strategy_names.reduce((sum, name) => {
    return sum + (strategyWeightsMap[name] || 1.0)
  }, 0)
})

const aggregatedSignalsTable = computed(() => {
  if (!analysisResult.value) return []
  // Filter non-zero signals and reverse to show newest first
  return analysisResult.value.aggregated_signals
    .filter(s => s.final_signal !== 0)
    .reverse()
})

const isFavorite = computed(() => {
  if (!aggregationForm.stock_code) return false
  return favorites.value.some(f => f.stock_code === aggregationForm.stock_code)
})

// Methods
const getValueColor = (value: number | undefined) => {
  if (value === undefined) return ''
  return value >= 0 ? 'up' : 'down'
} 

const handlePopoverShow = () => {
  strategySearchQuery.value = ''
}

const handlePopoverHide = () => {
  strategySearchQuery.value = ''
}

const handleToggleAll = () => {
  if (aggregationForm.strategy_names.length === filteredStrategies.value.length && filteredStrategies.value.length > 0) {
    // Unselect all
    aggregationForm.strategy_names = []
  } else {
    // Select all filtered
    aggregationForm.strategy_names = filteredStrategies.value.map(s => s.name)
  }
}

const handleStrategiesChange = async (value: string[]) => {
  // Initialize weights for new strategies
  value.forEach(name => {
    if (strategyWeightsMap[name] === undefined) {
      strategyWeightsMap[name] = 1.0
    }
    if (strategyParamsMap[name] === undefined) {
      loadStrategyParams(name)
    }
  })

  // Remove weights for deselected strategies
  Object.keys(strategyWeightsMap).forEach(name => {
    if (!value.includes(name)) {
      delete strategyWeightsMap[name]
      delete strategyParamsMap[name]
    }
  })

  // Set active tab to first selected strategy
  if (value.length > 0 && !value.includes(activeStrategyTab.value)) {
    activeStrategyTab.value = value[0]
  }

  // Remove from required strategies if deselected
  aggregationSettings.required_strategies = aggregationSettings.required_strategies.filter(s => value.includes(s))
}

const loadStrategyParams = async (strategyName: string) => {
  try {
    const info = await strategyAPI.getStrategyInfo(strategyName)
    
    // Store parameter descriptions
    strategyParamDescsMap[strategyName] = info.parameter_descriptions || {}
    
    // Initialize params based on descriptions to ensure all fields are shown
    const params: Record<string, any> = {}
    
    if (info.parameter_descriptions) {
      Object.keys(info.parameter_descriptions).forEach(key => {
        // Use backend default if available, otherwise 0
        if (info.parameters && info.parameters[key] !== undefined) {
          params[key] = info.parameters[key]
        } else {
          params[key] = 0 
        }
      })
    } else if (info.parameters) {
      // Fallback: use keys from parameters if descriptions missing
      Object.assign(params, info.parameters)
    }

    strategyParamsMap[strategyName] = params
  } catch (error) {
    console.error(`Failed to load params for ${strategyName}:`, error)
    strategyParamsMap[strategyName] = {}
    strategyParamDescsMap[strategyName] = {}
  }
}

const handleAnalyze = async () => {
  if (aggregationForm.strategy_names.length === 0) {
    ElMessage.warning('请至少选择一个策略')
    return
  }

  if (!aggregationForm.stock_code) {
    ElMessage.warning('请输入股票代码')
    return
  }

  if (!dateRange.value || !dateRange.value[0] || !dateRange.value[1]) {
    ElMessage.warning('请选择日期范围')
    return
  }

  analyzing.value = true

  try {
    // Prepare request
    const strategiesWithWeights = aggregationForm.strategy_names.map(name => ({
      name,
      params: strategyParamsMap[name] || {},
      weight: strategyWeightsMap[name] || 1.0,
    }))

    const result = await strategyAggregationAPI.analyzeAggregation({
      stock_code: aggregationForm.stock_code,
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      strategies: strategiesWithWeights,
      settings: {
        buy_threshold: aggregationSettings.buy_threshold,
        sell_threshold: aggregationSettings.sell_threshold,
        required_strategies: aggregationSettings.required_strategies,
      },
    })

    console.log('Aggregation request result:', result)
    analysisResult.value = result

    // Load K-line data
    console.log('Fetching K-line data...')
    const rawData = await dataAPI.getKlineData(aggregationForm.stock_code, dateRange.value[0], dateRange.value[1])
    console.log('K-line data fetched:', rawData.length, 'records')
    if (rawData.length > 0) {
      console.log('First record:', rawData[0])
    }

    klineData.value = rawData.map((item: any) => ({
      time: item.date, 
      open: Number(item.open),
      high: Number(item.high),
      low: Number(item.low),
      close: Number(item.close),
      volume: Number(item.volume),
    }))

    // Create markers from aggregated signals
    signalMarkers.value = result.aggregated_signals
      .filter((s) => s.final_signal !== 0)
      .map((s) => ({
        time: s.date,
        position: s.final_signal === 1 ? 'belowBar' : 'aboveBar',
        color: s.final_signal === 1 ? '#26a69a' : '#ef5350',
        shape: s.final_signal === 1 ? 'arrowUp' : 'arrowDown',
        text: s.final_signal === 1 ? '买' : '卖',
      }))

    ElMessage.success('分析完成')
  } catch (error: any) {
    console.error('Analysis error:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '分析失败')
  } finally {
    analyzing.value = false
  }
}

const handleReset = () => {
  aggregationForm.strategy_names = []
  aggregationForm.stock_code = ''
  Object.keys(strategyWeightsMap).forEach(key => delete strategyWeightsMap[key])
  Object.keys(strategyParamsMap).forEach(key => delete strategyParamsMap[key])
  aggregationSettings.buy_threshold = 2.0
  aggregationSettings.sell_threshold = 2.0
  aggregationSettings.required_strategies = []
  dateRange.value = ['', '']
  analysisResult.value = null
  klineData.value = []
  signalMarkers.value = []
}

// Load strategies on mount
const loadStrategies = async () => {
  try {
    const response = await strategyAPI.listStrategies()
    strategies.value = response.strategies
  } catch (error: any) {
    console.error('Load strategies error:', error)
    ElMessage.error('加载策略列表失败: ' + (error.message || '未知错误'))
  }
}

// Load favorites
const loadFavorites = async () => {
  try {
    const response = await watchlistAPI.getWatchlist()
    favorites.value = response || []
  } catch (error: any) {
    console.error('Load favorites error:', error)
  }
}

// Stock search
const searchStocks = async (queryString: string, cb: any) => {
  if (!queryString) {
    cb([])
    return
  }
  try {
    const results = await dataAPI.getStockList()
    const filtered = results.stocks.filter((stock: any) => 
      stock.code.includes(queryString) || stock.name.includes(queryString)
    )
    const suggestions = filtered.slice(0, 20).map((stock: any) => ({
      value: stock.code,
      code: stock.code,
      name: stock.name,
    }))
    cb(suggestions)
  } catch (error) {
    cb([])
  }
}

const handleStockSelect = (item: any) => {
  aggregationForm.stock_code = item.code
}

const handleFavoriteSelect = (fav: any) => {
  aggregationForm.stock_code = fav.stock_code
}

const toggleFavorite = async () => {
  if (!aggregationForm.stock_code) return
  
  try {
    if (isFavorite.value) {
      // Remove from favorites
      await watchlistAPI.removeFromWatchlist(aggregationForm.stock_code)
      ElMessage.success('已取消收藏')
    } else {
      // Add to favorites
      await watchlistAPI.addToWatchlist(aggregationForm.stock_code)
      ElMessage.success('已添加收藏')
    }
    await loadFavorites()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// Watch total weight changes to adjust thresholds
watch(totalWeight, (newTotal, oldTotal) => {
  if (oldTotal > 0 && newTotal > 0) {
    // Proportionally adjust thresholds
    const ratio = newTotal / oldTotal
    aggregationSettings.buy_threshold = Math.min(newTotal, aggregationSettings.buy_threshold * ratio)
    aggregationSettings.sell_threshold = Math.min(newTotal, aggregationSettings.sell_threshold * ratio)
  }
})

// Initialize
onMounted(() => {
  loadStrategies()
  loadFavorites()
})

// Set default date range (last 6 months)
const end = new Date()
const start = new Date()
start.setMonth(start.getMonth() - 6)
dateRange.value = [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
</script>

<style scoped lang="scss">
.strategy-aggregation {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 15px; // Vertical gap between rows
}

.control-panel {
  flex-shrink: 0;
}


// Config Panel (Row 2) Update
.config-panel {
  flex-shrink: 0;
  margin-bottom: 0px; 
}

.config-container {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.config-section {
  background-color: var(--el-fill-color-lighter);
  padding: 15px;
  border-radius: 4px;
  height: 100%;
  box-sizing: border-box; /* Ensure padding doesn't affect width calculation */
  display: flex;
  flex-direction: column;
}

.config-section.tabs-section {
  flex: 2; // Allocate more space for tabs
  min-width: 0; // Prevent flex overflow
}

.config-section.thresholds-section {
  flex: 0 0 420px; /* Increased to prevent text wrapping */
  min-width: 0;
}

.strategy-tabs {
  height: 220px; 
  display: flex; 
  flex-direction: column;
  
  :deep(.el-tabs__content) {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
  }
}

.tab-content {
  display: flex;
  flex-direction: column;
}

.param-group {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.param-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  width: 100px;
  flex-shrink: 0;
}

.weight-control {
  flex: 1;
  display: flex;
  align-items: center;
}

.params-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 10px;
}

.empty-params {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  padding: 10px 0;
}

// Thresholds Styles Update
.thresholds-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.threshold-row {
  display: flex;
  align-items: center;
  justify-content: space-between; /* Align left/right edges */
  margin-bottom: 12px;
  
  &.vertical {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px; /* Gap for vertical layout */
    
    .label {
      margin-bottom: 0px; /* Handled by gap */
    }
  }

  .label {
    font-size: 13px;
    color: var(--el-text-color-regular);
    white-space: nowrap; /* Prevent wrapping */
  }
  
  .control {
    flex: 1;
    margin-left: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

// Analysis Container (Row 3)
.analysis-container {
  display: flex;
  gap: 15px;
  min-height: 380px;
  flex: 1; // Grow to fill available space
}

.chart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chart-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chart-wrapper {
  height: 100%;
  width: 100%;
  position: relative;
}

.performance-section {
  width: 320px; // Fixed width for stats
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.performance-card {
  height: 100%;
  overflow-y: auto;
}


// Logic from StrategyAnalysis.vue
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
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-icon {
  cursor: pointer;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 15px; /* Added spacing */
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 24px; /* Fix height for alignment */
}

.stat-item .value {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.up { color: #f56c6c !important; }
.down { color: #67c23a !important; }


// Details Card (Row 4)
.details-card {
  flex-shrink: 0;
  max-height: 500px;
  display: flex;
  flex-direction: column;
  
  :deep(.el-card__body) {
    flex: 1;
    overflow: hidden;
    padding: 0;
  }
}

// Utility
.text-success { color: var(--el-color-success); }
.text-danger { color: var(--el-color-danger); }

.empty-chart {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

// Reuse previous common styles
.control-form { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.control-form :deep(.el-form-item) { margin-bottom: 0; }
.control-form :deep(.el-form-item__label) { line-height: 32px; margin-bottom: 0; }
.control-form :deep(.el-form-item__content) { line-height: 32px; }

// Strategy selector
.custom-select {
  min-width: 220px; height: 32px; padding: 0 30px 0 15px;
  display: flex; align-items: center;
  border: 1px solid var(--el-border-color); border-radius: 4px;
  cursor: pointer; transition: all 0.2s; position: relative;
  background-color: var(--el-fill-color-blank);
  &:hover { border-color: var(--el-border-color-hover); background-color: var(--el-fill-color-light); }
  .placeholder { color: var(--el-text-color-placeholder); font-size: 14px; }
  .selected-text { color: var(--el-text-color-primary); font-size: 14px; .count { color: var(--el-color-primary); font-weight: 600; } }
  .arrow-icon { position: absolute; right: 10px; transition: transform 0.3s; color: var(--el-text-color-secondary); &.is-reverse { transform: rotate(180deg); } }
}

.strategy-selector { display: flex; flex-direction: column; max-height: 500px; }
.selector-header { padding: 12px; border-bottom: 1px solid var(--el-border-color-lighter); display: flex; gap: 8px; }
.strategy-list { flex: 1; overflow-y: auto; padding: 8px; max-height: 400px; }
.strategy-item { padding: 8px 12px; cursor: pointer; transition: background-color 0.2s; &:hover { background-color: var(--el-fill-color-light); } }
.strategy-name { font-size: 14px; font-weight: 500; color: var(--el-text-color-primary); margin-bottom: 2px; }
.strategy-desc { font-size: 12px; color: var(--el-text-color-secondary); white-space: normal; line-height: 1.3; }
.selector-footer { padding: 12px; border-top: 1px solid var(--el-border-color-lighter); display: flex; justify-content: flex-end; }
.empty-text { text-align: center; color: var(--el-text-color-secondary); padding: 20px; }
</style>
