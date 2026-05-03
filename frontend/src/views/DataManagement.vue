<template>
  <div class="data-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据管理</span>
          <el-button 
            v-if="isAdmin" 
            type="primary" 
            @click="handleRefresh" 
            :loading="refreshing"
          >
            <el-icon><Refresh /></el-icon>
            刷新股票列表（从API）
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-row :gutter="20" class="search-row">
        <el-col :xs="24" :sm="12" :md="8">
          <el-input
            v-model="searchKeyword"
            placeholder="输入股票代码或名称搜索"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button @click="handleSearch">搜索</el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select v-model="selectedMarket" placeholder="选择市场" @change="handleMarketChange">
            <el-option label="全部" value="all" />
            <el-option label="主板" value="main" />
            <el-option label="创业板" value="cyb" />
            <el-option label="科创板" value="kcb" />
          </el-select>
        </el-col>
      </el-row>

      <!-- 骨架屏加载态 -->
      <div v-if="loading" class="skeleton-table" style="margin-top:20px">
        <div v-for="i in 8" :key="i" class="skeleton-row">
          <el-skeleton :rows="1" animated :throttle="500" />
        </div>
      </div>

      <!-- 股票列表 -->
      <el-table
        v-if="!loading"
        :data="filteredStocks"
        stripe
        style="width: 100%; margin-top: 20px"
        :default-sort="{ prop: 'code', order: 'ascending' }"
      >
        <el-table-column prop="code" label="股票代码" width="120" sortable />
        <el-table-column prop="name" label="股票名称" min-width="150" />
        <el-table-column prop="market" label="市场" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.market === 'main'" type="primary">主板</el-tag>
            <el-tag v-else-if="row.market === 'cyb'" type="warning">创业板</el-tag>
            <el-tag v-else-if="row.market === 'kcb'" type="info">科创板</el-tag>
            <el-tag v-else>其他</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="latest_date" label="最新数据日期" width="130">
          <template #default="{ row }">
            <span v-if="row.latest_date">{{ row.latest_date }}</span>
            <span v-else style="color: #909399">暂无数据</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button 
                :type="favoritesMap[row.code] ? 'warning' : 'default'" 
                size="small" 
                circle
                :icon="favoritesMap[row.code] ? StarFilled : Star"
                @click="toggleFavorite(row)"
                :title="favoritesMap[row.code] ? '取消收藏' : '收藏'"
                style="margin-right: 8px;"
            />
            <el-button type="primary" size="small" @click="handleViewData(row)">
              查看数据
            </el-button>
            <el-button type="success" size="small" @click="handleFetchData(row)">
              获取数据
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="totalStocks"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 20px; justify-content: flex-end"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 数据获取对话框 -->
    <el-dialog
      v-model="fetchDialogVisible"
      :title="`获取 ${selectedStock?.code} - ${selectedStock?.name} 数据`"
      width="500px"
    >
      <p>将获取该股票的最新数据并保存到数据库。</p>
      <template #footer>
        <el-button @click="fetchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmFetch" :loading="fetching">
          确定获取
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Star, StarFilled } from '@element-plus/icons-vue'
import { dataAPI, type StockInfo } from '@/api/data'
import { watchlistAPI, type WatchlistItem } from '@/api/watchlist'
import { useAuthStore } from '@/stores/auth'
import { useStockDataStore } from '@/stores/stockData'

const router = useRouter()
const authStore = useAuthStore()
const stockDataStore = useStockDataStore()

const loading = ref(false)
const refreshing = ref(false)
const fetching = ref(false)

const stocks = ref<StockInfo[]>([])
const searchKeyword = ref('')
const selectedMarket = ref('main')
const currentPage = ref(1)
const pageSize = ref(50)

const fetchDialogVisible = ref(false)
const selectedStock = ref<StockInfo | null>(null)

// Watchlist Map for quick lookup
const favoritesMap = ref<Record<string, boolean>>({})

// Load Favorites
const loadFavorites = async () => {
    try {
        const list = await watchlistAPI.getWatchlist()
        const map: Record<string, boolean> = {}
        list.forEach((item: WatchlistItem) => {
            map[item.stock_code] = true
        })
        favoritesMap.value = map
    } catch (e) {
        console.error('Failed to load favorites', e)
    }
}

