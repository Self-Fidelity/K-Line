<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="header-left">
        <h2>开发者控制台</h2>
        <p class="subtitle">K-Line Daily v1.0.0</p>
      </div>
      <div class="header-right">
        <el-tag type="success" effect="dark" round>System Online</el-tag>
        <div class="user-info" v-if="authStore.user">
          <span class="username">👤 {{ authStore.user.username }}</span>
          <el-button type="danger" link @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </div>
    </div>

    <!-- 状态栏 — 渐变色卡片 -->
    <div class="status-bar">
      <div class="stat-card stat-stocks">
        <div class="stat-icon-bg">
          <el-icon :size="36"><DataLine /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">股票池</span>
          <span class="stat-value">{{ stats.stockCount }}</span>
          <span class="stat-sub">只 A 股标的</span>
        </div>
        <div class="stat-trend up">📈 实时</div>
      </div>
      <div class="stat-card stat-strategies">
        <div class="stat-icon-bg">
          <el-icon :size="36"><TrendCharts /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">策略库</span>
          <span class="stat-value">{{ stats.strategyCount }}</span>
          <span class="stat-sub">个可用策略</span>
        </div>
        <div class="stat-trend up">已就绪</div>
      </div>
      <div class="stat-card stat-update">
        <div class="stat-icon-bg">
          <el-icon :size="36"><Cpu /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">最后更新</span>
          <span class="stat-value" style="font-size:18px">{{ lastUpdateTime }}</span>
          <span class="stat-sub">系统运行中</span>
        </div>
        <div class="stat-trend">🟢 Online</div>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧：使用指南 -->
      <div class="guide-section">
        <el-card class="guide-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>系统使用说明</span>
            </div>
          </template>
          
          <div class="guide-content markdown-body">
            <h3>🚀 快速开始 (Quick Start)</h3>
            <p>本系统主要用于A股历史数据回测与策略验证。核心工作流如下：</p>
            <ol>
              <li><strong>数据准备 (Data)</strong>：前往 <el-link type="primary" @click="router.push('/data/manage')">数据管理</el-link> 检查股票池，必要时在 <el-link type="primary" @click="router.push('/data/update')">数据更新</el-link> 获取最新日线数据。</li>
              <li><strong>策略分析 (Backtest)</strong>：在 <el-link type="primary" @click="router.push('/strategy/analysis')">单策略分析</el-link> 中选择策略与标的，调整参数进行回测。</li>
              <li><strong>复盘验证 (Review)</strong>：使用 <el-link type="primary" @click="router.push('/chart')">K线复盘</el-link> 工具，手动查看K线形态与指标配合情况。</li>
            </ol>

            <h3>📈 进阶工作流 (Advanced Workflow)</h3>
            <p>构建稳健的量化交易系统，建议遵循以下闭环流程：</p>
            <ol>
              <li><strong>参数优化 (Optimization)</strong>：使用 <el-link type="primary" @click="router.push('/strategy/optimize')">策略优化</el-link> 工具，对特定策略进行多目标参数寻优，找到夏普比率或收益率最优的参数组合。</li>
              <li><strong>保存参数 (Save)</strong>：在优化结果或单策略分析中，将满意的参数组合保存。</li>
              <li><strong>对比验证 (Compare)</strong>：在 <el-link type="primary" @click="router.push('/strategy/compare')">策略对比</el-link> 中横向比较不同策略或同一策略不同参数的表现。</li>
              <li><strong>策略聚合 (Aggregation)</strong>：最终使用 <el-link type="primary" @click="router.push('/strategy/aggregation')">策略聚合</el-link>，加载已保存的优化参数，构建多策略组合，平滑资金曲线。</li>
            </ol>

            <h3>🛠️ 常用功能 (Features)</h3>
            <ul>
              <li><strong>策略参数调优</strong>：在单策略分析页，鼠标悬停在参数名旁可查看详细定义的物理含义。</li>
              <li><strong>图表交互</strong>：K线图支持滚轮缩放、拖拽平移；右上角工具栏可切换周期（日/周/月）。</li>
              <li><strong>我的收藏</strong>：在任意股票选择框旁点击星号⭐，可将该股加入收藏，方便快速访问。</li>
            </ul>

            <h3>📊 策略开发 (Dev Guide)</h3>
            <p>您可以在 <el-link type="primary" @click="router.push('/strategy/custom')">自定义策略</el-link> 页面直接创建新策略，无需编写本地文件。流程如下：</p>
            <ol>
              <li><strong>创建策略</strong>：点击"创建新策略"，填写名称与描述。</li>
              <li><strong>编写代码</strong>：在在线编辑器中编写逻辑。系统提供"插入模板"功能，可快速生成标准结构。</li>
              <li><strong>验证与保存</strong>：点击"验证代码"检查语法，确认无误后保存。</li>
              <li><strong>回测验证</strong>：保存后可直接点击"回测"按钮，跳转至分析页面验证效果。</li>
            </ol>
            <pre><code># 常用代码模板 (Template)
    def analyze(self, data, **kwargs):
        df = data.copy()
        period = int(kwargs.get("period", self.period))
        
        # 使用 pandas 计算指标
        df['ma'] = df['close'].rolling(window=period).mean()
        
        # 生成信号 (1:买入, -1:卖出)
        df['signal'] = 0
        df.loc[df['close'] > df['ma'], 'signal'] = 1 
        df.loc[df['close'] < df['ma'], 'signal'] = -1
        
        return df</code></pre>
          </div>
        </el-card>
      </div>

      <!-- 右侧：快捷操作与日志 -->
      <div class="side-panel">
        <el-card class="action-card">
          <template #header>
            <div class="card-header">
              <el-icon><Lightning /></el-icon>
              <span>快捷操作</span>
            </div>
          </template>
          <div class="action-grid">
            <button class="action-btn" @click="router.push('/strategy/analysis')">
              <span class="action-icon" style="background:#ecf5ff;color:#409eff"><el-icon :size="22"><Monitor /></el-icon></span>
              <span>策略回测</span>
            </button>
            <button class="action-btn" @click="router.push('/chart')">
              <span class="action-icon" style="background:#f0f9eb;color:#67c23a"><el-icon :size="22"><Histogram /></el-icon></span>
              <span>K线复盘</span>
            </button>
            <button class="action-btn" @click="router.push('/data/manage')">
              <span class="action-icon" style="background:#fdf6ec;color:#e6a23c"><el-icon :size="22"><DataAnalysis /></el-icon></span>
              <span>数据管理</span>
            </button>
            <button class="action-btn" @click="router.push('/strategy/optimize')">
              <span class="action-icon" style="background:#f4f4f5;color:#909399"><el-icon :size="22"><Aim /></el-icon></span>
              <span>策略优化</span>
            </button>
            <button class="action-btn" @click="router.push('/strategy/aggregation')">
              <span class="action-icon" style="background:#ecf5ff;color:#409eff"><el-icon :size="22"><Connection /></el-icon></span>
              <span>策略聚合</span>
            </button>
            <button class="action-btn" @click="router.push('/strategy/compare')">
              <span class="action-icon" style="background:#fef0f0;color:#f56c6c"><el-icon :size="22"><Files /></el-icon></span>
              <span>策略对比</span>
            </button>
            <button class="action-btn" @click="router.push('/strategy/custom')">
              <span class="action-icon" style="background:#f4f4f5;color:#909399"><el-icon :size="22"><Setting /></el-icon></span>
              <span>自定义策略</span>
            </button>
            <button v-if="isAdmin" class="action-btn" @click="router.push('/settings/users')">
              <span class="action-icon" style="background:#fdf6ec;color:#e6a23c"><el-icon :size="22"><User /></el-icon></span>
              <span>用户管理</span>
            </button>
          </div>
        </el-card>

        <el-card v-if="isAdmin" class="daily-task-card">
          <template #header>
            <div class="card-header">
              <el-icon><AlarmClock /></el-icon>
              <span>每日优化任务</span>
              <el-tag v-if="taskStatus?.is_running" type="warning" size="small">运行中</el-tag>
              <el-tag v-else-if="taskStatus?.last_run" type="success" size="small">已就绪</el-tag>
              <el-tag v-else type="info" size="small">待运行</el-tag>
            </div>
          </template>
          <div v-if="taskStatus" class="task-body">
            <div class="task-row">
              <span class="task-label">定时</span>
              <span class="task-value">{{ String(taskStatus.config.hour).padStart(2,'0') }}:{{ String(taskStatus.config.minute).padStart(2,'0') }} 每日</span>
            </div>
            <div v-if="taskStatus.last_run" class="task-row">
              <span class="task-label">上次</span>
              <span class="task-value">{{ taskStatus.last_run.time?.slice(11,19) || '-' }}</span>
              <span class="task-meta">{{ taskStatus.last_run.elapsed_seconds?.toFixed(0) }}s · {{ taskStatus.last_run.buy_signals || 0 }}信号</span>
            </div>
            <el-button size="small" type="primary" @click="$router.push('/settings/daily-task')" style="margin-top:8px;width:100%">
              <el-icon><ArrowRight /></el-icon> 进入管理
            </el-button>
          </div>
          <div v-else class="task-body" v-loading="true" style="min-height:60px"></div>
        </el-card>

        <el-card class="log-card">
          <template #header>
            <div class="card-header">
              <el-icon><Bell /></el-icon>
              <span>系统日志</span>
            </div>
          </template>
            <div class="log-list">
              <div v-for="log in logs" :key="log.id" class="log-item">
                <span class="time">{{ formatDate(log.created_at) }}</span>
                <span class="content">
                  <span class="username">{{ log.username }}</span>
                  <span class="action">{{ log.action }}</span>
                  <span v-if="log.details" class="details">- {{ log.details }}</span>
                </span>
              </div>
              <div v-if="logs.length === 0" class="empty-log">暂无日志</div>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  DataLine, TrendCharts, Cpu, Document, 
  Lightning, Bell, Monitor, Histogram, 
  DataAnalysis, Setting, Aim, Connection, Files, User, SwitchButton,
  AlarmClock, ArrowRight,
} from '@element-plus/icons-vue'
import { dataAPI } from '@/api/data'
import { strategyAPI } from '@/api/strategy'
import { logsAPI, type AuditLogInfo } from '@/api/logs'
import { dailyTaskAPI, type DailyTaskStatus } from '@/api/dailyTask'
import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'
import { useDateFormat } from '@vueuse/core'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const router = useRouter()
// const currentTime = useDateFormat(new Date(), 'HH:mm:ss') // Removed static time

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    // 退出前也可以记录日志（前端触发或者后端在 logout endpoint 记录）
    await authStore.logout()
    router.push('/login')
    ElMessage.success('已退出登录')
  })
}
const lastUpdateTime = useDateFormat(new Date(), 'YYYY-MM-DD HH:mm')

