<template>
  <div class="data-update-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据更新管理</span>
          <el-tag type="warning" v-if="!isAdmin">仅管理员可修改配置</el-tag>
        </div>
      </template>

      <!-- 数据源配置 -->
      <el-card class="config-card" shadow="never">
        <template #header>
          <div class="card-title">
            <el-icon><DataLine /></el-icon>
            <span>数据源配置</span>
          </div>
        </template>

        <el-form :model="dataSourceConfig" label-width="200px" label-position="left">
          <el-form-item label="数据提供方">
            <el-radio-group
              v-model="dataSourceConfig.data_source"
              @change="handleDataSourceChange"
              :disabled="!isAdmin"
            >
              <el-radio-button label="akshare">
                <el-icon><Share /></el-icon> AkShare
              </el-radio-button>
              <el-radio-button label="tushare">
                <el-icon><Connection /></el-icon> Tushare Pro
              </el-radio-button>
            </el-radio-group>
            <span class="form-tip">切换数据源后，下次数据获取将使用新的数据源</span>
          </el-form-item>

          <el-form-item v-if="dataSourceConfig.data_source === 'tushare'" label="Tushare Token">
            <el-input
              v-model="tushareTokenInput"
              placeholder="请输入 Tushare Pro API Token"
              show-password
              style="width: 400px"
              :disabled="!isAdmin"
            />
            <el-button
              type="primary"
              :loading="testingTushare"
              :disabled="!isAdmin || !tushareTokenInput"
              @click="handleTestTushare"
              style="margin-left: 10px"
            >
              测试连接
            </el-button>
            <el-button
              type="success"
              :loading="savingToken"
              :disabled="!isAdmin"
              @click="handleSaveToken"
              style="margin-left: 10px"
            >
              保存 Token
            </el-button>
            <div class="form-tip">
              <el-link type="primary" href="https://tushare.pro/register" target="_blank">
                没有 Token？前往 Tushare 官网注册
              </el-link>
              <span style="margin-left: 8px; color: #909399">
                Token 仅保存在本地数据库，不会上传到 GitHub
              </span>
            </div>
          </el-form-item>

          <el-form-item v-if="dataSourceConfig.data_source === 'tushare'" label="Token 状态">
            <el-tag :type="dataSourceConfig.tushare_token ? 'success' : 'danger'">
              {{ dataSourceConfig.tushare_token ? '已配置' : '未配置' }}
            </el-tag>
            <span class="form-tip" v-if="!dataSourceConfig.tushare_token && isAdmin" style="color: #f56c6c">
              使用 Tushare 前必须先配置 Token
            </span>
          </el-form-item>

          <el-form-item label="当前数据源状态">
            <el-button
              size="small"
              :loading="testingCurrent"
              :disabled="!isAdmin"
              @click="handleTestCurrentSource"
            >
              测试当前数据源
            </el-button>
            <el-tag
              v-if="currentTestResult"
              :type="currentTestResult.success ? 'success' : 'danger'"
              style="margin-left: 10px"
            >
              {{ currentTestResult.message }}
            </el-tag>
          </el-form-item>

          <el-form-item label="数据清理">
            <el-popconfirm
              title="确定要清空该数据源的所有历史日K线数据吗？此操作不可恢复！"
              confirm-button-text="确定清空"
              cancel-button-text="取消"
              :disabled="!isAdmin"
              @confirm="handleClearData"
            >
              <template #reference>
                <el-button
                  type="danger"
                  size="small"
                  :disabled="!isAdmin"
                >
                  <el-icon><Delete /></el-icon>
                  清空 {{ dataSourceConfig.data_source === 'tushare' ? 'AkShare' : 'Tushare' }} 历史数据
                </el-button>
              </template>
            </el-popconfirm>
            <span class="form-tip">
              切换数据源后，旧数据仍保留在数据库中。如确认不再需要，可手动清空以释放空间。
            </span>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 日K线数据更新策略 -->
      <el-card class="config-card" shadow="never">
        <template #header>
          <div class="card-title">
            <el-icon><TrendCharts /></el-icon>
            <span>日K线数据更新策略</span>
          </div>
        </template>

        <el-form :model="config" label-width="200px" label-position="left">
          <el-form-item label="自动更新日K线数据">
            <el-switch
              v-model="config.auto_update_enabled"
              @change="handleSaveConfig"
              :disabled="!isAdmin"
            />
            <span class="form-tip">工作日自动从数据源拉取日K线数据</span>
          </el-form-item>

          <el-form-item v-if="config.auto_update_enabled" label="执行时间">
            <el-time-picker
              v-model="dailyUpdateTime"
              format="HH:mm"
              value-format="HH:mm"
              @change="handleDailyTimeChange"
              :disabled="!isAdmin"
              style="width: 140px"
            />
            <span class="form-tip">建议晚间 19:00 后，避开接口高峰</span>
          </el-form-item>

          <!-- 爬虫速度档位 -->
          <el-form-item v-if="config.auto_update_enabled" label="更新速度">
            <el-radio-group
              v-model="config.update_speed_preset"
              @change="handleSaveConfig"
              :disabled="!isAdmin"
            >
              <el-radio-button label="slow">
                <el-icon><Timer /></el-icon> 慢速
              </el-radio-button>
              <el-radio-button label="normal">
                <el-icon><Ship /></el-icon> 标准
              </el-radio-button>
              <el-radio-button label="fast">
                <el-icon><Lightning /></el-icon> 快速
              </el-radio-button>
            </el-radio-group>
            <div class="speed-info">
              <el-tag size="small" type="info">{{ speedDesc }}</el-tag>
              <el-tag size="small" type="warning" style="margin-left: 8px">
                全量预估: {{ estimatedDuration }}
              </el-tag>
            </div>
          </el-form-item>

          <!-- 批次休息 -->
          <el-form-item v-if="config.auto_update_enabled" label="批次休息设置">
            <div class="batch-config">
              <span>每</span>
              <el-input-number
                v-model="config.batch_size"
                :min="10"
                :max="500"
                :step="10"
                :disabled="!isAdmin"
                @change="handleSaveConfig"
                style="width: 100px; margin: 0 8px"
              />
              <span>只股票休息</span>
              <el-input-number
                v-model="config.batch_rest_seconds"
                :min="0"
                :max="300"
                :step="10"
                :disabled="!isAdmin"
                @change="handleSaveConfig"
                style="width: 100px; margin: 0 8px"
              />
              <span>秒</span>
            </div>
            <span class="form-tip">N100 小主机建议每 50 只休息 60 秒，防止过热降频</span>
          </el-form-item>

          <!-- 增量更新 -->
          <el-form-item v-if="config.auto_update_enabled" label="增量更新">
            <el-switch
              v-model="config.incremental_update"
              @change="handleSaveConfig"
              :disabled="!isAdmin"
            />
            <span class="form-tip">开启后跳过已有昨天数据的股票，大幅减少日常请求量</span>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 股票列表更新策略 -->
      <el-card class="config-card" shadow="never" style="margin-top: 20px">
        <template #header>
          <div class="card-title">
            <el-icon><List /></el-icon>
            <span>股票列表更新策略</span>
          </div>
        </template>

        <el-form :model="config" label-width="200px" label-position="left">
          <el-form-item label="自动更新股票列表">
            <el-switch
              v-model="config.stock_list_update_enabled"
              @change="handleSaveConfig"
              :disabled="!isAdmin"
            />
            <span class="form-tip">股票列表变化不频繁，建议开启即可</span>
          </el-form-item>

          <el-form-item v-if="config.stock_list_update_enabled" label="执行频率">
            <el-radio-group
              v-model="config.stock_list_update_frequency"
              @change="handleSaveConfig"
              :disabled="!isAdmin"
            >
              <el-radio-button label="weekly">每周一</el-radio-button>
              <el-radio-button label="daily">每天</el-radio-button>
            </el-radio-group>
            <span class="form-tip">推荐每周一，新股上市/退市信息一周内同步即可</span>
          </el-form-item>

          <el-form-item v-if="config.stock_list_update_enabled" label="执行时间">
            <el-time-picker
              v-model="stockListUpdateTime"
              format="HH:mm"
              value-format="HH:mm"
              @change="handleStockListTimeChange"
              :disabled="!isAdmin"
              style="width: 140px"
            />
          </el-form-item>

          <el-form-item v-if="config.stock_list_update_enabled" label="启动前随机等待">
            <el-slider
              v-model="config.pre_update_random_wait"
              :min="0"
              :max="120"
              :step="5"
              show-stops
              show-input
              :disabled="!isAdmin"
              @change="handleSaveConfig"
              style="width: 400px"
            />
            <span class="form-tip">{{ config.pre_update_random_wait }} 秒 — 避免固定时刻被识别为爬虫</span>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 定时任务状态 -->
      <el-card class="status-card" shadow="never" style="margin-top: 20px">
        <template #header>
          <div class="card-title">
            <el-icon><Clock /></el-icon>
            <span>定时任务状态</span>
            <el-button
              link
              size="small"
              @click="refreshSchedulerStatus"
              style="margin-left: 10px"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <div class="scheduler-info">
          <el-tag :type="schedulerStatus.running ? 'success' : 'info'">
            {{ schedulerStatus.running ? '运行中' : '已停止' }}
          </el-tag>
        </div>

        <el-table
          :data="schedulerStatus.jobs"
          style="margin-top: 15px"
          v-if="schedulerStatus.jobs.length > 0"
        >
          <el-table-column prop="id" label="任务ID" width="200" />
          <el-table-column prop="name" label="任务名称" />
          <el-table-column label="下次执行时间" width="220">
            <template #default="{ row }">
              {{ row.next_run_time ? formatDateTime(row.next_run_time) : '未调度' }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无定时任务" :image-size="80" />
      </el-card>

      <!-- 手动更新 -->
      <el-card class="manual-update-card" shadow="never" style="margin-top: 20px">
        <template #header>
          <div class="card-title">
            <el-icon><Operation /></el-icon>
            <span>手动更新</span>
          </div>
        </template>

        <el-space direction="vertical" style="width: 100%">
          <el-alert
            :title="`手动更新会立即从 ${config.data_source === 'tushare' ? 'Tushare' : 'akshare'} API 获取最新数据，当前爬虫策略配置同样生效`"
            type="warning"
            :closable="false"
            show-icon
          />

          <el-row :gutter="20">
            <el-col :span="8">
              <el-card shadow="hover" class="update-action-card">
                <div class="action-header">
                  <el-icon><List /></el-icon>
                  <span>更新股票列表</span>
                </div>
                <div class="action-desc">从API获取最新的股票列表</div>
                <el-button
                  type="primary"
                  @click="handleManualUpdate('stock_list')"
                  :loading="updating"
                  :disabled="!isAdmin"
                  style="margin-top: 10px"
                >
                  立即更新
                </el-button>
              </el-card>
            </el-col>

            <el-col :span="8">
              <el-card shadow="hover" class="update-action-card">
                <div class="action-header">
                  <el-icon><DataLine /></el-icon>
                  <span>更新日K线数据</span>
                </div>
                <div class="action-desc">更新指定市场或全部股票的日K线数据</div>
                <el-select
                  v-model="selectedMarket"
                  placeholder="选择市场"
                  style="width: 100%; margin-top: 10px"
                  :disabled="!isAdmin"
                >
                  <el-option label="全部" value="all" />
                  <el-option label="主板" value="main" />
                  <el-option label="创业板" value="cyb" />
                  <el-option label="科创板" value="kcb" />
                </el-select>
                <el-button
                  type="primary"
                  @click="handleManualUpdate('daily_data')"
                  :loading="updating"
                  :disabled="!isAdmin"
                  style="margin-top: 10px; width: 100%"
                >
                  立即更新
                </el-button>
              </el-card>
            </el-col>

            <el-col :span="8">
              <el-card shadow="hover" class="update-action-card">
                <div class="action-header">
                  <el-icon><RefreshRight /></el-icon>
                  <span>更新全部数据</span>
                </div>
                <div class="action-desc">更新股票列表和所有股票的日K线数据</div>
                <el-button
                  type="danger"
                  @click="handleManualUpdate('all')"
                  :loading="updating"
                  :disabled="!isAdmin"
                  style="margin-top: 10px; width: 100%"
                >
                  立即更新全部
                </el-button>
              </el-card>
            </el-col>
          </el-row>
        </el-space>
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  List,
  Clock,
  Refresh,
  Operation,
  DataLine,
  RefreshRight,
  Timer,
  Ship,
  Lightning,
  Share,
  Connection,
  Delete,
} from '@element-plus/icons-vue'
import { dataUpdateAPI, SPEED_PRESETS, estimateDuration, type DataUpdateConfig, type SchedulerStatus, type DataSourceConfig, type DataSourceTestResult } from '@/api/dataUpdate'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const config = ref<DataUpdateConfig>({
  auto_update_enabled: false,
  daily_update_hour: 19,
  daily_update_minute: 0,
  stock_list_update_enabled: false,
  stock_list_update_frequency: 'weekly',
  stock_list_update_hour: 6,
  stock_list_update_minute: 0,
  update_speed_preset: 'slow',
  batch_size: 50,
  batch_rest_seconds: 60,
  pre_update_random_wait: 20,
  incremental_update: true,
  data_source: 'akshare',
})

