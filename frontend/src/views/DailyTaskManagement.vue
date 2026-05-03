<template>
  <div class="daily-task-page">
    <!-- 状态横幅 -->
    <div class="status-banner" :class="bannerClass">
      <div class="banner-left">
        <el-icon :size="28">
          <Loading v-if="taskStatus?.is_running" class="is-loading" />
          <CircleCheckFilled v-else-if="lastSuccess" />
          <WarningFilled v-else-if="lastFailed" />
          <Clock v-else />
        </el-icon>
        <div>
          <h3>{{ bannerTitle }}</h3>
          <p>{{ bannerDesc }}</p>
        </div>
      </div>
      <div class="banner-right" v-if="!taskStatus?.is_running">
        <el-button type="primary" :icon="VideoPlay" :loading="triggering" @click="handleTrigger">
          立即执行
        </el-button>
      </div>
    </div>

    <!-- 运行中：实时进度 -->
    <el-card v-if="taskStatus?.is_running" class="progress-card">
      <template #header>
        <div class="card-header"><el-icon><Loading class="is-loading" /></el-icon><span>优化进行中…</span></div>
      </template>
      <div class="progress-section">
        <div class="progress-row">
          <span class="prog-label">股票进度</span>
          <el-progress
            :percentage="stockPercent"
            :stroke-width="16"
            :text-inside="true"
            :color="'#409eff'"
            style="flex:1"
          />
          <span class="prog-text">{{ taskStatus.progress.stock_index }}/{{ taskStatus.progress.stock_total }}</span>
        </div>
        <div class="progress-row">
          <span class="prog-label">当前股票</span>
          <span class="prog-value" style="font-weight:600;min-width:80px">{{ taskStatus.progress.stock_code || '-' }}</span>
        </div>
        <div class="progress-row">
          <span class="prog-label">策略进度</span>
          <el-progress
            :percentage="strategyPercent"
            :stroke-width="12"
            :text-inside="true"
            :color="'#67c23a'"
            style="flex:1"
          />
          <span class="prog-text">{{ taskStatus.progress.strategy_index }}/{{ taskStatus.progress.strategy_total }}</span>
        </div>
        <div class="progress-row">
          <span class="prog-label">当前策略</span>
          <span class="prog-value">{{ taskStatus.progress.strategy_name || '-' }}</span>
        </div>
        <div class="progress-row" style="color:var(--el-text-color-secondary);font-size:12px">
          <el-icon><Timer /></el-icon>
          <span>已运行 {{ fmtProgressElapsed }}</span>
        </div>
      </div>
    </el-card>

    <div class="page-grid">
      <!-- 左侧：配置 -->
      <el-card class="config-card">
        <template #header>
          <div class="card-header"><el-icon><Setting /></el-icon><span>任务配置</span></div>
        </template>
        <div class="config-item">
          <span class="label">定时执行</span>
          <span class="value">{{ fmtTime }}</span>
          <span class="hint">每日</span>
        </div>
        <div class="config-item">
          <span class="label">优化周期</span>
          <span class="value">6 个月</span>
          <span class="hint">回溯数据</span>
        </div>
        <div class="config-item">
          <span class="label">并行线程</span>
          <span class="value">3</span>
          <span class="hint">i5-8400</span>
        </div>
        <el-divider />
        <div class="config-item">
          <span class="label">邮件通知</span>
          <el-switch
            v-model="emailEnabled"
            :loading="emailToggling"
            @change="handleEmailToggle"
            inline-prompt
            active-text="开"
            inactive-text="关"
          />
        </div>
      </el-card>

      <!-- 右侧：上次运行 -->
      <el-card v-if="taskStatus?.last_run" class="result-card">
        <template #header>
          <div class="card-header"><el-icon><DataAnalysis /></el-icon><span>上次运行结果</span></div>
        </template>
        <div class="result-grid">
          <div class="result-item stock">
            <span class="num">{{ taskStatus.last_run.stocks_scanned }}</span>
            <span class="txt">扫描股票</span>
          </div>
          <div class="result-item signal" :class="{ active: (taskStatus.last_run.buy_signals || 0) > 0 }">
            <span class="num">{{ taskStatus.last_run.buy_signals || 0 }}</span>
            <span class="txt">买入信号</span>
          </div>
          <div class="result-item time">
            <span class="num">{{ fmtElapsed }}</span>
            <span class="txt">耗时</span>
          </div>
          <div class="result-item error" v-if="(taskStatus.last_run.errors || 0) > 0">
            <span class="num">{{ taskStatus.last_run.errors }}</span>
            <span class="txt">异常</span>
          </div>
        </div>

        <div v-if="taskStatus.last_buy_signals?.length" class="signals-section">
          <el-divider />
          <h4>📊 触发信号</h4>
          <div class="signal-list">
            <div v-for="(s, i) in taskStatus.last_buy_signals" :key="i" class="signal-item">
              <span class="sig-code">{{ s.stock_code }}</span>
              <span class="sig-name">{{ s.stock_name }}</span>
              <el-tag :type="s.score >= 0.7 ? 'success' : 'warning'" size="small" effect="dark">
                {{ (s.score * 100).toFixed(0) }}%
              </el-tag>
              <span class="sig-strategies">{{ (s.strategies || []).slice(0, 4).join(', ') }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <el-card v-else class="result-card">
        <template #header>
          <div class="card-header"><el-icon><DataAnalysis /></el-icon><span>运行结果</span></div>
        </template>
        <el-empty description="尚未执行过每日优化任务" :image-size="80" />
      </el-card>

      <!-- 运行历史 -->
      <el-card v-if="taskStatus?.run_history?.length" class="history-card">
        <template #header>
          <div class="card-header"><el-icon><Timer /></el-icon><span>运行历史 ({{ taskStatus.run_history.length }})</span></div>
        </template>
        <el-table :data="taskStatus.run_history" size="small" stripe>
          <el-table-column prop="time" label="时间" width="180">
            <template #default="{ row }">{{ row.time?.slice(0, 19)?.replace('T', ' ') }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="elapsed_seconds" label="耗时" width="80">
            <template #default="{ row }">{{ row.elapsed_seconds?.toFixed(0) }}s</template>
          </el-table-column>
          <el-table-column prop="stocks_scanned" label="股票" width="70" />
          <el-table-column prop="buy_signals" label="信号" width="70" />
          <el-table-column prop="error" label="错误信息" min-width="200">
            <template #default="{ row }">
              <span v-if="row.error" style="color:#f56c6c">{{ row.error }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 快捷链接 -->
      <el-card class="links-card">
        <template #header>
          <div class="card-header"><el-icon><Link /></el-icon><span>快捷操作</span></div>
        </template>
        <div class="links-grid">
          <el-button text type="primary" @click="$router.push('/strategy/aggregation')">
            策略聚合 → 加载最优参数
          </el-button>
          <el-button text type="success" @click="$router.push('/data/manage')">
            数据管理 → 更新行情
          </el-button>
          <el-button text type="warning" @click="$router.push('/strategy/analysis')">
            单策略分析 → 手动验证
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Loading, CircleCheckFilled, WarningFilled, Clock, VideoPlay,
  Setting, DataAnalysis, Timer, Link,
} from '@element-plus/icons-vue'
import { dailyTaskAPI, type DailyTaskStatus } from '@/api/dailyTask'

const taskStatus = ref<DailyTaskStatus | null>(null)
const triggering = ref(false)
const emailEnabled = ref(true)
const emailToggling = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

const bannerClass = computed(() => {
  if (taskStatus.value?.is_running) return 'running'
  if (taskStatus.value?.last_run?.status === 'success') return 'success'
  if (taskStatus.value?.last_run?.status === 'failed') return 'failed'
  return 'idle'
})

const lastSuccess = computed(() => taskStatus.value?.last_run?.status === 'success')
const lastFailed = computed(() => taskStatus.value?.last_run?.status === 'failed')

const bannerTitle = computed(() => {
  if (taskStatus.value?.is_running) return '任务执行中...'
  if (lastSuccess.value) return '上次运行成功'
  if (lastFailed.value) return '上次运行失败'
  return '等待首次运行'
})

const bannerDesc = computed(() => {
  if (taskStatus.value?.is_running) {
    const p = taskStatus.value.progress
    return `正在优化 ${p.stock_code || '...'} · ${p.strategy_name || ''}`
  }
  const lr = taskStatus.value?.last_run
  if (lr) return `${lr.time?.slice(0, 19)?.replace('T', ' ')} · 耗时 ${lr.elapsed_seconds?.toFixed(0)}s`
  return `定时 ${fmtTime.value} 每日自动执行`
})

const fmtTime = computed(() => {
  const h = taskStatus.value?.config?.hour ?? 15
  const m = taskStatus.value?.config?.minute ?? 30
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
})

const fmtElapsed = computed(() => {
  const s = taskStatus.value?.last_run?.elapsed_seconds ?? 0
  return s >= 60 ? `${(s / 60).toFixed(1)}min` : `${s.toFixed(0)}s`
})

const fmtProgressElapsed = computed(() => {
  const s = taskStatus.value?.progress?.elapsed ?? 0
  return s >= 60 ? `${(s / 60).toFixed(1)} min` : `${s.toFixed(0)}s`
})

const stockPercent = computed(() => {
  const p = taskStatus.value?.progress
  if (!p || p.stock_total === 0) return 0
  return Math.round((p.stock_index / p.stock_total) * 100)
})

const strategyPercent = computed(() => {
  const p = taskStatus.value?.progress
  if (!p || p.strategy_total === 0) return 0
  return Math.round((p.strategy_index / p.strategy_total) * 100)
})

const loadStatus = async () => {
  try {
    const data = await dailyTaskAPI.getStatus()
    taskStatus.value = data
    emailEnabled.value = data.email_enabled

    // 运行中则启动轮询
    if (data.is_running && !pollTimer) {
      pollTimer = setInterval(loadStatus, 1500)
    } else if (!data.is_running && pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  } catch { /* silent */ }
}

const handleTrigger = async () => {
  triggering.value = true
  try {
    await dailyTaskAPI.triggerRun()
    ElMessage.success('优化任务已启动')
    // 立即开始轮询
    setTimeout(loadStatus, 500)
  } catch (e: any) {
    ElMessage.error(e?.message || '触发失败')
  } finally { triggering.value = false }
}

const handleEmailToggle = async (val: boolean) => {
  emailToggling.value = true
  try {
    await dailyTaskAPI.toggleEmail(val)
    ElMessage.success(val ? '邮件通知已开启' : '邮件通知已关闭')
  } catch {
    emailEnabled.value = !val
  } finally { emailToggling.value = false }
}

onMounted(() => {
  loadStatus()
})

onUnmounted(() => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
})
</script>

<style scoped lang="scss">
.daily-task-page {
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-banner {
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;

  &.running { background: linear-gradient(135deg, #e6a23c, #d48806); }
  &.success { background: linear-gradient(135deg, #67c23a, #529b2e); }
  &.failed  { background: linear-gradient(135deg, #f56c6c, #c0392b); }
  &.idle    { background: linear-gradient(135deg, #909399, #63666e); }

  .banner-left { display: flex; align-items: center; gap: 14px;
    h3 { margin: 0; font-size: 18px; }
    p { margin: 4px 0 0; font-size: 13px; opacity: .85; }
  }
}

.page-grid {
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: auto auto;
  gap: 16px;

  .config-card  { grid-row: 1 / 3; }
  .result-card  { grid-column: 2; }
  .history-card { grid-column: 2; }
  .links-card   { grid-column: 1 / -1; }

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    .config-card, .result-card, .history-card, .links-card { grid-column: 1; grid-row: auto; }
  }
}

// ── 实时进度卡 ──
.progress-card {
  border: 1px solid var(--el-color-primary-light-5);
  .progress-section { display: flex; flex-direction: column; gap: 10px; }
  .progress-row { display: flex; align-items: center; gap: 10px; }
  .prog-label { width: 64px; font-size: 13px; color: var(--el-text-color-secondary); flex-shrink: 0; }
  .prog-value { font-size: 14px; }
  .prog-text { font-size: 13px; color: var(--el-text-color-secondary); white-space: nowrap; }
}

.config-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  .label { color: var(--el-text-color-secondary); width: 64px; font-size: 13px; }
  .value { font-weight: 600; font-size: 15px; }
  .hint { color: var(--el-text-color-placeholder); font-size: 12px; margin-left: 8px; }
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 12px;
}

.result-item {
  text-align: center; padding: 12px 8px; border-radius: 10px; background: var(--el-fill-color-light);
  &.signal.active { background: #fef0f0; }
  .num { font-size: 24px; font-weight: 700; display: block; }
  .txt { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 2px; }
}

.signals-section h4 { margin: 4px 0 8px; font-size: 14px; }

.signal-item {
  display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--el-border-color-lighter);
  .sig-code { font-weight: 600; width: 70px; }
  .sig-name { color: var(--el-text-color-secondary); font-size: 13px; flex: 1; }
  .sig-strategies { color: var(--el-text-color-placeholder); font-size: 12px; }
}

.card-header { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 15px; }

.links-grid { display: flex; flex-wrap: wrap; gap: 16px; }
</style>