const toggleFavorite = async (stock: StockInfo) => {
    try {
        if (favoritesMap.value[stock.code]) {
            await watchlistAPI.removeFromWatchlist(stock.code)
            favoritesMap.value[stock.code] = false
            ElMessage.success(`已取消收藏 ${stock.name}`)
        } else {
            await watchlistAPI.addToWatchlist(stock.code)
            favoritesMap.value[stock.code] = true
            ElMessage.success(`已收藏 ${stock.name}`)
        }
    } catch (e: any) {
        ElMessage.error(e.response?.data?.detail || '操作失败')
    }
}


const totalStocks = computed(() => {
  // 计算过滤后的总数（考虑搜索和市场过滤）
  let result = stocks.value

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(
      (stock) =>
        stock.code.toLowerCase().includes(keyword) || stock.name.toLowerCase().includes(keyword)
    )
  }

  // 市场过滤
  if (selectedMarket.value && selectedMarket.value !== 'all') {
    result = result.filter((stock) => stock.market === selectedMarket.value)
  }

  return result.length
})

const filteredStocks = computed(() => {
  let result = stocks.value

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(
      (stock) =>
        stock.code.toLowerCase().includes(keyword) || stock.name.toLowerCase().includes(keyword)
    )
  }

  // 市场过滤
  if (selectedMarket.value && selectedMarket.value !== 'all') {
    result = result.filter((stock) => stock.market === selectedMarket.value)
  }

  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

// 检查是否是管理员
const isAdmin = computed(() => {
  return authStore.user?.role === 'admin'
})

const loadStockList = async () => {
  loading.value = true
  try {
    const result = await stockDataStore.getStockList(selectedMarket.value)
    stocks.value = result.stocks
    currentPage.value = 1
    if (result.total > 0) {
      ElMessage.success(`已加载 ${result.total} 只股票`)
    } else {
      ElMessage.warning('该市场分类下暂无股票数据')
    }
  } catch (error: any) {
    console.error('加载股票列表失败:', error)
    ElMessage.error(error?.message || '加载股票列表失败')
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  refreshing.value = true
  try {
    const result = await stockDataStore.refreshStockList(selectedMarket.value)
    stocks.value = result.stocks
    currentPage.value = 1
    ElMessage.success(`已从 API 刷新股票列表，共 ${result.total} 只股票`)
  } catch (error: any) {
    console.error('刷新股票列表失败:', error)
    ElMessage.error(error?.message || '刷新股票列表失败（需要管理员权限）')
  } finally {
    refreshing.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleMarketChange = () => {
  loadStockList()
}

const handleSizeChange = () => {
  currentPage.value = 1
}

const handlePageChange = () => {
  // 分页变化时的处理
}

const handleViewData = (stock: StockInfo) => {
  // 直接跳转到K线图查看页面
  router.push({
    path: '/chart',
    query: {
      stock: stock.code,
      name: stock.name,
    },
  })
}

const handleFetchData = (stock: StockInfo) => {
  selectedStock.value = stock
  fetchDialogVisible.value = true
}


const handleConfirmFetch = async () => {
  if (!selectedStock.value) return

  fetching.value = true
  try {
    const response = await dataAPI.fetchStockData(selectedStock.value.code)
    ElMessage.success(response.message || '数据获取成功')
    fetchDialogVisible.value = false
    // 刷新股票列表（更新最新数据日期）
    await loadStockList()
  } catch (error: any) {
    console.error('获取数据失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取数据失败')
  } finally {
    fetching.value = false
  }
}

const formatVolume = (volume: number): string => {
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  }
  return volume.toString()
}

onMounted(() => {
  loadStockList()
  loadFavorites()
})
</script>

<style scoped>
.data-management { padding: 0; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.search-row {
  margin-bottom: 20px;
  .el-select { width: 100%; }
}

.data-form { margin-bottom: 20px; }

/* 骨架屏 */
.skeleton-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 响应式表格 */
@media (max-width: 768px) {
  :deep(.el-table) {
    font-size: 12px;
  }
  .card-header {
    font-size: 14px;
  }
}
</style>