const dataSourceConfig = ref<DataSourceConfig>({
  data_source: 'akshare',
  tushare_token: '',
})

const tushareTokenInput = ref('')
const testingTushare = ref(false)
const savingToken = ref(false)
const testingCurrent = ref(false)
const currentTestResult = ref<DataSourceTestResult | null>(null)

const schedulerStatus = ref<SchedulerStatus>({
  running: false,
  jobs: [],
})

const selectedMarket = ref('all')
const updating = ref(false)
const saving = ref(false)

// 速度档位描述
const speedDesc = computed(() => {
  const preset = config.value.update_speed_preset
  const speed = SPEED_PRESETS[preset]
  return `${speed.label} — ${speed.desc}`
})

// 预估全量耗时
const estimatedDuration = computed(() => {
  return estimateDuration(
    config.value.update_speed_preset,
    config.value.batch_size,
    config.value.batch_rest_seconds,
  )
})

// 日K线更新时间计算属性
const dailyUpdateTime = computed({
  get: () => {
    const hour = String(config.value.daily_update_hour).padStart(2, '0')
    const minute = String(config.value.daily_update_minute).padStart(2, '0')
    return `${hour}:${minute}`
  },
  set: (val: string) => {
    if (val) {
      const [hour, minute] = val.split(':')
      config.value.daily_update_hour = parseInt(hour)
      config.value.daily_update_minute = parseInt(minute)
    }
  },
})

