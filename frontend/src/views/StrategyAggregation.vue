<template>
  <div class="strategy-aggregation">
    <!-- 顶部控制栏 -->
    <!-- 顶部控制栏 -->
    <el-card class="control-panel" :body-style="{ padding: '15px 20px' }">
      <div class="header-toolbar">
        <!-- 左侧控件组: 股票 + 策略 + 日期 -->
        <div class="toolbar-left">
          <!-- 1. 股票选择 -->
          <div class="stock-selector-wrapper">
             <el-dropdown trigger="click" @command="handleFavoriteSelect" style="margin-right: 8px">
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

             <el-select
              v-model="aggregationForm.stock_code"
              filterable
              remote
              placeholder="搜索股票代码/名称"
              :remote-method="searchStocks"
              :loading="stockSearchLoading"
              style="width: 220px"
              @change="handleStockChange"
            >
              <el-option
                v-for="item in stockOptions"
                :key="item.code"
                :label="`${item.code} ${item.name}`"
                :value="item.code"
              >
                <div class="stock-option">
                  <span>{{ item.name }}</span>
                  <span class="stock-code">{{ item.code }}</span>
                </div>
              </el-option>
            </el-select>
            
            <el-button 
              :icon="isFavorite ? StarFilled : Star" 
              circle 
              size="small"
              :type="isFavorite ? 'warning' : 'default'"
              @click="toggleFavorite"
              title="收藏当前股票"
              style="margin-left: 8px;"
              :disabled="!aggregationForm.stock_code"
            />
          </div>

          <el-divider direction="vertical" style="height: 24px" />

          <!-- 2. 策略选择 (Popover) -->
          <el-popover
            v-model:visible="strategyPopoverVisible"
            placement="bottom-start"
            :width="400"
            trigger="click"
            @show="handlePopoverShow"
            @hide="handlePopoverHide"
          >
            <template #reference>
              <div class="custom-select" :class="{ 'has-value': aggregationForm.strategy_names.length > 0 }">
                <span v-if="aggregationForm.strategy_names.length === 0" class="placeholder">
                  选择策略 (至少1项)
                </span>
                <span v-else class="selected-text">
                  已选 <span class="count">{{ aggregationForm.strategy_names.length }}</span> 项策略
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

           <el-divider direction="vertical" style="height: 24px" />

          <!-- 3. 日期选择 -->
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            style="width: 240px"
          />
        </div>

        <!-- 右侧操作栏: 方案管理 + 分析 -->
        <div class="toolbar-right">
          <el-dropdown trigger="click" @visible-change="(v) => v && fetchSchemes()">
            <el-button :icon="FolderOpened" style="margin-right: 10px">
              加载方案<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <div v-loading="loadingSchemes" style="min-width: 280px; max-height: 400px; overflow-y: auto;">
                  <template v-if="savedSchemes.length > 0">
                    <el-dropdown-item v-for="scheme in savedSchemes" :key="scheme.id">
                      <div class="scheme-item" style="display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 5px 0;">
                        <span @click="loadScheme(scheme)" style="flex: 1; margin-right: 10px;">
                          {{ scheme.name }} 
                          <span v-if="scheme.stock_code" class="scheme-tag">{{ scheme.stock_code }}</span>
                        </span>
                        <el-icon 
                          class="delete-icon" 
                          @click.stop="deleteScheme(scheme.id)"
                          style="color: var(--el-text-color-secondary); cursor: pointer;"
                        ><Delete /></el-icon>
                      </div>
                    </el-dropdown-item>
                  </template>
                  <el-empty v-else description="暂无保存的方案" :image-size="40" />
                </div>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-button type="success" :icon="FolderAdd" plain @click="openSaveSchemeDialog">
            保存方案
          </el-button>
          
          <el-button type="primary" :icon="DataAnalysis" :loading="analyzing" @click="handleAnalyze" style="margin-left: 15px">
            开始聚合分析
          </el-button>
        </div>
      </div>

       <!-- 方案保存对话框 (Nested correctly) -->
      <el-dialog
        v-model="schemeDialogVisible"
        title="保存策略方案"
        width="400px"
      >
        <el-form :model="schemeForm" label-width="80px">
          <el-form-item label="方案名称">
            <el-input v-model="schemeForm.name" placeholder="例如：稳健型组合" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="schemeForm.description" type="textarea" placeholder="可选备注..." />
          </el-form-item>
          <el-form-item label="绑定股票">
            <el-switch
              v-model="schemeForm.stock_code"
              :active-value="aggregationForm.stock_code"
              :inactive-value="''"
              active-text="仅对当前股票可见"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="schemeDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveScheme">保存</el-button>
          </span>
        </template>
      </el-dialog>
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
                <div class="params-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                  <span class="section-subtitle" style="font-weight: bold; font-size: 14px;">策略参数</span>
                  <el-popover
                    placement="bottom"
                    :width="300"
                    trigger="click"
                    @show="loadSavedParams(strategyName)"
                  >
                    <template #reference>
                      <el-button link type="primary" size="small" :icon="Download">
                        加载优化参数
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
                              {{ getMetricLabel(set.target_metric) }}: {{ set.best_score?.toFixed(2) }}
                            </span>
                          </div>
                          <div style="font-size: 12px; color: var(--el-text-color-secondary);">
                            {{ set.date_range || '无日期范围' }}
                          </div>
                        </div>
                      </div>
                      <el-empty v-else description="暂无优化记录" :image-size="40" />
                    </div>
                  </el-popover>
                </div>
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
                        v-bind="getParamProps(key, strategyName)"
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
              :watermark="`${analysisResult?.stock_name} - 策略聚合`"
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
import { ArrowDown, Search, DataAnalysis, Collection, Star, StarFilled, QuestionFilled, Download, Delete, FolderOpened, FolderAdd } from '@element-plus/icons-vue'
import { useDark } from '@vueuse/core'
import { strategyAPI, strategyAggregationAPI, type StrategyInfo, type AggregationResponse } from '@/api/strategy'
import KlineChart from '@/components/KlineChart.vue'
import type { ChartData, Marker } from '@/components/KlineChart.vue'
import { dataAPI } from '@/api/data'
import { watchlistAPI } from '@/api/watchlist'
import { paramSetsAPI, type ParamSet } from '@/api/param-sets'
import { aggregationSchemesAPI, type AggregationScheme } from '@/api/aggregation-schemes'


