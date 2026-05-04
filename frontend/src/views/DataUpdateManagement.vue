<template>
  <div class="data-update-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据更新管理</span>
          <el-tag type="warning" v-if="!isAdmin">仅管理员可修改配置</el-tag>
        </div>
      </template>

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
            <span class="form-tip">工作日自动从 akshare 拉取日K线数据</span>
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
            title="手动更新会立即从 akshare API 获取最新数据，当前爬虫策略配置同样生效"
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
} from '@element-plus/icons-vue'
import { dataUpdateAPI, SPEED_PRESETS, estimateDuration, type DataUpdateConfig, type SchedulerStatus } from '@/api/dataUpdate'
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
})

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