// 股票列表更新时间计算属性
const stockListUpdateTime = computed({
  get: () => {
    const hour = String(config.value.stock_list_update_hour).padStart(2, '0')
    const minute = String(config.value.stock_list_update_minute).padStart(2, '0')
    return `${hour}:${minute}`
  },
  set: (val: string) => {
    if (val) {
      const [hour, minute] = val.split(':')
      config.value.stock_list_update_hour = parseInt(hour)
      config.value.stock_list_update_minute = parseInt(minute)
    }
  },
})

// 加载配置
const loadConfig = async () => {
  try {
    const data = await dataUpdateAPI.getConfig()
    config.value = { ...config.value, ...data }
  } catch (error: any) {
    console.error('加载配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载配置失败')
  }
}

// 加载数据源配置
const loadDataSourceConfig = async () => {
  try {
    const data = await dataUpdateAPI.getDataSourceConfig()
    dataSourceConfig.value = { ...dataSourceConfig.value, ...data }
    tushareTokenInput.value = ''
  } catch (error: any) {
    console.error('加载数据源配置失败:', error)
  }
}

// 加载调度器状态
const loadSchedulerStatus = async () => {
  try {
    const data = await dataUpdateAPI.getSchedulerStatus()
    schedulerStatus.value = data
  } catch (error: any) {
    console.error('加载调度器状态失败:', error)
  }
}

