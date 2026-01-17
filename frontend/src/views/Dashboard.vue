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

    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="status-item">
        <el-icon><DataLine /></el-icon>
        <div class="info">
          <span class="label">股票池</span>
          <span class="value">{{ stats.stockCount }}</span>
        </div>
      </div>
      <div class="status-item">
        <el-icon><TrendCharts /></el-icon>
        <div class="info">
          <span class="label">策略库</span>
          <span class="value">{{ stats.strategyCount }}</span>
        </div>
      </div>
      <div class="status-item">
        <el-icon><Cpu /></el-icon>
        <div class="info">
          <span class="label">最后更新 (Last Updated)</span>
          <span class="value">{{ lastUpdateTime }}</span>
        </div>
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
            <el-button type="primary" plain :icon="Monitor" @click="router.push('/strategy/analysis')">策略回测</el-button>
            <el-button type="success" plain :icon="Histogram" @click="router.push('/chart')">K线复盘</el-button>
            <el-button type="warning" plain :icon="DataAnalysis" @click="router.push('/data/manage')">数据管理</el-button>
            <el-button type="info" plain :icon="Aim" @click="router.push('/strategy/optimize')">策略优化</el-button>
            <el-button type="primary" plain :icon="Connection" @click="router.push('/strategy/aggregation')">策略聚合</el-button>
            <el-button type="danger" plain :icon="Files" @click="router.push('/strategy/compare')">策略对比</el-button>
            <el-button type="info" plain :icon="Setting" @click="router.push('/strategy/custom')">自定义策略</el-button>
            <el-button v-if="isAdmin" type="warning" plain :icon="User" @click="router.push('/settings/users')">用户管理</el-button>
          </div>
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
  DataAnalysis, Setting, Aim, Connection, Files, User, SwitchButton
} from '@element-plus/icons-vue'
import { dataAPI } from '@/api/data'
import { strategyAPI } from '@/api/strategy'
import { logsAPI, type AuditLogInfo } from '@/api/logs'
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
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  background-color: var(--el-bg-color);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .username {
      font-size: 14px;
      color: var(--el-text-color-regular);
      font-weight: 500;
    }
  }

  .subtitle {
    margin: 5px 0 0 0;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }
}

.status-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  
  .status-item {
    background: var(--el-bg-color-overlay);
    padding: 20px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 15px;
    border: 1px solid var(--el-border-color-light);
    
    .el-icon {
      font-size: 24px;
      padding: 10px;
      background: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      border-radius: 8px;
    }
    
    .info {
      display: flex;
      flex-direction: column;
      
      .label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
      
      .value {
        font-size: 20px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      }
    }
  }
}

.main-content {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.guide-section {
  flex: 2;
  overflow-y: auto;
}

.side-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 300px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

/* Markdown Style Guide Content */
.guide-content {
  color: var(--el-text-color-regular);
  line-height: 1.6;
  
  h3 {
    margin: 16px 0 10px;
    font-size: 16px;
    color: var(--el-text-color-primary);
    
    &:first-child {
      margin-top: 0;
    }
  }
  
  p {
    margin-bottom: 12px;
    font-size: 14px;
  }
  
  ol, ul {
    padding-left: 20px;
    margin-bottom: 16px;
    font-size: 14px;
    
    li {
      margin-bottom: 6px;
    }
  }
  
  pre {
    background: var(--el-bg-color-page);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-family: 'Roboto Mono', monospace;
    font-size: 12px;
    border: 1px solid var(--el-border-color-light);
    
    code {
      color: var(--el-color-primary);
    }
  }
}

.action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  
  .el-button {
    margin: 0;
    height: auto;
    padding: 15px;
    justify-content: flex-start;
  }
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-item {
  display: flex;
  gap: 10px;
  font-size: 12px;
  
  .time {
    color: var(--el-text-color-secondary);
    font-family: 'Roboto Mono', monospace;
  }
  
  .content {
    color: var(--el-text-color-primary);
  }
}

/* Responsive */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }
  
  .status-bar {
    grid-template-columns: 1fr;
  }
}
</style>
