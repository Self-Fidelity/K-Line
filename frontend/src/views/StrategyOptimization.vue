<template>
  <div class="strategy-optimization">
    <!-- 三栏布局 -->
    <div class="optimization-container">
      <!-- 左侧：配置面板 -->
      <div class="config-section">
        <!-- 配置面板 -->
        <el-card class="config-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>优化配置</span>
            </div>
          </template>

          <el-form :model="form" label-width="100px" label-position="top">
            <!-- 股票选择（带收藏下拉） -->
            <el-form-item label="股票代码">
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
                  v-model="form.stock_code"
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
                  :disabled="!form.stock_code"
                  title="收藏当前股票"
                />
              </div>
            </el-form-item>

            <!-- 策略选择 -->
            <el-form-item label="策略">
              <el-select v-model="form.strategy_name" placeholder="选择策略" @change="handleStrategyChange">
                <el-option
                  v-for="s in strategies"
                  :key="s.name"
                  :label="s.name"
                  :value="s.name"
                >
                  <span>{{ s.name }}</span>
                  <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
                    {{ s.description }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>

            <!-- 日期范围（带快捷选项） -->
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :shortcuts="dateShortcuts"
                style="width: 100%"
              />
            </el-form-item>

            <!-- 优化目标 -->
            <el-form-item label="优化目标">
              <el-select v-model="form.target_metric">
                <el-option label="夏普比率" value="sharpe_ratio" />
                <el-option label="累计收益率" value="cumulative_return" />
                <el-option label="索提诺比率" value="sortino_ratio" />
                <el-option label="胜率" value="win_rate" />
              </el-select>
            </el-form-item>

            <!-- 算法参数 -->
            <el-form-item label="粒子数量">
              <el-input-number v-model="form.num_particles" :min="5" :max="50" style="width: 100%" />
            </el-form-item>

            <el-form-item label="迭代次数">
              <el-input-number v-model="form.max_iter" :min="5" :max="100" style="width: 100%" />
            </el-form-item>

            <el-divider content-position="left">参数范围</el-divider>

            <!-- 参数范围 -->
            <div v-if="Object.keys(paramRanges).length > 0" class="param-ranges">
              <div v-for="(range, key) in paramRanges" :key="key" class="param-range-item">
                <div class="label">{{ getParameterLabel(key) }}</div>
                <div class="range-inputs">
                  <el-input-number v-model="range[0]" size="small" :controls="false" />
                  <span>~</span>
                  <el-input-number v-model="range[1]" size="small" :controls="false" />
                </div>
              </div>
            </div>
            <div v-else-if="form.strategy_name" class="empty-params" style="text-align: center; color: var(--el-text-color-secondary); padding: 20px;">
              该策略无需额外参数配置
            </div>
            <el-empty v-else description="请先选择策略" :image-size="60" />

            <!-- 操作按钮 -->
            <el-form-item style="margin-top: 20px">
              <el-button type="primary" @click="handleOptimize" :loading="optimizing" :disabled="!canOptimize" block>
                <el-icon><VideoPlay /></el-icon>
                开始优化
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <!-- 中间：进度和结果 -->
      <div class="result-section">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>优化结果</span>
            </div>
          </template>

          <!-- 优化中 -->
          <div v-if="optimizing" class="optimizing-state">
            <div class="progress-header">
              <h3>正在优化参数...</h3>
              <div class="progress-meta">
                <span>{{ form.strategy_name }}</span>
                <span>•</span>
                <span>{{ form.target_metric }}</span>
              </div>
            </div>
            
            <div class="progress-bar-container">
              <el-progress 
                :percentage="optimizingProgress" 
                :stroke-width="24"
                :show-text="false"
              />
              <div class="progress-text">
                <span class="percentage">{{ optimizingProgress.toFixed(1) }}%</span>
                <span class="status">{{ optimizingStatusText }}</span>
              </div>
            </div>
            
            <div class="progress-stats" v-if="optimizingElapsedTime > 0">
              <div class="stat-item">
                <div class="stat-label">已用时间</div>
                <div class="stat-value">{{ formatElapsedTime(optimizingElapsedTime) }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">预计剩余</div>
                <div class="stat-value">{{ formatElapsedTime(optimizingEstimatedRemaining) }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">当前最佳</div>
                <div class="stat-value">{{ optimizingBestScore ? optimizingBestScore.toFixed(4) : '--' }}</div>
              </div>
            </div>

            <!-- 实时优化日志 -->
            <div class="optimization-logs" v-if="optimizingLogs.length > 0" style="margin-top: 20px;">
              <h4>优化日志</h4>
              <div class="logs-container" ref="realtimeLogsContainer" style="max-height: 200px; overflow-y: auto; background: var(--el-fill-color-light); padding: 10px; border-radius: 4px;">
                <div v-for="(log, index) in optimizingLogs" :key="index" class="log-line" style="font-family: monospace; font-size: 12px; line-height: 1.5;">
                  {{ log }}
                </div>
              </div>
            </div>
          </div>

          <!-- 未开始 -->
          <el-empty 
            v-else-if="!result" 
            description="配置参数后点击【开始优化】"
            :image-size="120"
          />

          <!-- 优化结果 -->
          <div v-else class="result-content" style="margin-top: 20px;">
            <div class="best-score">
              <div class="score-label">{{ getMetricLabel(form.target_metric) }}</div>
              <div class="score-value">{{ result.best_score.toFixed(4) }}</div>
              <div class="score-meta" v-if="result.iterations">
                {{ result.iterations }} 次迭代完成
              </div>
            </div>

            <el-divider />

            <!-- 收敛曲线 -->
            <div class="convergence-chart-section" v-if="result.convergence_curve && result.convergence_curve.length > 0">
              <h4>收敛过程</h4>
              <!-- Explicit relative positioning for chart container -->
              <div class="chart-wrapper" ref="chartContainer" style="height: 300px; width: 100%; position: relative;"></div>
            </div>
            


            <div class="best-params">
              <h4>最佳参数组合</h4>
              <div class="params-list">
                <div v-for="(value, key) in result.best_params" :key="key" class="param-chip">
                  <span class="key">{{ getParameterLabel(key) }}</span>
                  <span class="value">{{ value }}</span>
                </div>
              </div>
            </div>

            <div class="param-ranges-info">
              <h4>参数优化区间</h4>
              <div class="ranges-list">
                <div v-for="(range, key) in paramRanges" :key="key" class="range-info">
                  <span class="key">{{ getParameterLabel(key) }}:</span>
                  <span class="range">[{{ range[0] }}, {{ range[1] }}]</span>
                </div>
              </div>
            </div>

            <el-button type="success" @click="showSaveDialog" style="margin-top: 20px" block>
              <el-icon><Check /></el-icon>
              保存到参数库
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 右侧：参数库 -->
      <div class="library-section">
        <el-card class="library-card">
          <template #header>
            <div class="card-header">
              <el-icon><FolderOpened /></el-icon>
              <span>参数库</span>
              <el-button 
                v-if="form.stock_code && form.strategy_name"
                text 
                size="small" 
                @click="loadParamSets"
              >
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <!-- 参数集列表 -->
          <div v-if="paramSets.length > 0" class="param-sets-list">
            <div
              v-for="set in paramSets"
              :key="set.id"
              class="param-set-card"
              :class="{ 'is-default': set.is_default }"
              @click="loadParamSet(set)"
            >
              <div class="set-header">
                <span class="set-name">{{ set.name }}</span>
                <el-tag v-if="set.is_default" type="success" size="small">默认</el-tag>
              </div>
              
              <!-- 日期区间 -->
              <div class="set-date-range" v-if="set.date_range">
                <el-icon><Calendar /></el-icon>
                <span>{{ set.date_range }}</span>
              </div>
              
              <!-- 得分信息 -->
              <div class="set-score" v-if="set.best_score !== null && set.best_score !== undefined">
                <span class="label">{{ getMetricLabel(set.target_metric || '得分') }}:</span>
                <span class="value">{{ set.best_score.toFixed(4) }}</span>
              </div>
              
              <!-- 参数详情 -->
              <div class="set-params" v-if="set.params">
                <div class="params-title">参数:</div>
                <div class="params-content">
                  <span v-for="(value, key) in set.params" :key="key" class="param-tag">
                    {{ getParameterLabel(key) }}: {{ value }}
                  </span>
                </div>
              </div>
              
              <!-- 优化区间 -->
              <div class="set-ranges" v-if="set.param_ranges">
                <div class="ranges-title">优化区间:</div>
                <div class="ranges-content">
                  <span v-for="(range, key) in set.param_ranges" :key="key" class="range-tag">
                    {{ getParameterLabel(key) }}: [{{ range[0] }}, {{ range[1] }}]
                  </span>
                </div>
              </div>
              
              <!-- 创建时间 -->
              <div class="set-time">
                <el-icon><Clock /></el-icon>
                {{ formatDateTime(set.created_at) }}
              </div>
              
              <!-- 操作按钮 -->
              <div class="set-actions" @click.stop>
                <el-button 
                  text 
                  size="small" 
                  type="primary"
                  @click="setDefaultParamSet(set)"
                  v-if="!set.is_default"
                >
                  设为默认
                </el-button>
                <el-button 
                  text 
                  size="small" 
                  type="danger"
                  @click="deleteParamSet(set)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <el-empty 
            v-else 
            description="暂无保存的参数"
            :image-size="80"
          >
            <template #description>
              <p>{{ form.stock_code && form.strategy_name ? '暂无保存的参数' : '请先选择股票和策略' }}</p>
            </template>
          </el-empty>
        </el-card>
      </div>
    </div>

    <!-- 保存参数对话框 -->
    <el-dialog
      v-model="saveDialogVisible"
      title="保存参数集"
      width="500px"
    >
      <el-form :model="saveForm" label-width="100px">
        <el-form-item label="参数集名称" required>
          <el-input v-model="saveForm.name" placeholder="例如：最佳参数-2025-01-15" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="saveForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="描述该参数集的特点、适用场景等"
          />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="saveForm.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveParamSet" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { 
  createChart, 
  ColorType, 
  LineSeries
} from 'lightweight-charts'
import type { IChartApi } from 'lightweight-charts'
import { ref, reactive, computed, onMounted, watch, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Setting, VideoPlay, Check, DataAnalysis, Refresh, Calendar, Clock,
  Collection, Star, StarFilled
} from '@element-plus/icons-vue'
import { strategyAPI, type StrategyInfo } from '@/api/strategy'
import { dataAPI } from '@/api/data'
import { paramSetsAPI, type ParamSet } from '@/api/param-sets'
import { watchlistAPI, type WatchlistItem } from '@/api/watchlist'
import { useDark } from '@vueuse/core'

const isDark = useDark()

// 状态
const strategies = ref<StrategyInfo[]>([])
const strategyInfoMap = ref<Record<string, StrategyInfo>>({})
const optimizing = ref(false)
const optimizingProgress = ref(0)
const optimizingStatusText = ref('准备中...')
const optimizingElapsedTime = ref(0)
const optimizingEstimatedRemaining = ref(0)
const optimizingBestScore = ref<number | null>(null)
const optimizingStartTime = ref(0)
const optimizingTimer = ref<number | null>(null)
const result = ref<any>(null)
const paramSets = ref<ParamSet[]>([])
const saveDialogVisible = ref(false)
const saving = ref(false)
const optimizingLogs = ref<string[]>([])
const realtimeLogsContainer = ref<HTMLElement | null>(null)



// 表单
const form = reactive({
  stock_code: '',
  strategy_name: '',
  target_metric: 'sharpe_ratio',
  num_particles: 10,  // 默认10
  max_iter: 15,  // 默认15
})

const dateRange = ref<[string, string]>(['', ''])
const paramRanges = reactive<Record<string, number[]>>({})

// 日期快捷选项
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

// 收藏功能
const favorites = ref<WatchlistItem[]>([])
const isFavorite = computed(() => {
  if (!form.stock_code) return false
  return favorites.value.some(f => f.stock_code === form.stock_code)
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
  if (!form.stock_code) return
  try {
    if (isFavorite.value) {
      await watchlistAPI.removeFromWatchlist(form.stock_code)
      ElMessage.success('已取消收藏')
    } else {
      await watchlistAPI.addToWatchlist(form.stock_code)
      ElMessage.success('已收藏')
    }
    loadFavorites()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const handleFavoriteSelect = (fav: WatchlistItem) => {
  form.stock_code = fav.stock_code
}

const saveForm = reactive({
  name: '',
  description: '',
  is_default: false
})

// 计算属性
const canOptimize = computed(() => {
  return form.stock_code && form.strategy_name && Object.keys(paramRanges).length > 0
})

// 方法
const searchStocks = async (queryString: string, cb: (results: any[]) => void) => {
  if (!queryString) {
    cb([])
    return
  }
  try {
    const response = await dataAPI.getStockList('all')
    const results = response.stocks
      .filter(s => s.code.includes(queryString) || s.name.includes(queryString))
      .slice(0, 10)
      .map(s => ({ value: s.code, code: s.code, name: s.name }))
    cb(results)
  } catch (error) {
    cb([])
  }
}

const handleStockSelect = (item: any) => {
  form.stock_code = item.code
  if (form.strategy_name) {
    loadParamSets()
  }
}

const handleStrategyChange = async (strategyName: string) => {
  result.value = null
  Object.keys(paramRanges).forEach(k => delete paramRanges[k])

  if (!strategyInfoMap.value[strategyName]) {
    try {
      const info = await strategyAPI.getStrategyInfo(strategyName)
      strategyInfoMap.value[strategyName] = info
    } catch (e) {
      console.error(e)
      return
    }
  }

  const info = strategyInfoMap.value[strategyName]
  if (info && info.parameter_descriptions) {
    for (const [key] of Object.entries(info.parameter_descriptions)) {
      const defVal = info.parameters?.[key] || 1
      const minVal = Math.floor(defVal * 0.5) || 1
      const maxVal = Math.ceil(defVal * 2.0) || (defVal + 10)
      paramRanges[key] = [minVal, maxVal]
    }
  }

  if (form.stock_code) {
    loadParamSets()
  }
}

const handleOptimize = async () => {
  if (!dateRange.value || !dateRange.value[0] || !dateRange.value[1]) {
    ElMessage.warning('请选择日期范围')
    return
  }

  optimizing.value = true
  optimizingProgress.value = 0
  optimizingStatusText.value = '提交任务中...'
  optimizingElapsedTime.value = 0
  optimizingEstimatedRemaining.value = 0
  optimizingBestScore.value = null
  optimizingStartTime.value = Date.now()
  optimizingLogs.value = []
  result.value = null

  // UI timer for elapsed time
  if (optimizingTimer.value) clearInterval(optimizingTimer.value)
  optimizingTimer.value = window.setInterval(() => {
    const elapsed = (Date.now() - optimizingStartTime.value) / 1000
    optimizingElapsedTime.value = elapsed
  }, 1000)

  try {
    // 1. Submit task
    const res = await strategyAPI.optimizeStrategy({
      stock_code: form.stock_code,
      strategy_name: form.strategy_name,
      param_ranges: paramRanges,
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      target_metric: form.target_metric,
      method: 'pso',
      num_particles: form.num_particles,
      max_iter: form.max_iter
    })

    const taskId = res.task_id
    optimizingStatusText.value = '任务已提交，正在排队...'

    // 2. Poll for progress
    const pollInterval = window.setInterval(async () => {
      try {
        const progress = await strategyAPI.getOptimizationProgress(taskId)
        
        if (progress.status === 'running') {
          const current = progress.current_iteration
          const total = progress.total_iterations
          
          optimizingProgress.value = Math.min((current / total) * 100, 99)
          optimizingStatusText.value = `正在优化: 第 ${current} / ${total} 次迭代`
          optimizingBestScore.value = progress.best_score
          
          if (progress.estimated_time_remaining) {
            optimizingEstimatedRemaining.value = progress.estimated_time_remaining
          }
          
          if (progress.logs) {
            optimizingLogs.value = progress.logs
            nextTick(() => {
                if (realtimeLogsContainer.value) {
                    realtimeLogsContainer.value.scrollTop = realtimeLogsContainer.value.scrollHeight
                }
            })
          }
        } else if (progress.status === 'completed') {
           clearInterval(pollInterval)
           finishOptimization(progress.result)
        } else if (progress.status === 'failed') {
           clearInterval(pollInterval)
           throw new Error(progress.error || '优化失败')
        }
      } catch (err) {
        console.warn('Polling error (will retry):', err)
      }
    }, 1000)
    
    // Safety cleanup
    const checkCancel = window.setInterval(() => {
        if (!optimizing.value) {
            clearInterval(pollInterval)
            clearInterval(checkCancel)
        }
    }, 1000)

  } catch (e: any) {
    handleError(e)
  }
}

const finishOptimization = (res: any) => {
    if (optimizingTimer.value) {
      clearInterval(optimizingTimer.value)
      optimizingTimer.value = null
    }
    
    optimizingProgress.value = 100
    optimizingStatusText.value = '优化完成'
    
    setTimeout(() => {
      result.value = res
      ElMessage.success('优化完成')
      optimizing.value = false
      
      // Render chart if available
      if (res.convergence_curve) {
         nextTick(() => {
             renderConvergenceChart(res.convergence_curve)
         })
      }
    }, 500)
}

const handleError = (e: any) => {
    if (optimizingTimer.value) {
      clearInterval(optimizingTimer.value)
      optimizingTimer.value = null
    }
    optimizing.value = false
    ElMessage.error(e.message || e.response?.data?.detail || '优化失败')
}

const showSaveDialog = () => {
  const now = new Date()
  const dateStr = now.getFullYear() +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0') +
    String(now.getHours()).padStart(2, '0') +
    String(now.getMinutes()).padStart(2, '0')
  
  saveForm.name = dateStr
  saveForm.description = `使用${form.target_metric}优化，得分${result.value.best_score.toFixed(4)}`
  saveForm.is_default = false
  saveDialogVisible.value = true
}

const handleSaveParamSet = async () => {
  if (!saveForm.name) {
    ElMessage.warning('请输入参数集名称')
    return
  }

  saving.value = true
  try {
    await paramSetsAPI.createParamSet({
      stock_code: form.stock_code,
      strategy_name: form.strategy_name,
      name: saveForm.name,
      description: saveForm.description,
      params: result.value.best_params,
      param_ranges: paramRanges as Record<string, [number, number]>,
      target_metric: form.target_metric,
      best_score: result.value.best_score,
      optimization_method: 'pso',
      num_particles: form.num_particles,
      max_iter: form.max_iter,
      date_range: dateRange.value && dateRange.value[0] && dateRange.value[1] 
        ? `${new Date(dateRange.value[0]).toISOString().split('T')[0]} 至 ${new Date(dateRange.value[1]).toISOString().split('T')[0]}`
        : '',
      is_default: saveForm.is_default
    })
    
    ElMessage.success('保存成功')
    saveDialogVisible.value = false
    await loadParamSets()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const loadParamSets = async () => {
  if (!form.stock_code || !form.strategy_name) return
  
  try {
    const res = await paramSetsAPI.getParamSets(form.stock_code, form.strategy_name)
    paramSets.value = res.param_sets
  } catch (e: any) {
    console.error(e)
  }
}

const loadParamSet = (set: ParamSet) => {
  // 加载参数到配置
  if (set.param_ranges) {
    Object.keys(paramRanges).forEach(k => delete paramRanges[k])
    Object.assign(paramRanges, set.param_ranges)
  }
  
  ElMessage.success(`已加载参数集："${set.name}"`)
}

const setDefaultParamSet = async (set: ParamSet) => {
  try {
    await paramSetsAPI.setDefaultParamSet(set.id, form.stock_code, form.strategy_name)
    ElMessage.success('已设为默认')
    await loadParamSets()
  } catch (e: any) {
    ElMessage.error('设置失败')
  }
}

const deleteParamSet = async (set: ParamSet) => {
  try {
    await ElMessageBox.confirm(`确定删除参数集"${set.name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    await paramSetsAPI.deleteParamSet(set.id)
    ElMessage.success('删除成功')
    await loadParamSets()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getParameterLabel = (key: string): string => {
  const info = strategyInfoMap.value[form.strategy_name]
  if (info?.parameter_descriptions?.[key]) {
    return key
  }
  const labelMap: Record<string, string> = {
    'short_period': '短期周期',
    'long_period': '长期周期',
    'period': '周期',
  }
  return labelMap[key] || key
}

const getMetricLabel = (val: string) => {
  const map: Record<string, string> = {
    'sharpe_ratio': '夏普比率',
    'cumulative_return': '累计收益率',
    'sortino_ratio': '索提诺比率',
    'win_rate': '胜率',
  }
  return map[val] || val
}



const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}



// 格式化时间（秒）为 mm:ss 或 hh:mm:ss
const formatElapsedTime = (seconds: number) => {
  if (seconds < 0) return '00:00'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// Chart variables
let chart: IChartApi | null = null
const chartContainer = ref<HTMLElement | null>(null)

const renderConvergenceChart = (data: number[]) => {
    if (!chartContainer.value) return
    
    // Dispose old
    if (chart) {
        chart.remove()
        chart = null
    }

    // Create new
    chart = createChart(chartContainer.value, {
        width: chartContainer.value.clientWidth,
        height: 300,
        layout: {
            background: { type: ColorType.Solid, color: isDark.value ? '#1e1e1e' : '#ffffff' },
            textColor: isDark.value ? '#d1d5db' : '#333',
        },
        grid: {
            vertLines: { color: isDark.value ? '#2b2b2b' : '#f0f0f0' },
            horzLines: { color: isDark.value ? '#2b2b2b' : '#f0f0f0' },
        },
        timeScale: {
            visible: true,
            timeVisible: true,
            secondsVisible: false,
             tickMarkFormatter: (time: number) => {
               return String(time)
            },
        },
        localization: {
           timeFormatter: (time: number) => {
             return `迭代 ${time}` 
           } 
        }
    })
    
    const lineSeries = chart.addSeries(LineSeries, {
        color: '#2962FF',
        lineWidth: 2,
        title: '最佳适应度',
    })
    
    const chartData = data.map((val, idx) => ({
        time: (idx + 1) as any,
        value: val
    }))
    
    lineSeries.setData(chartData)
    chart.timeScale().fitContent()
    
    // Resize observer
    const resizeObserver = new ResizeObserver(entries => {
      if (entries.length === 0 || !entries[0].contentRect) return
      if (chart) {
        chart.applyOptions({ 
          width: entries[0].contentRect.width,
          height: entries[0].contentRect.height 
        })
      }
    })
    resizeObserver.observe(chartContainer.value)
    
    if ((window as any).__convergenceChartResizeObserver) {
        (window as any).__convergenceChartResizeObserver.disconnect()
    }
    ;(window as any).__convergenceChartResizeObserver = resizeObserver
}

// Watchers
watch(() => result.value, async (newResult) => {
  if (newResult && newResult.convergence_curve && newResult.convergence_curve.length > 0) {
     await nextTick()
     setTimeout(() => {
         renderConvergenceChart(newResult.convergence_curve)
     }, 50)
  }
}, { deep: true })

watch(isDark, () => {
  if (chart) {
    chart.applyOptions({
      layout: {
        background: { type: ColorType.Solid, color: isDark.value ? '#1e1e1e' : '#ffffff' },
        textColor: isDark.value ? '#d1d5db' : '#333',
      },
      grid: {
        vertLines: { color: isDark.value ? '#2b2b2b' : '#f0f0f0' },
        horzLines: { color: isDark.value ? '#2b2b2b' : '#f0f0f0' },
      },
    })
  }
})

onUnmounted(() => {
  if (chart) {
    chart.remove()
    chart = null
  }
   if ((window as any).__convergenceChartResizeObserver) {
    (window as any).__convergenceChartResizeObserver.disconnect()
    ;(window as any).__convergenceChartResizeObserver = null
  }
})

// 初始化
onMounted(async () => {
  try {
    const response = await strategyAPI.listStrategies()
    strategies.value = response.strategies
  } catch (error: any) {
    ElMessage.error('加载策略列表失败')
  }
  
  loadParamSets()
  loadFavorites()
  
  // 设置默认日期范围
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - 6)
  dateRange.value = [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
})
</script>

<style scoped lang="scss">
.strategy-optimization {
  height: 100%;
  padding: 0;
}

.optimization-container {
  display: flex;
  gap: 20px;
  height: 100%;
}

// 配置面板
.config-panel {
  width: 350px;
  flex-shrink: 0;
}

.config-card {
  height: 100%;
  overflow-y: auto;
  
  .stock-input-group {
    display: flex;
    align-items: center;
    width: 100%;
  }
}

// 中间结果区域
.result-section {
  flex: 1;
  min-width: 400px;
}

.result-card {
  height: 100%;
}

// 右侧参数库
.library-section {
  width: 300px;
  flex-shrink: 0;
}

.library-card {
  height: 100%;
  overflow-y: auto;
}

// 卡片头部
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  
  .el-icon {
    font-size: 18px;
  }
  
  span:last-child {
    margin-left: auto;
  }
}

// 参数范围配置
.param-ranges {
  .param-range-item {
    margin-bottom: 12px;
    
    .label {
      font-size: 13px;
      color: var(--el-text-color-regular);
      margin-bottom: 6px;
    }
    
    .range-inputs {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .el-input-number {
        flex: 1;
      }
      
      span {
        color: var(--el-text-color-secondary);
      }
    }
  }
}

// 优化中状态
.optimizing-state {
  padding: 40px 30px;
  
  .progress-header {
    text-align: center;
    margin-bottom: 30px;
    
    h3 {
      font-size: 20px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 10px 0;
    }
    
    .progress-meta {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      
      span:nth-child(2) {
        margin: 0 8px;
      }
    }
  }
  
  .progress-bar-container {
    margin-bottom: 30px;
    
    .progress-text {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;
      
      .percentage {
        font-size: 24px;
        font-weight: bold;
        color: var(--el-color-primary);
      }
      
      .status {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
  }
  
  .progress-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    
    .stat-item {
      background: var(--el-fill-color-light);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
      
      .stat-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-bottom: 8px;
      }
      
      .stat-value {
        font-size: 20px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }
  }
}

// 优化结果
.result-content {
  padding: 20px;
  
  .best-score {
    text-align: center;
    padding: 20px;
    background: var(--el-fill-color-light);
    border-radius: 8px;
    margin-bottom: 20px;
    
    .score-label {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin-bottom: 8px;
    }
    
    .score-value {
      font-size: 36px;
      font-weight: bold;
      color: var(--el-color-primary);
      margin-bottom: 8px;
    }
    
    .score-meta {
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }
  }
  
  // 收敛曲线
  .convergence-chart-section {
    margin-bottom: 20px;
    
    h4 {
      font-size: 14px;
      color: var(--el-text-color-primary);
      margin: 0 0 12px 0;
    }
    
    .chart-wrapper {
      background: var(--el-fill-color-light);
      border-radius: 8px;
      padding: 15px;
      
      .convergence-chart {
        width: 100%;
        height: 200px;
        display: block;
      }
    }
  }
  
  // 优化日志
  .optimization-logs {
    margin-bottom: 20px;
    
    h4 {
      font-size: 14px;
      color: var(--el-text-color-primary);
      margin: 0 0 12px 0;
    }
    
    .logs-container {
      background: #1e1e1e;
      color: #d4d4d4;
      border-radius: 8px;
      padding: 12px;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 12px;
      line-height: 1.6;
      max-height: 300px;
      overflow-y: auto;
      
      .log-line {
        padding: 2px 0;
        
        &:hover {
          background: rgba(255, 255, 255, 0.05);
        }
      }
      
      /* 滚动条样式 */
      &::-webkit-scrollbar {
        width: 8px;
      }
      
      &::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
      }
      
      &::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        
        &:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      }
    }
  }
  
  h4 {
    font-size: 14px;
    color: var(--el-text-color-primary);
    margin: 16px 0 12px;
  }
  
  .best-params {
    .params-list {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    
    .param-chip {
      background: var(--el-color-primary-light-9);
      border: 1px solid var(--el-color-primary-light-8);
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 13px;
      
      .key {
        color: var(--el-text-color-regular);
        margin-right: 4px;
      }
      
      .value {
        color: var(--el-color-primary);
        font-weight: 600;
      }
    }
  }
  
  .param-ranges-info {
    .ranges-list {
      font-size: 13px;
      
      .range-info {
        padding: 4px 0;
        display: flex;
        justify-content: space-between;
        
        .key {
          color: var(--el-text-color-regular);
        }
        
        .range {
          color: var(--el-text-color-secondary);
          font-family: monospace;
        }
      }
    }
  }
}

// 参数集列表
.param-sets-list {
  .param-set-card {
    background: var(--el-fill-color-light);
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      background: var(--el-fill-color);
      border-color: var(--el-color-primary-light-7);
      transform: translateY(-2px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    &.is-default {
      border-color: var(--el-color-success);
      background: var(--el-color-success-light-9);
    }
    
    .set-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      
      .set-name {
        font-weight: 600;
        font-size: 14px;
        color: var(--el-text-color-primary);
      }
    }
    
    .set-score {
      font-size: 13px;
      margin-bottom: 8px;
      
      .label {
        color: var(--el-text-color-secondary);
      }
      
      .value {
        color: var(--el-color-primary);
        font-weight: 600;
        margin-left: 4px;
      }
    }
    
    .set-date-range {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 4px;
      
      .el-icon {
        font-size: 14px;
      }
    }
    
    .set-params {
      margin-bottom: 6px;
      
      .params-title {
        font-size: 11px;
        color: var(--el-text-color-secondary);
        margin-bottom: 4px;
      }
      
      .params-content {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
      
      .param-tag {
        font-size: 11px;
        background: var(--el-color-info-light-9);
        padding: 2px 6px;
        border-radius: 4px;
        color: var(--el-text-color-regular);
      }
    }
    
    .set-ranges {
      margin-bottom: 6px;
      
      .ranges-title {
        font-size: 11px;
        color: var(--el-text-color-secondary);
        margin-bottom: 4px;
      }
      
      .ranges-content {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
      
      .range-tag {
        font-size: 11px;
        background: var(--el-fill-color);
        padding: 2px 6px;
        border-radius: 4px;
        color: var(--el-text-color-secondary);
        font-family: monospace;
      }
    }
    
    .set-time {
      font-size: 11px;
      color: var(--el-text-color-placeholder);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 4px;
      
      .el-icon {
        font-size: 12px;
      }
    }
    
    .set-actions {
      display: flex;
      gap: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--el-border-color-lighter);
    }
  }
}

// 股票、策略选项样式
.stock-code {
  font-weight: bold;
  margin-right: 8px;
}

.stock-name {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.strategy-option {
  display: flex;
  flex-direction: column;
  
  .desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
  }
}
</style>
