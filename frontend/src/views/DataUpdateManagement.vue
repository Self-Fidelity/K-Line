<template>
  <div class="data-update-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据更新管理</span>
          <el-tag type="warning" v-if="!isAdmin">仅管理员可用</el-tag>
        </div>
      </template>

      <!-- 配置区域 -->
      <el-card class="config-card" shadow="never">
        <template #header>
          <div class="card-title">
            <el-icon><Setting /></el-icon>
            <span>自动更新配置</span>
          </div>
        </template>

        <el-form :model="config" label-width="180px" label-position="left">
          <!-- 日K线数据自动更新 -->
          <el-form-item label="日K线数据自动更新">
            <el-switch
              v-model="config.auto_update_enabled"
              @change="handleConfigChange"
            />
            <span class="form-tip">开启后将在指定时间自动更新所有股票的日K线数据</span>
          </el-form-item>

          <el-form-item
            v-if="config.auto_update_enabled"
            label="更新时间"
          >
            <el-time-picker
              v-model="dailyUpdateTime"
              format="HH:mm"
              value-format="HH:mm"
              @change="handleDailyTimeChange"
            />
            <span class="form-tip">交易日结束后执行（建议：15:30）</span>
          </el-form-item>

          <!-- 股票列表自动更新 -->
          <el-form-item label="股票列表自动更新">
            <el-switch
              v-model="config.stock_list_update_enabled"
              @change="handleConfigChange"
            />
            <span class="form-tip">开启后将在指定时间自动从API更新股票列表</span>
          </el-form-item>

          <el-form-item
            v-if="config.stock_list_update_enabled"
            label="更新时间"
          >
            <el-time-picker
              v-model="stockListUpdateTime"
              format="HH:mm"
              value-format="HH:mm"
              @change="handleStockListTimeChange"
            />
            <span class="form-tip">交易日开始前执行（建议：09:00）</span>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleSaveConfig" :loading="saving">
              保存配置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 调度器状态 -->
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
          <el-table-column label="下次执行时间" width="200">
            <template #default="{ row }">
              {{ row.next_run_time ? formatDateTime(row.next_run_time) : '未调度' }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无定时任务" :image-size="80" />
      </el-card>

      <!-- 手动更新区域 -->
      <el-card class="manual-update-card" shadow="never" style="margin-top: 20px">
        <template #header>
          <div class="card-title">
            <el-icon><Operation /></el-icon>
            <span>手动更新</span>
          </div>
        </template>

        <el-space direction="vertical" style="width: 100%">
          <el-alert
            title="手动更新会立即从 akshare API 获取最新数据，请谨慎使用"
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
  Setting,
  Clock,
  Refresh,
  Operation,
  List,
  DataLine,
  RefreshRight,
} from '@element-plus/icons-vue'
import { dataUpdateAPI, type DataUpdateConfig, type SchedulerStatus } from '@/api/dataUpdate'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const config = ref<DataUpdateConfig>({
  auto_update_enabled: false,
  daily_update_hour: 15,
  daily_update_minute: 30,
  stock_list_update_enabled: false,
  stock_list_update_hour: 9,
  stock_list_update_minute: 0,
})

const schedulerStatus = ref<SchedulerStatus>({
  running: false,
  jobs: [],
})

const selectedMarket = ref('all')
const saving = ref(false)
const updating = ref(false)

// 计算属性：日K线更新时间
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

// 计算属性：股票列表更新时间
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
    config.value = data
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

// 保存配置
const handleSaveConfig = async () => {
  saving.value = true
  try {
    const updated = await dataUpdateAPI.updateConfig(config.value)
    config.value = updated
    ElMessage.success('配置已保存')
    // 刷新调度器状态
    await loadSchedulerStatus()
  } catch (error: any) {
    console.error('保存配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存配置失败')
  } finally {
    saving.value = false
  }
}

// 配置变更处理
const handleConfigChange = () => {
  // 配置变更时自动保存
  handleSaveConfig()
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
  if (isAdmin.value) {
    await loadConfig()
    await loadSchedulerStatus()
    // 每30秒刷新一次调度器状态
    setInterval(loadSchedulerStatus, 30000)
  }
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
