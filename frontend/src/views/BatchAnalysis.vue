<template>
  <div class="batch-analysis">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>检测配置</span>
        </div>
      </template>

      <el-form :model="analysisForm" label-width="120px">
        <el-form-item label="选择策略" required>
          <el-select
            v-model="analysisForm.strategy_names"
            placeholder="请选择至少一个策略"
            style="width: 400px"
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
          <div class="form-hint">已选择 {{ analysisForm.strategy_names.length }} 个策略</div>
        </el-form-item>

        <el-form-item label="股票代码" required>
          <el-input
            v-model="stockCodesText"
            type="textarea"
            :rows="6"
            placeholder="请输入股票代码，每行一个，例如：&#10;000001&#10;000002&#10;600000"
            style="width: 400px"
          />
          <div class="form-hint">
            已输入 {{ stockCodeList.length }} 只股票
          </div>
        </el-form-item>

        <!-- 策略参数配置 -->
        <el-card v-if="analysisForm.strategy_names && analysisForm.strategy_names.length > 0" style="margin-top: 15px; width: 600px">
          <template #header>
            <div class="card-header">
              <span>策略参数配置</span>
            </div>
          </template>
          <el-tabs v-model="activeStrategyTab" type="border-card">
            <el-tab-pane
              v-for="strategyName in analysisForm.strategy_names"
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
        </el-card>

        <el-form-item>
          <el-button type="primary" @click="handleAnalyze" :loading="analyzing">
            <el-icon><Search /></el-icon>
            开始检测
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 检测结果 -->
    <el-card v-if="analysisResult" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>检测结果</span>
          <div>
            <el-tag type="info">总计: {{ analysisResult.total_count }}</el-tag>
            <el-tag type="success" style="margin-left: 10px">成功: {{ analysisResult.success_count }}</el-tag>
            <el-tag type="danger" style="margin-left: 10px">失败: {{ analysisResult.failed_count }}</el-tag>
            <el-tag type="warning" style="margin-left: 10px">有买点: {{ analysisResult.recommended_count }}</el-tag>
          </div>
        </div>
      </template>

      <!-- 有买点的股票 -->
      <el-card v-if="analysisResult.recommended_stocks && analysisResult.recommended_stocks.length > 0" style="margin-bottom: 20px">
        <template #header>
          <div class="card-header">
            <span style="color: #e6a23c; font-weight: bold">
              <el-icon><Star /></el-icon>
              有买点的股票 ({{ analysisResult.recommended_stocks.length }} 只)
            </span>
          </div>
        </template>
        <el-table
          :data="analysisResult.recommended_stocks"
          stripe
          border
          style="width: 100%"
        >
          <el-table-column prop="stock_code" label="股票代码" width="120" />
          <el-table-column prop="stock_name" label="股票名称" width="150" />
          <el-table-column label="买点信号" min-width="300">
            <template #default="{ row }">
              <div v-for="signal in row.strategy_signals" :key="signal.strategy_name" style="margin-bottom: 5px">
                <el-tag v-if="signal.has_buy_signal" type="success" style="margin-right: 5px">
                  {{ signal.strategy_name }}: 买入
                </el-tag>
                <el-tag v-else-if="signal.error" type="danger" style="margin-right: 5px">
                  {{ signal.strategy_name }}: 错误
                </el-tag>
                <span v-else style="color: #909399; margin-right: 10px">
                  {{ signal.strategy_name }}: 无信号
                </span>
                <span v-if="signal.latest_signal_date" style="font-size: 12px; color: #909399">
                  ({{ signal.latest_signal_date }})
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="handleViewChart(row.stock_code)">
                查看K线图
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 全部结果 -->
      <el-card>
        <template #header>
          <div class="card-header">
            <span>全部检测结果</span>
          </div>
        </template>
        <el-table
          :data="analysisResult.results"
          stripe
          border
          style="width: 100%"
        >
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="stock_code" label="股票代码" width="120" />
          <el-table-column prop="stock_name" label="股票名称" width="150" />
          <el-table-column prop="has_buy_signal" label="买点" width="80" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.has_buy_signal" type="success">有</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="策略信号" min-width="300">
            <template #default="{ row }">
              <div v-for="signal in row.strategy_signals" :key="signal.strategy_name" style="margin-bottom: 5px">
                <el-tag v-if="signal.has_buy_signal" type="success" style="margin-right: 5px">
                  {{ signal.strategy_name }}: 买入
                </el-tag>
                <el-tag v-else-if="signal.error" type="danger" style="margin-right: 5px">
                  {{ signal.strategy_name }}: {{ signal.error }}
                </el-tag>
                <span v-else style="color: #909399; margin-right: 10px">
                  {{ signal.strategy_name }}: 无信号
                </span>
                <span v-if="signal.latest_signal_date" style="font-size: 12px; color: #909399">
                  ({{ signal.latest_signal_date }})
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="error" label="错误信息" min-width="200" v-if="analysisResult.failed_count > 0">
            <template #default="{ row }">
              <span v-if="row.error" style="color: #f56c6c">{{ row.error }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.success"
                type="primary"
                link
                size="small"
                @click="handleViewChart(row.stock_code)"
              >
                查看K线图
              </el-button>
              <span v-else style="color: #909399">-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Star } from '@element-plus/icons-vue'