const refreshSchedulerStatus = () => {
  loadSchedulerStatus()
}

// 保存配置（防抖：300ms 内多次变更只保存一次）
let saveTimer: ReturnType<typeof setTimeout> | null = null
const handleSaveConfig = () => {
  if (!isAdmin.value) return
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    saving.value = true
    try {
      const updated = await dataUpdateAPI.updateConfig(config.value)
      config.value = { ...config.value, ...updated }
      ElMessage.success('配置已保存并生效')
      await loadSchedulerStatus()
    } catch (error: any) {
      console.error('保存配置失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存配置失败')
    } finally {
      saving.value = false
    }
  }, 300)
}

const handleDailyTimeChange = () => {
  handleSaveConfig()
}

const handleStockListTimeChange = () => {
  handleSaveConfig()
}

// 数据源切换
const handleDataSourceChange = async () => {
  if (!isAdmin.value) return
  try {
    await dataUpdateAPI.updateConfig({ data_source: dataSourceConfig.value.data_source })
    config.value.data_source = dataSourceConfig.value.data_source
    ElMessage.success(`数据源已切换为 ${dataSourceConfig.value.data_source === 'tushare' ? 'Tushare' : 'AkShare'}`)
  } catch (error: any) {
    console.error('切换数据源失败:', error)
    ElMessage.error(error.response?.data?.detail || '切换数据源失败')
  }
}

