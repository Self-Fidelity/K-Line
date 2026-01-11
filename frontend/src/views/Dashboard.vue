<template>
  <div class="dashboard">
    <h1>仪表盘</h1>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon stock-icon">
              <el-icon :size="40"><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">股票数量</div>
              <div class="stat-value">{{ stats.stockCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon strategy-icon">
              <el-icon :size="40"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">策略数量</div>
              <div class="stat-value">{{ stats.strategyCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon data-icon">
              <el-icon :size="40"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">数据记录</div>
              <div class="stat-value">{{ stats.dataRecordCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon update-icon">
              <el-icon :size="40"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">最后更新</div>
              <div class="stat-value">{{ stats.lastUpdate || '暂无' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作 -->
    <el-card class="quick-actions-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>快速操作</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-button type="primary" @click="goToDataManagement" style="width: 100%">
            <el-icon><DataLine /></el-icon>
            数据管理
          </el-button>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-button type="success" @click="goToStrategyAnalysis" style="width: 100%">
            <el-icon><TrendCharts /></el-icon>
            策略分析
          </el-button>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-button type="info" @click="goToChartView" style="width: 100%">
            <el-icon><Picture /></el-icon>
            K线图查看
          </el-button>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-button type="warning" @click="goToCompare" style="width: 100%">
            <el-icon><Operation /></el-icon>
            策略比较
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 欢迎信息 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>欢迎使用 K-Line 股票数据分析系统</span>
        </div>
      </template>
      <div class="welcome-content">
        <p>欢迎，{{ userInfo?.username || '用户' }}！</p>
        <p>系统已就绪，您可以开始使用以下功能：</p>
        <ul>
          <li>数据管理：获取和管理股票数据</li>
          <li>策略分析：使用各种技术指标分析股票</li>
          <li>K线图查看：可视化查看K线图表</li>
          <li>策略比较：对比多个策略的表现</li>
        </ul>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataLine, TrendCharts, Document, Clock, Picture, Operation } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { dataAPI } from '@/api/data'
import { strategyAPI } from '@/api/strategy'

const router = useRouter()
const authStore = useAuthStore()

const userInfo = computed(() => authStore.user)

const stats = ref({
  stockCount: 0,
  strategyCount: 0,
  dataRecordCount: 0,
  lastUpdate: '',
})

const loading = ref(false)

const loadStats = async () => {
  loading.value = true
  try {
    // 获取股票列表
    const stockListRes = await dataAPI.getStockList('main', false)
    stats.value.stockCount = stockListRes.total

    // 获取策略列表
    const strategyListRes = await strategyAPI.listStrategies()
    stats.value.strategyCount = strategyListRes.total

    // 数据记录数和最后更新时间暂时显示0，后续可以通过API获取
    stats.value.dataRecordCount = 0
    stats.value.lastUpdate = ''
  } catch (error: any) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

const goToDataManagement = () => {
  router.push('/data')
}

const goToStrategyAnalysis = () => {
  router.push('/strategy')
}

const goToChartView = () => {
  router.push('/chart')
}

const goToCompare = () => {
  router.push('/compare')
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.dashboard h1 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  height: 100%;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stock-icon {
  background-color: #e3f2fd;
  color: #2196f3;
}

.strategy-icon {
  background-color: #f3e5f5;
  color: #9c27b0;
}

.data-icon {
  background-color: #e8f5e9;
  color: #4caf50;
}

.update-icon {
  background-color: #fff3e0;
  color: #ff9800;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
}

.welcome-content {
  line-height: 1.8;
  color: #606266;
}

.welcome-content p {
  margin: 10px 0;
}

.welcome-content ul {
  margin: 10px 0;
  padding-left: 20px;
}

.welcome-content li {
  margin: 8px 0;
}
</style>