import { batchAnalysisAPI } from '@/api/batchAnalysis'
import { strategyAPI, type StrategyInfo } from '@/api/strategy'

const router = useRouter()

const analyzing = ref(false)
const strategies = ref<StrategyInfo[]>([])
const strategyInfoMap = ref<Record<string, StrategyInfo>>({})
const strategyParamsMap = reactive<Record<string, Record<string, any>>>({})
const activeStrategyTab = ref<string>('')
const analysisResult = ref<any>(null)

const analysisForm = reactive({
  strategy_names: [] as string[],
  stock_codes: [] as string[],
})

const stockCodesText = ref('')

// 默认参数配置
const defaultParams: Record<string, Record<string, number>> = {
  'MA Strategy': { short_period: 5, long_period: 20 },
  'RSI Strategy': { period: 14, overbought: 70, oversold: 30 },
  'MACD Strategy': { fast_period: 12, slow_period: 26, signal_period: 9 },
  'Bollinger Strategy': { period: 20, num_std: 2 },
  'Momentum Strategy': { period: 10 },
  'Bullish Engulfing Strategy': {},
  'Bearish Engulfing Strategy': {},
  'Hammer Strategy': {},
  'Hanging Man Strategy': {},
  'Doji Strategy': { doji_threshold: 0.1 },
  'Morning Star Strategy': {},
  'Evening Star Strategy': {},
  'Bullish Harami Strategy': {},
  'Bearish Harami Strategy': {},
}

// 股票代码列表（计算属性）
const stockCodeList = computed(() => {
  if (!stockCodesText.value) return []
  return stockCodesText.value
    .split('\n')
    .map((code) => code.trim())
    .filter((code) => code.length > 0)
})

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
          for (const [key, desc] of Object.entries(info.parameter_descriptions)) {
            const paramDesc = desc as any
            strategyParamsMap[strategyName][key] = paramDesc.default ?? 1
          }
        }

        // 设置第一个策略为活动标签
        if (!activeStrategyTab.value && strategyNames.length > 0) {
          activeStrategyTab.value = strategyNames[0]
        }
      } catch (error: any) {
        console.error(`加载策略 ${strategyName} 信息失败:`, error)
        ElMessage.error(`加载策略 ${strategyName} 信息失败`)
      }
    }
  }
}

// 执行批量检测
const handleAnalyze = async () => {
  if (analysisForm.strategy_names.length === 0) {
    ElMessage.warning('请至少选择一个策略')
    return
  }

  const codes = stockCodeList.value
  if (codes.length === 0) {
    ElMessage.warning('请输入至少一个股票代码')
    return
  }

  analyzing.value = true
  analysisResult.value = null

  try {
    // 构建策略参数
    const strategyParams: Record<string, Record<string, any>> = {}
    for (const strategyName of analysisForm.strategy_names) {
      if (strategyParamsMap[strategyName] && Object.keys(strategyParamsMap[strategyName]).length > 0) {
        strategyParams[strategyName] = { ...strategyParamsMap[strategyName] }
      }
    }

    const request = {
      stock_codes: codes,
      strategy_names: analysisForm.strategy_names,
      strategy_params: strategyParams,
    }

    const result = await batchAnalysisAPI.checkBuySignals(request)
    analysisResult.value = result

    ElMessage.success(
      `检测完成！成功: ${result.success_count}, 失败: ${result.failed_count}, 有买点: ${result.recommended_count}`
    )
  } catch (error: any) {
    console.error('批量检测失败:', error)
    ElMessage.error(error.response?.data?.detail || '批量检测失败')
  } finally {
    analyzing.value = false
  }
}

// 重置表单
const handleReset = () => {
  analysisForm.strategy_names = []
  stockCodesText.value = ''
  Object.keys(strategyParamsMap).forEach((key) => delete strategyParamsMap[key])
  Object.keys(strategyInfoMap.value).forEach((key) => delete strategyInfoMap.value[key])
  activeStrategyTab.value = ''
  analysisResult.value = null
}

// 查看K线图
const handleViewChart = (stockCode: string) => {
  router.push({
    path: '/chart',
    query: {
      stock: stockCode,
    },
  })
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
  const paramDesc = strategyInfo.parameter_descriptions[key] as any
  return paramDesc?.description || ''
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

onMounted(() => {
  loadStrategies()
})
</script>

<style scoped>
.batch-analysis {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.parameter-description {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}
</style>