// 测试 Tushare 连接
const handleTestTushare = async () => {
  if (!isAdmin.value || !tushareTokenInput.value) return
  testingTushare.value = true
  try {
    // 先临时保存 token 到后端（仅用于测试）
    await dataUpdateAPI.updateDataSourceConfig({
      data_source: 'tushare',
      tushare_token: tushareTokenInput.value,
    })
    const result = await dataUpdateAPI.testDataSource('tushare')
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error: any) {
    console.error('测试 Tushare 连接失败:', error)
    ElMessage.error(error.response?.data?.detail || '测试连接失败')
  } finally {
    testingTushare.value = false
  }
}

// 保存 Tushare Token
const handleSaveToken = async () => {
  if (!isAdmin.value) return
  savingToken.value = true
  try {
    await dataUpdateAPI.updateDataSourceConfig({
      data_source: 'tushare',
      tushare_token: tushareTokenInput.value,
    })
    await loadDataSourceConfig()
    ElMessage.success('Tushare Token 已保存')
  } catch (error: any) {
    console.error('保存 Token 失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存 Token 失败')
  } finally {
    savingToken.value = false
  }
}

// 测试当前数据源
const handleTestCurrentSource = async () => {
  if (!isAdmin.value) return
  testingCurrent.value = true
  currentTestResult.value = null
  try {
    const result = await dataUpdateAPI.testDataSource(config.value.data_source)
    currentTestResult.value = result
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error: any) {
    console.error('测试数据源失败:', error)
    ElMessage.error(error.response?.data?.detail || '测试失败')
  } finally {
    testingCurrent.value = false
  }
}

// 清空旧数据源数据
const handleClearData = async () => {
  if (!isAdmin.value) {
    ElMessage.warning('仅管理员可以执行此操作')
    return
  }

  const targetSource = dataSourceConfig.value.data_source === 'tushare' ? 'akshare' : 'tushare'
  try {
    const result = await dataUpdateAPI.clearDataBySource(targetSource)
    ElMessage.success(result.message || '数据清空成功')
  } catch (error: any) {
    console.error('清空数据失败:', error)
    ElMessage.error(error.response?.data?.detail || '清空数据失败')
  }
}

// 手动更新
const handleManualUpdate = async (updateType: 'stock_list' | 'daily_data' | 'all') => {
  if (!isAdmin.value) {
    ElMessage.warning('仅管理员可以执行此操作')
    return
  }

  updating.value = true
  try {
    const request: any = { update_type: updateType }
    if (updateType === 'daily_data') {
      request.market = selectedMarket.value
    }

    const result = await dataUpdateAPI.manualUpdate(request)
    ElMessage.success(result.message || '更新任务已启动')
  } catch (error: any) {
    console.error('手动更新失败:', error)
    ElMessage.error(error.response?.data?.detail || '手动更新失败')
  } finally {
    updating.value = false
  }
}

// 格式化日期时间
const formatDateTime = (dateTimeStr: string) => {
  if (!dateTimeStr) return '未设置'
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(async () => {
  await loadConfig()
  await loadDataSourceConfig()
  await loadSchedulerStatus()
  setInterval(loadSchedulerStatus, 30000)
})
</script>

<style scoped>
.data-update-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.config-card,
.status-card,
.manual-update-card {
  margin-bottom: 20px;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.speed-info {
  margin-top: 8px;
}

.batch-config {
  display: flex;
  align-items: center;
  gap: 4px;
}

.scheduler-info {
  margin-bottom: 10px;
}

.update-action-card {
  text-align: center;
  height: 100%;
}

.action-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 10px;
}

.action-desc {
  color: #909399;
  font-size: 12px;
  margin-bottom: 10px;
}
</style>