const isDark = useDark()

// State
const strategies = ref<StrategyInfo[]>([])
const analyzing = ref(false)
const analysisResult = ref<AggregationResponse | null>(null)
const klineData = ref<ChartData[]>([])
const signalMarkers = ref<Marker[]>([])
const favorites = ref<any[]>([])
const availableParamSets = ref<Record<string, ParamSet[]>>({})
const loadingParamSets = ref<Record<string, boolean>>({})

// Popover state
const strategyPopoverVisible = ref(false)
const strategySearchQuery = ref('')
const activeStrategyTab = ref('')

// Form data
const aggregationForm = reactive({
  strategy_names: [] as string[],
  stock_code: '',
  start_date: '',
  end_date: '',
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

// Strategy parameter types map (strategy_name -> { param_name: type_str })
const strategyTypesMap = reactive<Record<string, Record<string, string>>>({})

// Date shortcuts
const dateShortcuts = [
  {
    text: '最近1个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 1)
      return [start, end]
    },
  },
  {
    text: '最近3个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 3)
      return [start, end]
    },
  },
  {
    text: '最近6个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 6)
      return [start, end]
    },
  },
  {
    text: '最近1年',
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

// Scheme Management
const schemeDialogVisible = ref(false)
const savedSchemes = ref<AggregationScheme[]>([])
const loadingSchemes = ref(false)
const schemeForm = reactive({
  name: '',
  description: '',
  stock_code: ''
})

// Stock Search Logic
const allStocks = ref<any[]>([])
const stockOptions = ref<any[]>([])
const stockSearchLoading = ref(false)
const currentStockInfo = ref<any>(null)

// Initialize stocks on mount
// Initialize stocks on mount
onMounted(async () => {
  try {
    const res = await dataAPI.getStockList('main')
    allStocks.value = res.stocks
    stockOptions.value = allStocks.value.slice(0, 20) // Initial list
    
    // Check for imported data from StrategyCompare
    const importDataStr = localStorage.getItem('strategies_aggregation_import')
    if (importDataStr) {
      try {
        const importData = JSON.parse(importDataStr)
        // 1. Set basic info
        if (importData.stock_code) aggregationForm.stock_code = importData.stock_code
        if (importData.start_date && importData.end_date) {
            dateRange.value = [importData.start_date, importData.end_date]
            aggregationForm.start_date = importData.start_date
            aggregationForm.end_date = importData.end_date
        }

        // 2. Set strategies and trigger change to load metadata
        if (importData.strategy_names && importData.strategy_names.length > 0) {
            aggregationForm.strategy_names = importData.strategy_names
            await handleStrategiesChange(importData.strategy_names)

            // 3. Override params (handleStrategiesChange clears them, so we set them after)
            if (importData.params) {
                // Merge params carefully
                for (const [sName, params] of Object.entries(importData.params)) {
                    if (strategyParamsMap[sName]) {
                        Object.assign(strategyParamsMap[sName], params)
                    } else {
                        strategyParamsMap[sName] = params as Record<string, any>
                    }
                }
            }

            // 4. Set weights
            if (importData.weights) {
                 for (const [sName, weight] of Object.entries(importData.weights)) {
                     strategyWeightsMap[sName] = weight as number
                 }
            }
        }
        
        // Clear storage
        localStorage.removeItem('strategies_aggregation_import')
        ElMessage.success('已自动加载策略组合配置')
        
      } catch (e) {
        console.error('Failed to parse import data', e)
        localStorage.removeItem('strategies_aggregation_import')
      }
    }

    // If stock code exists (e.g. from nav or import), set info
    if (aggregationForm.stock_code) {
      handleStockChange(aggregationForm.stock_code)
    }
  } catch (e) {
    console.error('Failed to load stock list', e)
  }
})

const searchStocks = (query: string) => {
  if (query) {
    stockSearchLoading.value = true
    setTimeout(() => {
      stockOptions.value = allStocks.value.filter(item => {
        return item.code.toLowerCase().includes(query.toLowerCase()) ||
               item.name.includes(query)
      }).slice(0, 20) // Limit results
      stockSearchLoading.value = false
    }, 200)
  } else {
    stockOptions.value = allStocks.value.slice(0, 20)
  }
}

const handleStockChange = (val: string) => {
  const stock = allStocks.value.find(item => item.code === val)
  if (stock) {
    // Fetch latest price info if needed, or use list info if available
    // Assuming list info has basic data, but better to fetch quote if separate API exists.
    // dataAPI.getStockInfo might give more details.
    // For now use local data + mock price change if not in list
    // Actually getStockList returns StockInfo which has code, name.
    // We might need quote data. dataAPI.getKlineData(val, 1day) or similar?
    // Let's just set name for now.
    currentStockInfo.value = {
        name: stock.name,
        close: 0, // Placeholder as list might not have price
        pct_chg: 0
    }
    // Try to fetch real quote?
    fetchStockQuote(val)
  }
}

const handleFavoriteSelect = (fav: any) => {
  aggregationForm.stock_code = fav.stock_code
  handleStockChange(fav.stock_code)
}

const fetchStockQuote = async (code: string) => {
    try {
        // Mocking or fetching latest kline?
        // Use dataAPI.getKlineData for latest 1 day?
        // Or if we have a quote API.
        // For this task, strict price display isn't critical but "currentStockInfo" is used in template.
        // Let's fetch basic info from getStockInfo
        const info = await dataAPI.getStockInfo(code)
        // info doesn't have price. 
        // We'll leave price as 0 or implement a quote API later.
        // Changing template compliance:
        // Template uses currentStockInfo.close and pct_chg.
        // If not available, we hide or show 0.
        // I will use a dummy random or empty for now to prevent errors, 
        // as real quote API is not in dataAPI interface shown.
        // Wait, list response might have it? "latest_date" only.
        // I will set dummy values to avoid template errors.
        currentStockInfo.value = { ...currentStockInfo.value, close: 0, pct_chg: 0 }
    } catch(e) {}
}

const fetchSchemes = async () => {
  loadingSchemes.value = true
  try {
    savedSchemes.value = await aggregationSchemesAPI.getSchemes(aggregationForm.stock_code)
  } catch (error) {
    console.error('获取方案列表失败:', error)
  } finally {
    loadingSchemes.value = false
  }
}

const openSaveSchemeDialog = () => {
  schemeForm.name = ''
  schemeForm.description = ''
  schemeForm.stock_code = aggregationForm.stock_code || ''
  schemeDialogVisible.value = true
}

const saveScheme = async () => {
  if (!schemeForm.name) {
    ElMessage.warning('请输入方案名称')
    return
  }
  
  const strategiesData = aggregationForm.strategy_names.map(name => ({
    name,
    weight: strategyWeightsMap[name] || 1.0,
    params: strategyParamsMap[name] || {}
  }))
  
  if (strategiesData.length === 0) {
    ElMessage.warning('请至少配置一个策略')
    return
  }

  try {
    await aggregationSchemesAPI.createScheme({
      name: schemeForm.name,
      description: schemeForm.description,
      stock_code: schemeForm.stock_code || undefined,
      strategies: strategiesData,
      buy_threshold: aggregationSettings.buy_threshold,
      sell_threshold: aggregationSettings.sell_threshold,
      required_strategies: aggregationSettings.required_strategies
    })
    ElMessage.success('方案保存成功')
    schemeDialogVisible.value = false
    // Refresh list just in case needed elsewhere, though usually on open
  } catch (error) {
    ElMessage.error('方案保存失败')
  }
}


const getMetricLabel = (val: string | null) => {
  if (!val) return '得分'
  const map: Record<string, string> = {
    'sharpe_ratio': '夏普比率',
    'cumulative_return': '累计收益',
    'sortino_ratio': '索提诺',
    'win_rate': '胜率',
  }
  return map[val] || val
}

// Important: Parameter names must match backend expectations
const defaultParams: Record<string, Record<string, number>> = {
  'MA Strategy': { short_period: 5, long_period: 20 },
  'RSI Strategy': { period: 14, overbought: 70, oversold: 30 },
  'MACD Strategy': { fast_period: 12, slow_period: 26, signal_period: 9 },
  'Bollinger Strategy': { period: 20, std_dev: 2 }, // Fixed: std_dev (matches backend)
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

const loadStrategyParams = async (strategyName: string) => {
  try {
    const info = await strategyAPI.getStrategyInfo(strategyName)
    
    // 1. Start with backend parameters if available
    const params: Record<string, any> = { ...(info.parameters || {}) }
    
    // 2. Ensure param descriptions are loaded
    let descs = info.parameter_descriptions || {}
    
    // 3. Fallback: If no params from backend, use hardcoded defaults
    if (Object.keys(params).length === 0 && defaultParams[strategyName]) {
       Object.assign(params, defaultParams[strategyName])
    }
    
    // 4. Ensure descriptions exist for all params
    Object.keys(params).forEach(key => {
        if (!descs[key]) {
            descs[key] = key // Use key as description if missing
        }
    })
    
    // 5. Fallback for descriptions from local list if still empty
    if (Object.keys(descs).length === 0) {
        const localStrategy = strategies.value.find(s => s.name === strategyName)
        if (localStrategy && localStrategy.parameter_descriptions) {
            descs = localStrategy.parameter_descriptions
        }
    }

    strategyParamDescsMap[strategyName] = descs
    strategyParamsMap[strategyName] = params
    strategyTypesMap[strategyName] = info.parameter_types || {}
  } catch (error) {
    console.error(`Failed to load params for ${strategyName}:`, error)
    // Even if API fails, try to use defaults so UI isn't empty
    if (defaultParams[strategyName]) {
        strategyParamsMap[strategyName] = { ...defaultParams[strategyName] }
        const fallbackDescs: Record<string, string> = {}
        Object.keys(defaultParams[strategyName]).forEach(k => fallbackDescs[k] = k)
        strategyParamDescsMap[strategyName] = fallbackDescs
    } else {
        strategyParamsMap[strategyName] = {}
        strategyParamDescsMap[strategyName] = {}
    }
  }
}

const handleStrategiesChange = async (value: string[]) => {
  // Initialize weights for new strategies
  value.forEach(name => {
    if (strategyWeightsMap[name] === undefined) {
      strategyWeightsMap[name] = 1.0
    }
    if (strategyParamsMap[name] === undefined) {
      // Sync inject defaults if available (Immediate UI update)
      if (defaultParams[name]) {
         strategyParamsMap[name] = { ...defaultParams[name] }
         const descs: Record<string, string> = {}
         Object.keys(defaultParams[name]).forEach(k => descs[k] = k)
         strategyParamDescsMap[name] = descs
      }
      
      // Async load (for custom strategies or to double check)
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

  // Set active tab to first selected strategy, prioritizing those with parameters
  if (value.length > 0 && !value.includes(activeStrategyTab.value)) {
    // Try to find a strategy that has default params defined (and is not empty)
    // This avoids showing an "Empty Parameters" tab (like Bearish Engulfing) by default
    const preferredWithParams = value.find(name => 
        defaultParams[name] && Object.keys(defaultParams[name]).length > 0
    )
    
    if (preferredWithParams) {
        activeStrategyTab.value = preferredWithParams
    } else {
        activeStrategyTab.value = value[0]
    }
  }

  // Remove from required strategies if deselected
  aggregationSettings.required_strategies = aggregationSettings.required_strategies.filter(s => value.includes(s))
}

const loadSavedParams = async (strategyName: string) => {
  if (!aggregationForm.stock_code) {
    ElMessage.warning('请先选择股票')
    return
  }
  loadingParamSets.value[strategyName] = true
  try {
    const res = await paramSetsAPI.getParamSets(aggregationForm.stock_code, strategyName)
    availableParamSets.value[strategyName] = res.param_sets
    if (res.param_sets.length === 0) {
      ElMessage.info('暂无该策略的优化参数记录')
    }
  } catch (e: any) {
    ElMessage.error('加载参数记录失败')
  } finally {
    loadingParamSets.value[strategyName] = false
  }
}

const applyParamSet = (strategyName: string, set: ParamSet) => {
  if (!strategyParamsMap[strategyName]) {
    strategyParamsMap[strategyName] = {}
  }
  Object.assign(strategyParamsMap[strategyName], set.params)
  ElMessage.success(`已应用参数: ${set.name}`)
}

const loadScheme = (scheme: AggregationScheme) => {
  // 1. Set strategies
  aggregationForm.strategy_names = scheme.strategies.map(s => s.name)
  
  // 2. Set weights and params
  scheme.strategies.forEach(s => {
    strategyWeightsMap[s.name] = s.weight
    strategyParamsMap[s.name] = s.params
  })
  
  // 3. Set thresholds
  aggregationSettings.buy_threshold = scheme.buy_threshold
  aggregationSettings.sell_threshold = scheme.sell_threshold
  aggregationSettings.required_strategies = scheme.required_strategies
  
  // 4. Ensure param descriptions are loaded for display
  scheme.strategies.forEach(s => {
    if (!strategyParamDescsMap[s.name]) {
      loadStrategyParams(s.name) 
      ensureStrategyInfo(s.name)
    }
  })
  
  ElMessage.success(`已加载方案: ${scheme.name}`)
}

const deleteScheme = async (id: number) => {
  try {
    await aggregationSchemesAPI.deleteScheme(id)
    ElMessage.success('删除成功')
    await fetchSchemes()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// Helper to load description without resetting params
const ensureStrategyInfo = async (strategyName: string) => {
    try {
        const info = await strategyAPI.getStrategyInfo(strategyName)
        strategyParamDescsMap[strategyName] = info.parameter_descriptions || {}
    } catch(e) { /* ignore */ }
}

const handleToggleAll = () => {
  if (aggregationForm.strategy_names.length === filteredStrategies.value.length && filteredStrategies.value.length > 0) {
    // Unselect all
    aggregationForm.strategy_names = []
  } else {
    // Select all filtered
    aggregationForm.strategy_names = filteredStrategies.value.map(s => s.name)
  }
  // Manually trigger change handler since programmatic update doesn't fire @change
  handleStrategiesChange(aggregationForm.strategy_names)
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
        color: s.final_signal === 1 ? '#4CAF50' : '#F44336',
        shape: s.final_signal === 1 ? 'arrowUp' : 'arrowDown',
        text: s.final_signal === 1 ? 'B' : 'S',
      }))

    ElMessage.success('分析完成')
  } catch (error: any) {
    console.error('Analysis error:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '分析失败')
  } finally {
    analyzing.value = false
  }
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



// 获取参数UI属性 (Min, Step, Precision)
const getParamProps = (key: string, strategyName: string) => {
  const types = strategyTypesMap[strategyName]
  const props: any = { step: 1, min: undefined, precision: undefined }
  
  // 1. 尝试使用后端提供的类型信息
  if (types && types[key]) {
      const typeStr = types[key]
      if (typeStr === 'float') {
          props.step = 0.01
          // float 不强制 precision，允许输入更多小数位
          props.precision = undefined 
      } else if (typeStr === 'int') {
          props.step = 1
          props.precision = 0
      }
      return props
  }

  // 2. 降级：基于参数名的启发式规则
  const lowerKey = key.toLowerCase()
  if (lowerKey.includes('dev') || lowerKey.includes('ratio') || lowerKey.includes('threshold') || lowerKey.includes('alpha') || lowerKey.includes('beta')) {
     props.step = 0.01
  } else if (lowerKey.includes('period') || lowerKey.includes('window')) {
     props.step = 1
     props.precision = 0
     props.min = 1
  }
  
  return props
}

// Initialize
onMounted(() => {
  loadStrategies()
  loadFavorites()
  
  // Set default date range (last 6 months) if not set
  if (!dateRange.value[0]) {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 6)
      dateRange.value = [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
  }
})

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
/* Toolbar Styles */
.header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.custom-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 220px;
  height: 32px;
  padding: 0 11px;
  background-color: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  cursor: pointer;
  transition: all 0.3s;
}

.custom-select:hover {
  border-color: var(--el-border-color-hover);
}

.custom-select.has-value {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.custom-select .placeholder {
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}

.custom-select .selected-text {
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.custom-select .count {
  color: var(--el-color-primary);
  font-weight: bold;
}

.stock-selector-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stock-price {
  font-family: monospace;
  font-weight: bold;
}
.stock-price.up { color: var(--el-color-success); }
.stock-price.down { color: var(--el-color-danger); }

.scheme-tag {
  font-size: 10px;
  background-color: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  padding: 1px 4px;
  border-radius: 2px;
  margin-left: 6px;
}

.delete-icon:hover {
  color: var(--el-color-danger) !important;
}

.el-dropdown-menu__item:hover .delete-icon {
  display: block; 
}
</style>