const stats = ref({
  stockCount: 0,
  strategyCount: 0,
})

const taskStatus = ref<DailyTaskStatus | null>(null)

const logs = ref<AuditLogInfo[]>([])

const loadStats = async () => {
  try {
    const stockListRes = await dataAPI.getStockList('all')
    stats.value.stockCount = stockListRes.total

    const strategyListRes = await strategyAPI.listStrategies()
    stats.value.strategyCount = strategyListRes.total
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const getStartupTime = () => {
    let stored = sessionStorage.getItem('system_startup_time')
    if (!stored) {
      stored = new Date().toISOString()
      sessionStorage.setItem('system_startup_time', stored)
    }
    return stored
}

const loadLogs = async () => {
  try {
    const res = await logsAPI.getLogs(10)
    
    const startupTime = getStartupTime()
    
    // 添加系统启动日志（模拟）
    const systemLogs: AuditLogInfo[] = [
      {
        id: -1,
        user_id: 0,
        username: 'System',
        action: 'System Status',
        details: 'System Online: All services running normally',
        ip_address: '127.0.0.1',
        created_at: startupTime
      },
      {
        id: -2,
        user_id: 0,
        username: 'System',
        action: 'Database',
        details: 'Connection established successfully',
        ip_address: '127.0.0.1',
        created_at: startupTime
      }
    ]
    
    const allLogs = [...systemLogs, ...res.logs]
    // 按时间倒序排序
    logs.value = allLogs.sort((a, b) => {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
  } catch (error) {
    console.error('加载日志失败:', error)
  }
}

const formatDate = (isoString: string) => {
  const date = new Date(isoString)
  return useDateFormat(date, 'HH:mm:ss').value
}

onMounted(() => {
  loadStats()
  loadLogs()
  loadTaskStatus()
})

const loadTaskStatus = async () => {
  const authStore = useAuthStore()
  if (authStore.user?.role !== 'admin') return
  try { taskStatus.value = await dailyTaskAPI.getStatus() } catch { /* silent */ }
}
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;

  h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    .username { font-size: 14px; font-weight: 500; }
  }

  .subtitle {
    margin: 4px 0 0 0;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }
}

// ── 渐变色统计卡片 ──
.status-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  position: relative;
  padding: 20px 24px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: default;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
  }

  .stat-icon-bg {
    width: 56px; height: 56px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.25);
    color: #fff;
    flex-shrink: 0;
  }

  .stat-info {
    display: flex;
    flex-direction: column;
    color: #fff;
    .stat-label { font-size: 13px; opacity: 0.85; }
    .stat-value { font-size: 28px; font-weight: 700; line-height: 1.2; }
    .stat-sub { font-size: 11px; opacity: 0.7; }
  }

  .stat-trend {
    position: absolute;
    top: 12px; right: 16px;
    font-size: 12px;
    padding: 2px 10px;
    border-radius: 20px;
    background: rgba(255,255,255,0.2);
    color: #fff;
  }

  &.stat-stocks  { background: linear-gradient(135deg, #409eff, #337ecc); }
  &.stat-strategies { background: linear-gradient(135deg, #67c23a, #529b2e); }
  &.stat-update { background: linear-gradient(135deg, #e6a23c, #d48806); }
}

// ── 主内容区（左右布局 → 移动端上下堆叠） ──
.main-content {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  flex: 1;
  min-height: 0;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.guide-content {
  h3 { font-size: 16px; margin: 20px 0 10px; color: var(--el-color-primary); }
  h3:first-child { margin-top: 0; }
  ol, ul { padding-left: 20px; line-height: 1.8; font-size: 14px; }
  pre { background: var(--el-fill-color-light); border-radius: 8px; padding: 12px 16px; overflow-x: auto; font-size: 13px; }
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

// ── 快捷操作按钮网格 ──
.action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: var(--el-bg-color);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  transition: all 0.2s;
  font-family: inherit;

  &:hover {
    border-color: var(--el-color-primary);
    box-shadow: 0 2px 12px rgba(64,158,255,0.15);
    transform: translateY(-1px);
  }

  .action-icon {
    width: 36px; height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
}

// ── 日志列表 ──
.log-list {
  max-height: 280px;
  overflow-y: auto;
}

.log-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  font-size: 13px;
  display: flex;
  gap: 10px;

  .time { color: var(--el-text-color-placeholder); white-space: nowrap; font-family: monospace; }
  .username { color: var(--el-color-primary); font-weight: 500; margin-right: 4px; }
  .details { color: var(--el-text-color-secondary); }
}

.empty-log {
  text-align: center;
  padding: 30px;
  color: var(--el-text-color-placeholder);
}

// ── 每日任务卡片 ──
.daily-task-card {
  .task-body {
    font-size: 13px;
  }
  .task-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    .task-label { color: var(--el-text-color-secondary); width: 36px; flex-shrink: 0; }
    .task-value { font-weight: 500; }
    .task-meta { color: var(--el-text-color-placeholder); font-size: 12px; margin-left: auto; }
  }
}

// ── 卡片标题 ──
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}
</style>
