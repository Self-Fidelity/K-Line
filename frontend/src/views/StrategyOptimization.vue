<template>
  <div class="strategy-optimization">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>策略参数优化</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px" class="optimize-form">
        <!-- 股票选择 -->
        <el-form-item label="选择股票" required>
          <el-autocomplete
            v-model="form.stock_code"
            :fetch-suggestions="searchStocks"
            placeholder="请输入股票代码或名称"
            style="width: 300px"
            @select="handleStockSelect"
          >
            <template #default="{ item }">
              <span class="stock-code">{{ item.code }}</span>
              <span class="stock-name">{{ item.name }}</span>
            </template>
          </el-autocomplete>
        </el-form-item>

        <!-- 时间范围 -->
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            style="width: 300px"
            @change="handleDateRangeChange"
          />
        </el-form-item>

        <!-- 策略选择 -->
        <el-form-item label="选择策略" required>
          <el-select
            v-model="form.strategy_name"
            placeholder="请选择策略"
            style="width: 300px"
            @change="handleStrategyChange"
          >
            <el-option
              v-for="strategy in strategies"
              :key="strategy.name"
              :label="strategy.name"
              :value="strategy.name"
            >
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span>{{ strategy.name }}</span>
                <span style="font-size: 12px; color: #999; margin-left: 10px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                  {{ strategy.description }}
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 优化目标 -->
        <el-form-item label="优化目标" required>
          <el-select v-model="form.target_metric" style="width: 300px">
            <el-option label="夏普比率 (Sharpe Ratio)" value="sharpe_ratio" />
            <el-option label="累计收益率 (Total Return)" value="cumulative_return" />
            <el-option label="索提诺比率 (Sortino Ratio)" value="sortino_ratio" />
            <el-option label="胜率 (Win Rate)" value="win_rate" />
          </el-select>
        </el-form-item>

        <!-- 算法参数 -->
        <el-form-item label="粒子数量">
          <el-input-number v-model="form.num_particles" :min="5" :max="100" />
          <div class="form-hint">粒子群算法中的粒子数量，越多搜索越全面但速度越慢</div>
        </el-form-item>

        <el-form-item label="迭代次数">
          <el-input-number v-model="form.max_iter" :min="5" :max="200" />
          <div class="form-hint">算法迭代次数，越多越可能找到全局最优</div>
        </el-form-item>

        <!-- 参数范围配置 -->
        <el-divider content-position="left">参数范围配置</el-divider>
        <div v-if="form.strategy_name && Object.keys(paramRanges).length > 0" class="param-ranges">
          <div v-for="(range, key) in paramRanges" :key="key" class="range-item">
            <div class="range-label">
              <span>{{ getParameterLabel(key) }}</span>
              <el-tooltip v-if="getParameterDescription(key)" :content="getParameterDescription(key)" placement="top">
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
            <div class="range-inputs">
              <el-input-number v-model="range[0]" size="small" placeholder="最小值" />
              <span class="separator">至</span>
              <el-input-number v-model="range[1]" size="small" placeholder="最大值" />
            </div>
          </div>
        </div>
        <div v-else-if="form.strategy_name" class="empty-params">
          该策略无需配置参数范围
        </div>
        <div v-else class="empty-params">
          请先选择策略
        </div>

        <el-form-item style="margin-top: 30px">
          <el-button type="primary" @click="handleOptimize" :loading="optimizing" :disabled="!canOptimize">
            <el-icon><VideoPlay /></el-icon> 开始优化
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 优化结果 -->
    <el-card v-if="result" style="margin-top: 20px" class="result-card">
      <template #header>
        <div class="card-header">
          <span>优化结果</span>
          <el-button type="success" @click="saveParams" :loading="saving">
            <el-icon><Check /></el-icon> 保存参数
          </el-button>
        </div>
      </template>

      <div class="result-content">
        <div class="score-display">
          <div class="label">最佳得分 ({{ getMetricLabel(form.target_metric) }})</div>
          <div class="value">{{ result.best_score.toFixed(4) }}</div>
        </div>

        <div class="best-params">
          <h3>最佳参数组合</h3>
          <div class="params-grid">
            <div v-for="(value, key) in result.best_params" :key="key" class="param-item">
              <span class="key">{{ getParameterLabel(key) }}:</span>
              <span class="val">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, Check, QuestionFilled } from '@element-plus/icons-vue'
import { strategyAPI, type StrategyInfo } from '@/api/strategy'
import { dataAPI } from '@/api/data'

const strategies = ref<StrategyInfo[]>([])
const strategyInfoMap = ref<Record<string, StrategyInfo>>({})
const optimizing = ref(false)
const saving = ref(false)
const result = ref<any>(null)

