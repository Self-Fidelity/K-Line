<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="header-left">
        <h2>开发者控制台</h2>
        <p class="subtitle">K-Line Quant v1.0.0</p>
      </div>
      <div class="header-right">
        <el-tag type="success" effect="dark" round>System Online</el-tag>
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

            <h3>🛠️ 常用功能 (Features)</h3>
            <ul>
              <li><strong>策略参数调优</strong>：在单策略分析页，鼠标悬停在参数名旁可查看详细定义的物理含义。</li>
              <li><strong>图表交互</strong>：K线图支持滚轮缩放、拖拽平移；右上角工具栏可切换周期（日/周/月）。</li>
              <li><strong>我的收藏</strong>：在任意股票选择框旁点击星号⭐，可将该股加入收藏，方便快速访问。</li>
            </ul>

            <h3>📊 策略开发 (Dev Guide)</h3>
            <p>如需添加新策略，请在后端 <code>src/strategy/plugins/</code> 目录下新建 Python 文件，继承 <code>BaseStrategy</code> 类并实现 <code>analyze</code> 方法。系统会自动扫描并加载新策略。</p>
            <pre><code># Example: src/strategy/plugins/my_strategy.py
from src.strategy.base import BaseStrategy

class MyNewStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="My Strategy", 
            description="Simple moving average crossover",
            parameter_descriptions={"period": "MA period"}
        )
        self.period = 10
    
    def analyze(self, data, **kwargs):
        df = data.copy()
        # Implement your logic here
        df['signal'] = ... # 1: Buy, -1: Sell, 0: Hold
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
            <el-button type="primary" plain icon="Monitor" @click="router.push('/strategy/analysis')">策略回测</el-button>
            <el-button type="success" plain icon="Histogram" @click="router.push('/chart')">K线复盘</el-button>
            <el-button type="warning" plain icon="DataAnalysis" @click="router.push('/data/manage')">数据管理</el-button>
            <el-button type="info" plain icon="Setting" @click="router.push('/strategy/custom')">自定义策略</el-button>
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
            <div class="log-item">
              <span class="time">{{ currentTime }}</span>
              <span class="content">SQLite DB Path: data/database/kline.db</span>
            </div>
            <div class="log-item">
              <span class="time">{{ currentTime }}</span>
              <span class="content">System Online: All services running normally</span>
            </div>
            <div class="log-item">
              <span class="time">{{ currentTime }}</span>
              <span class="content">加载策略插件... {{ stats.strategyCount }} 个已加载</span>
            </div>
            <div class="log-item">
              <span class="time">{{ currentTime }}</span>
              <span class="content">数据库连接正常</span>
            </div>
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
  DataAnalysis, Setting 
} from '@element-plus/icons-vue'
import { dataAPI } from '@/api/data'
import { strategyAPI } from '@/api/strategy'
import { useNow, useDateFormat } from '@vueuse/core'

const router = useRouter()
const currentTime = useDateFormat(new Date(), 'HH:mm:ss') // Static time for logs
const lastUpdateTime = useDateFormat(new Date(), 'YYYY-MM-DD HH:mm')

const stats = ref({
  stockCount: 0,
  strategyCount: 0,
})

const loadStats = async () => {
  try {
    const stockListRes = await dataAPI.getStockList('main', false)
    stats.value.stockCount = stockListRes.total

    const strategyListRes = await strategyAPI.listStrategies()
    stats.value.strategyCount = strategyListRes.total
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStats()
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