const form = reactive({
  stock_code: '',
  strategy_name: '',
  start_date: '',
  end_date: '',
  target_metric: 'sharpe_ratio',
  num_particles: 20,
  max_iter: 30,
})

const dateRange = ref<[string, string]>(['', ''])
const paramRanges = reactive<Record<string, number[]>>({})

// 日期快捷选项
const dateShortcuts = [
  { text: '最近1月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 1); return [start, end]; } },
  { text: '最近3月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 3); return [start, end]; } },
  { text: '最近半年', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 6); return [start, end]; } },
  { text: '最近一年', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 12); return [start, end]; } },
]

const handleDateRangeChange = (val: any) => {
  if (!val) {
    form.start_date = ''
    form.end_date = ''
  } else {
    form.start_date = val[0]
    form.end_date = val[1]
  }
}

const canOptimize = computed(() => {
  return form.stock_code && form.strategy_name && Object.keys(paramRanges).length > 0
})

// 加载策略列表
const loadStrategies = async () => {
  try {
    const response = await strategyAPI.listStrategies()
    strategies.value = response.strategies
  } catch (error: any) {
    ElMessage.error('加载策略列表失败')
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
}

const handleStrategyChange = async (strategyName: string) => {
  result.value = null
  // 清空现有范围
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
    for (const [key, desc] of Object.entries(info.parameter_descriptions)) {
      // 尝试解析默认值作为参考
      let defVal = 1
      if (typeof desc === 'string' && desc.includes('默认')) {
         const match = desc.match(/默认[:\s]*([0-9.]+)/)
         if (match) defVal = parseFloat(match[1])
      }

      // 设置默认范围：0.5x ~ 2.0x
      // 如果是整数参数，取整
      const minVal = Math.floor(defVal * 0.5) || 1
      const maxVal = Math.ceil(defVal * 2.0) || (defVal + 10)

      paramRanges[key] = [minVal, maxVal]
    }
  }
}

const handleOptimize = async () => {
  optimizing.value = true
  result.value = null
  try {
    const res = await strategyAPI.optimizeStrategy(
      form.stock_code,
      form.strategy_name,
      paramRanges,
      form.start_date || undefined,
      form.end_date || undefined,
      form.target_metric,
      'pso',
      form.num_particles,
      form.max_iter
    )
    result.value = res
    ElMessage.success('优化完成')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '优化失败')
  } finally {
    optimizing.value = false
  }
}

const saveParams = async () => {
  if (!result.value || !result.value.best_params) return
  saving.value = true
  try {
    await strategyAPI.saveParams(
      form.stock_code,
      form.strategy_name,
      result.value.best_params
    )
    ElMessage.success('参数保存成功')
  } catch (e: any) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// Helpers
const getParameterLabel = (key: string): string => {
  const info = strategyInfoMap.value[form.strategy_name]
  if (info?.parameter_descriptions?.[key]) {
    const desc = info.parameter_descriptions[key]
    if (typeof desc === 'object' && (desc as any).label) {
      return (desc as any).label
    }
  }

  const labelMap: Record<string, string> = {
    'short_period': '短期周期',
    'long_period': '长期周期',
    'period': '周期',
    'std_dev': '标准差倍数',
    'oversold': '超卖阈值',
    'overbought': '超买阈值',
  }
  return labelMap[key] || key
}

const getParameterDescription = (key: string): string => {
  const info = strategyInfoMap.value[form.strategy_name]
  if (info?.parameter_descriptions?.[key]) {
    const desc = info.parameter_descriptions[key]
    return typeof desc === 'string' ? desc : (desc as any).description || ''
  }
  return ''
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

onMounted(() => {
  loadStrategies()
})
</script>

<style scoped>
.strategy-optimization {
  max-width: 1000px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 4px;
}

.param-ranges {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

.range-item {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
}

html.dark .range-item {
  background: #2d2d2d;
}

.range-label {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #606266;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}

.separator {
  color: #909399;
}

.empty-params {
  color: #909399;
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 4px;
}

html.dark .empty-params {
  background: #2d2d2d;
}

.stock-code {
  font-weight: bold;
  margin-right: 8px;
}

.stock-name {
  color: #909399;
  font-size: 12px;
}

.result-content {
  text-align: center;
  padding: 20px;
}

.score-display {
  margin-bottom: 30px;
}

.score-display .label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.score-display .value {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
}

.best-params h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 15px;
}

.params-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
}

.param-item {
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  padding: 10px 20px;
  border-radius: 20px;
  color: #409eff;
}

.param-item .key {
  margin-right: 8px;
  font-weight: 500;
}

.param-item .val {
  font-weight: bold;
}
</style>
