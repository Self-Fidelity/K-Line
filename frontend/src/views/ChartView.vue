<template>
  <div class="chart-view-container">
    <!-- 顶部控制栏 -->
    <el-card class="control-panel" :body-style="{ padding: '15px 20px' }">
      <el-form :inline="true" class="control-form">
        <el-form-item label="股票">
          <div style="display: flex; gap: 5px; align-items: center;">
         <el-dropdown trigger="click" @command="handleFavoriteSelect">
              <el-button :icon="Collection" circle title="我的收藏" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="favorites.length === 0" disabled>暂无收藏</el-dropdown-item>
              <el-dropdown-item 
                v-for="fav in favorites" 
                :key="fav.id" 
                :command="fav"
              >
                {{ fav.stock_code }} - {{ fav.stock_name || '未知' }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-autocomplete
          v-model="searchQuery"
          :fetch-suggestions="querySearch"
              placeholder="代码/名称"
              style="width: 180px"
          @select="handleSelect"
        >
          <template #default="{ item }">
                <span class="stock-code">{{ item.value }}</span>
                <span class="stock-name">{{ item.stock.name }}</span>
          </template>
        </el-autocomplete>

        <el-button 
            :type="isFavorite ? 'warning' : 'default'" 
            :icon="isFavorite ? StarFilled : Star" 
            circle 
            @click="toggleFavorite"
            :disabled="!currentStock"
            title="收藏当前股票"
        />
          </div>
        </el-form-item>

        <el-form-item label="时间">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          :shortcuts="shortcuts"
            style="width: 260px"
          @change="handleDateChange"
        />
        </el-form-item>

        <el-form-item label="主图">
          <div style="display: flex; gap: 8px; align-items: center;">
          <el-popover placement="bottom" trigger="click" width="200">
            <template #reference>
                <el-button size="small" :type="activeMainIndicator === 'MA' ? 'primary' : ''">MA</el-button>
            </template>
            <div class="checkbox-list">
              <el-checkbox v-model="maConfig.ma5" label="MA5" @change="updateLines" />
              <el-checkbox v-model="maConfig.ma10" label="MA10" @change="updateLines" />
              <el-checkbox v-model="maConfig.ma20" label="MA20" @change="updateLines" />
              <el-checkbox v-model="maConfig.ma30" label="MA30" @change="updateLines" />
              <el-checkbox v-model="maConfig.ma60" label="MA60" @change="updateLines" />
            </div>
          </el-popover>
          
          <el-tooltip content="清除主图指标" placement="top" :show-after="500">
             <el-button size="small" circle :icon="Close" @click="clearMainIndicator" />
          </el-tooltip>
        </div>
        </el-form-item>

        <el-form-item label="副图">
          <div style="display: flex; gap: 8px; align-items: center;">
        <el-radio-group v-model="selectedSubIndicator" size="small" @change="updateLines">
          <el-radio-button value="VOL">VOL</el-radio-button>
          <el-radio-button value="MACD">MACD</el-radio-button>
          <el-radio-button value="KDJ">KDJ</el-radio-button>
          <el-radio-button value="RSI">RSI</el-radio-button>
          <el-radio-button value="WR">WR</el-radio-button>
          <el-radio-button value="CCI">CCI</el-radio-button>
          <el-radio-button value="BIAS">BIAS</el-radio-button>
          <el-radio-button value="OBV">OBV</el-radio-button>
        </el-radio-group>
        <el-popover placement="bottom" trigger="hover" width="300">
          <template #reference>
            <el-icon class="help-icon"><QuestionFilled /></el-icon>
          </template>
          <div class="indicator-help">
            <div v-if="activeMainIndicator">
              <div class="title">{{ indicatorInfo[activeMainIndicator].name }}</div>
              <div class="desc">{{ indicatorInfo[activeMainIndicator].desc }}</div>
              <el-divider style="margin: 8px 0" />
            </div>
            <div class="title">{{ subIndicators[selectedSubIndicator].name }}</div>
            <div class="desc">{{ subIndicators[selectedSubIndicator].desc }}</div>
          </div>
        </el-popover>
      </div>
        </el-form-item>

        <el-form-item>
         <el-button type="primary" @click="fetchData" :loading="loading">
           <el-icon><Refresh /></el-icon> 刷新
         </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="main-content">
      <!-- Chart Area (Left) -->
      <div class="chart-wrapper" v-loading="loading">
        <div v-if="!currentStock" class="empty-state">
          <el-empty description="请选择或输入股票代码开始分析" />
        </div>
        <KlineChart 
          v-else
          :data="klineData" 
          :lines="lines"
          autosize
          :watermark="currentStock?.name"
          :dark-mode="isDark"
        />
      </div>

      <!-- Right Sidebar (Right) -->
      <div class="right-sidebar" v-if="currentStock">
          <!-- Chip Distribution Canvas -->
          <div class="chip-canvas-wrapper">
            <canvas ref="chipCanvas" class="chip-canvas"></canvas>
          </div>

          <!-- Statistics Panel (Bottom) -->
          <div class="stats-panel">

        <div class="stat-card">
          <h4>区间表现 <span class="period" style="font-weight: normal; font-size: 11px; margin-left: 8px;">{{ dateRange?.[0] }} ~ {{ dateRange?.[1] }}</span></h4>
          <div class="stat-grid">
            <div class="stat-item">
              <span class="label">区间涨跌幅</span>
              <span class="value" :class="getValueColor(stats.totalReturn)">
                {{ stats.totalReturn > 0 ? '+' : '' }}{{ stats.totalReturn }}%
              </span>
            </div>
            <div class="stat-item">
              <span class="label">最大回撤</span>
              <span class="value text-down">{{ stats.maxDrawdown }}%</span>
            </div>
            <div class="stat-item">
              <span class="label">起始价</span>
              <span class="value">{{ stats.startPrice }}</span>
            </div>
             <div class="stat-item">
              <span class="label">结束价</span>
              <span class="value">{{ stats.endPrice }}</span>
            </div>
            <div class="stat-item">
              <span class="label">最高价</span>
              <span class="value">{{ stats.maxPrice }}</span>
            </div>
            <div class="stat-item">
              <span class="label">最低价</span>
              <span class="value">{{ stats.minPrice }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Refresh, Close, QuestionFilled, Star, StarFilled, Collection } from '@element-plus/icons-vue';
import { useDark } from '@vueuse/core';
import { ElMessage } from 'element-plus';

// ... (imports)
import { type ChipDistributionData } from '@/plugins/ChipDistributionSeries';

// ... (other refs)


// ... (config)
// ... (config)
// Removed duplicate subIndicators definition


// ... (toggle function)







const chipData = ref<ChipDistributionData | null>(null);
const chipCanvas = ref<HTMLCanvasElement | null>(null);

import KlineChart, { type ChartData, type LineData } from '@/components/KlineChart.vue';
import { dataAPI, type StockInfo } from '@/api/data';
import { watchlistAPI, type WatchlistItem } from '@/api/watchlist';
import { calculateStatistics } from '@/utils/statistics';
import { 
    calculateMA, calculateMACD, calculateKDJ, calculateRSI,
    calculateWR, calculateCCI, calculateBIAS, calculateOBV 
} from '@/utils/indicators';

const route = useRoute();
const isDark = useDark();

// Indicator Metadata
const indicatorInfo: Record<string, { name: string, desc: string }> = {
  MA: { name: '移动平均线', desc: '将一定时期内的证券价格（指数）加以平均，并把不同时间的平均值连接起来，形成一根MA，用以观察证券价格变动趋势的一种技术指标。' },
};

const subIndicators: Record<string, { name: string, desc: string }> = {
  VOL: { name: '成交量 (Volume)', desc: '是指在某一时段内具体成交的总手数。成交量是一种供需的表现，指一个时间单位内对某项交易成交的数量。' },
  MACD: { name: '平滑异同移动平均线', desc: '利用收盘价的短期（常用为12日）指数移动平均线与长期（常用为26日）指数移动平均线之间的聚合与分离状况，对买进、卖出时机作出研判的技术指标。' },
  KDJ: { name: '随机指标', desc: '通过一个特定的周期内出现过的最高价、最低价及最后一个计算周期的收盘价及这三者之间的比例关系，来计算未成熟随机值RSV，然后计算K值、D值与J值。' },
  RSI: { name: '相对强弱指标', desc: '通过比较一段时期内的平均收盘涨数和平均收盘跌数来分析市场买沽盘的意向和实力，从而作出未来市场的走势。' },
  WR: { name: '威廉指标', desc: '主要用于辅助研判股价处于超买还是超卖状态。W%R 利用摆动点来度量市场的超买超卖现象。' },
  CCI: { name: '顺势指标', desc: '专门测量股价、外汇或者贵金属交易是否已超出常态分布范围。属于超买超卖类指标中较特殊的一种。' },
  BIAS: { name: '乖离率', desc: '测算股价在波动过程中与移动平均线出现偏离的程度，从而得出股价在剧烈波动时因偏离移动平均趋势而造成可能的回档或反弹。' },
  OBV: { name: '能量潮', desc: '通过统计成交量变动的趋势来推测股价趋势。将成交量值予以数量化，制成趋势线，配合股价趋势线，从价格的变动及成交量的增减关系，推测市场气氛。' },
  CYQ: { name: '筹码分布', desc: '筹码分布（CYQ）展示了市场中不同价格区间上的筹码堆积情况，帮助识别支撑位和压力位。' }
};

// State
const loading = ref(false);
const searchQuery = ref('');
const currentStock = ref<StockInfo | null>(null);
const dateRange = ref<[string, string]>(['', '']);
const klineData = ref<ChartData[]>([]);

// Watchlist
const favorites = ref<WatchlistItem[]>([]);
const isFavorite = computed(() => {
    if (!currentStock.value) return false;
    return favorites.value.some(f => f.stock_code === currentStock.value?.code);
});

// Indicator Selection
const activeMainIndicator = ref<string>('MA'); // 'MA' or ''
const selectedSubIndicator = ref<string>('VOL');

// Configs
const maConfig = reactive({ ma5: true, ma10: true, ma20: true, ma30: false, ma60: false });

// Chart Data
const lines = ref<LineData[]>([]);

// Statistics
const stats = computed(() => {
  const baseStats = calculateStatistics(klineData.value);
  let maxPrice = 0;
  let minPrice = 0;
  if (klineData.value.length > 0) {
     maxPrice = Math.max(...klineData.value.map(d => d.high));
     minPrice = Math.min(...klineData.value.map(d => d.low));
  }
  return { ...baseStats, maxPrice, minPrice };
});

// Date Shortcuts
const shortcuts = [
  { text: '最近1个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 1); return [start, end]; } },
  { text: '最近3个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 3); return [start, end]; } },
  { text: '最近6个月', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 6); return [start, end]; } },
  { text: '最近1年', value: () => { const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - 12); return [start, end]; } },
];

const getValueColor = (val: number) => {
  if (val > 0) return 'text-up';
  if (val < 0) return 'text-down';
  return '';
};

const querySearch = async (queryString: string, cb: any) => {
  if (!queryString) return cb([]);
  try {
    const res = await dataAPI.getStockList('all');
    const results = res.stocks
      .filter(s => s.code.includes(queryString) || s.name.includes(queryString))
      .slice(0, 10)
      .map(s => ({ value: s.code, stock: s }));
    cb(results);
  } catch (e) {
    console.error(e);
    cb([]);
  }
};

const handleSelect = (item: any) => {
  currentStock.value = item.stock;
  fetchData();
};

const handleDateChange = () => {
  if (currentStock.value) fetchData();
};

const clearMainIndicator = () => {
    activeMainIndicator.value = '';
    updateLines();
};

const updateLines = () => {
  const newLines: LineData[] = [];
  const data = klineData.value;
  if (data.length === 0) {
      lines.value = [];
      return;
  }

  // --- Main Chart Indicators ---
  if (activeMainIndicator.value === 'MA') {
      if (maConfig.ma5) newLines.push({ name: 'MA5', data: calculateMA(5, data), color: '#E91E63' });
      if (maConfig.ma10) newLines.push({ name: 'MA10', data: calculateMA(10, data), color: '#2196F3' });
      if (maConfig.ma20) newLines.push({ name: 'MA20', data: calculateMA(20, data), color: '#FF9800' });
      if (maConfig.ma30) newLines.push({ name: 'MA30', data: calculateMA(30, data), color: '#9C27B0' });
      if (maConfig.ma60) newLines.push({ name: 'MA60', data: calculateMA(60, data), color: '#009688' });
  }

  // --- Sub Chart Indicators ---
  const sub = selectedSubIndicator.value;
  
  if (sub === 'VOL') {
      // Create Volume histogram manually for sub chart
      const volData = data.map(d => ({
          time: d.time,
          value: d.volume || 0,
          color: (d.close >= d.open) ? 'rgba(239, 83, 80, 0.5)' : 'rgba(38, 166, 154, 0.5)'
      }));
      newLines.push({ name: 'VOL', data: volData, color: '', pane: 'sub', style: 'histogram' });
  } else if (sub === 'MACD') {
      const { dif, dea, macd } = calculateMACD(12, 26, 9, data);
      newLines.push(
          { name: 'DIF', data: dif, color: '#2196F3', pane: 'sub' },
          { name: 'DEA', data: dea, color: '#FF9800', pane: 'sub' },
          { name: 'MACD', data: macd, color: '', pane: 'sub', style: 'histogram' }
      );
  } else if (sub === 'KDJ') {
      const { k, d, j } = calculateKDJ(9, 3, 3, data);
      newLines.push(
          { name: 'K', data: k, color: '#E91E63', pane: 'sub' },
          { name: 'D', data: d, color: '#2196F3', pane: 'sub' },
          { name: 'J', data: j, color: '#FF9800', pane: 'sub' }
      );
  } else if (sub === 'RSI') {
      const rsi6 = calculateRSI(6, data);
      const rsi12 = calculateRSI(12, data);
      const rsi24 = calculateRSI(24, data);
      newLines.push(
          { name: 'RSI6', data: rsi6, color: '#E91E63', pane: 'sub' },
          { name: 'RSI12', data: rsi12, color: '#2196F3', pane: 'sub' },
          { name: 'RSI24', data: rsi24, color: '#FF9800', pane: 'sub' }
      );
  } else if (sub === 'WR') {
      const wr = calculateWR(14, data);
      newLines.push({ name: 'WR', data: wr, color: '#9C27B0', pane: 'sub' });
  } else if (sub === 'CCI') {
      const cci = calculateCCI(14, data);
      newLines.push({ name: 'CCI', data: cci, color: '#00BCD4', pane: 'sub' });
  } else if (sub === 'BIAS') {
      const bias6 = calculateBIAS(6, data);
      const bias12 = calculateBIAS(12, data);
      const bias24 = calculateBIAS(24, data);
      newLines.push(
          { name: 'BIAS6', data: bias6, color: '#E91E63', pane: 'sub' },
          { name: 'BIAS12', data: bias12, color: '#2196F3', pane: 'sub' },
          { name: 'BIAS24', data: bias24, color: '#FF9800', pane: 'sub' }
      );
  } else if (sub === 'OBV') {
      const obv = calculateOBV(data);
      newLines.push({ name: 'OBV', data: obv, color: '#FFC107', pane: 'sub' });
  }

  lines.value = newLines;
};

const fetchData = async () => {
  // Try to use searchQuery if currentStock is null or doesn't match
  let targetCode = currentStock.value?.code;
  
  if (searchQuery.value && (!currentStock.value || currentStock.value.code !== searchQuery.value)) {
      // Simple validation: 6 digits
      if (/^\d{6}$/.test(searchQuery.value)) {
          targetCode = searchQuery.value;
          currentStock.value = { code: targetCode, name: targetCode }; // Temporary name
      }
  }

  if (!targetCode) return;
  
  loading.value = true;
  try {
    const rawData = await dataAPI.getKlineData(
      targetCode, 
      dateRange.value?.[0], 
      dateRange.value?.[1]
    );
    
    klineData.value = rawData.map((item: any) => ({
      time: item.date,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
      volume: item.volume,
      pct_chg: item.pct_chg !== undefined && item.pct_chg !== null ? Number(item.pct_chg) : undefined
    }));
    
    updateLines();

  } catch (e) {
    console.error(e);
    ElMessage.error('获取数据失败，请检查股票代码是否正确');
  } finally {
    loading.value = false;
  }
};

// --- Watchlist Logic ---
const loadFavorites = async () => {
    try {
        const res = await watchlistAPI.getWatchlist();
        favorites.value = res;
    } catch (e) {
        console.error('加载收藏列表失败', e);
    }
};

const toggleFavorite = async () => {
    if (!currentStock.value) return;
    try {
        if (isFavorite.value) {
            await watchlistAPI.removeFromWatchlist(currentStock.value.code);
            ElMessage.success('已取消收藏');
        } else {
            await watchlistAPI.addToWatchlist(currentStock.value.code);
            ElMessage.success('已收藏');
        }
        loadFavorites(); // Reload to update state
    } catch (e: any) {
        ElMessage.error(e.response?.data?.detail || '操作失败');
    }
};

const handleFavoriteSelect = (fav: WatchlistItem) => {
    searchQuery.value = fav.stock_code;
    currentStock.value = { code: fav.stock_code, name: fav.stock_name || fav.stock_code }; 
    fetchData();
};

watch(() => [activeMainIndicator.value, selectedSubIndicator.value], () => {
    updateLines();
});

watch(() => maConfig, () => {
    if (activeMainIndicator.value === 'MA') {
        updateLines();
    }
}, { deep: true });

// Listen to popover button clicks to set active mode
watch(activeMainIndicator, () => {
    updateLines();
});


// --- Chip Distribution Logic ---
const activeCYQ = ref(true);

const loadCYQ = async () => {
    if (!currentStock.value) return;
    loading.value = true;
    try {
        console.log('[DEBUG] Loading CYQ for', currentStock.value.code);
        chipData.value = await dataAPI.getChipDistribution(currentStock.value.code);
    } catch (e) {
        console.error('Failed to load CYQ', e);
    } finally {
        loading.value = false;
    }
};



// Auto-load CYQ when stock changes
watch(() => currentStock.value, (newStock) => {
    if (newStock && activeCYQ.value) {
        loadCYQ();
    }
});

// Draw chip distribution on canvas
const drawChipDistribution = () => {
    if (!chipCanvas.value || !chipData.value) return;
    
    const canvas = chipCanvas.value;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set canvas size to match container
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    
    const { bins, chips, currentPrice } = chipData.value;
    if (bins.length === 0) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);
    
    // Find max chip for scaling
    const maxChip = Math.max(...chips);
    const canvasWidth = rect.width;
    const canvasHeight = rect.height;
    
    // Calculate bar dimensions
    const barMaxWidth = canvasWidth * 0.85; // Use 85% of canvas width
    const priceRange = Math.max(...bins) - Math.min(...bins);
    const pixelsPerPrice = canvasHeight / priceRange;
    
    // Draw each chip bar
    for (let i = 0; i < bins.length; i++) {
        const price = bins[i];
        const volume = chips[i];
        
        // Calculate Y position (price to pixel)
        const priceMin = Math.min(...bins);
        const y = canvasHeight - ((price - priceMin) * pixelsPerPrice);
        
        // Calculate bar height (more refined - smaller steps)
        const priceStep = bins[1] - bins[0];
        const barHeight = Math.max(pixelsPerPrice * priceStep, 1);
        
        // Calculate bar width based on volume
        const barWidth = (volume / maxChip) * barMaxWidth;
        
        // Color based on profit/loss
        const isProfit = price < currentPrice;
        ctx.fillStyle = isProfit 
            ? 'rgba(239, 83, 80, 0.7)'  // Red for loss (chips below current price)
            : 'rgba(76, 175, 80, 0.7)'; // Green for profit (chips above current price)
        
        // Draw horizontal bar from left
        ctx.fillRect(0, y - barHeight/2, barWidth, barHeight);
    }
    
    // Draw current price line
    const priceMin = Math.min(...bins);
    const currentY = canvasHeight - ((currentPrice - priceMin) * pixelsPerPrice);
    ctx.strokeStyle = '#FFC107';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(0, currentY);
    ctx.lineTo(canvasWidth, currentY);
    ctx.stroke();
    ctx.setLineDash([]);
};

// Watch chipData and redraw
watch(chipData, () => {
    if (chipData.value) {
        // Use nextTick to ensure canvas is rendered
        setTimeout(() => drawChipDistribution(), 100);
    }
}, { deep: true });

// Redraw on window resize
const handleResize = () => {
    if (chipData.value) {
        drawChipDistribution();
    }
};

window.addEventListener('resize', handleResize);


onMounted(() => {
    const end = new Date();
    const start = new Date();
    start.setMonth(start.getMonth() - 6);
    dateRange.value = [
        start.toISOString().split('T')[0],
        end.toISOString().split('T')[0]
    ];
    
    loadFavorites();

    const { stock, name } = route.query;
    if (stock) {
        currentStock.value = { code: stock as string, name: name as string || 'Unknown' };
        searchQuery.value = stock as string;
        fetchData();
        // CYQ will be loaded by watch
    }
});
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as v;

.chart-view-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: v.$bg-primary;
  color: v.$text-primary;
}

.control-panel {
  flex-shrink: 0;
}

.control-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.control-form :deep(.el-form-item) {
  margin-bottom: 0;
  display: flex;
  align-items: center;
}

.control-form :deep(.el-form-item__label) {
  line-height: 32px;
  margin-bottom: 0;
}

.control-form :deep(.el-form-item__content) {
  line-height: 32px;
}

.checkbox-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.help-icon {
  margin-left: 8px;
  color: v.$text-secondary;
  cursor: pointer;
  font-size: 16px;
  
  &:hover {
    color: var(--el-color-primary);
  }
}

.indicator-help {
  font-size: 13px;
  line-height: 1.6;
  
  .title {
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-bottom: 4px;
  }
  
  .desc {
    color: var(--el-text-color-regular);
  }
}

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: row; /* Horizontal layout */
    overflow: hidden;
    
    .chart-wrapper {
      flex: 1;
      position: relative;
      display: flex;
      flex-direction: column;
      min-width: 0;
      
      .empty-state {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: v.$text-secondary;
      }
    }
    
    .right-sidebar {
      width: 280px;
      display: flex;
      flex-direction: column;
      border-left: 1px solid v.$border-color;
      background-color: v.$bg-secondary;
      
      .chip-canvas-wrapper {
        flex: 1;
        position: relative;
        min-height: 0;
        display: flex;
        align-items: stretch;
        
        .chip-canvas {
          width: 100%;
          height: 100%;
          display: block;
        }
      }
      
      .stats-panel {
        /* Static layout in sidebar */
        position: static;
        width: 100%;
        max-height: 50%;
        border-top: 1px solid v.$border-color;
        border-left: none;
        border-radius: 0;
        box-shadow: none;
        overflow-y: auto;
        padding: 20px;
        background-color: transparent;

        .panel-header {
          margin-bottom: 20px;
          h3 { margin: 0 0 5px 0; font-size: 16px; font-weight: 600; }
          .period { font-size: 12px; color: v.$text-secondary; }
        }

        .stat-card {
          margin-bottom: 24px;
          h4 {
            font-size: 13px;
            color: v.$text-secondary;
            margin-bottom: 12px;
            border-bottom: 1px solid v.$border-color;
            padding-bottom: 8px;
            font-weight: 600;
          }
          .stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
          }
          .stat-item {
            display: flex;
            flex-direction: column;
            .label { font-size: 12px; color: v.$text-secondary; margin-bottom: 4px; }
            .value {
              font-size: 15px;
              font-weight: 600;
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            }
          }
        }
      }
    }
  }

.stock-code {
  font-weight: bold;
  margin-right: 8px;
}

.stock-name {
  color: #909399;
  font-size: 12px;
}

.text-up { color: #f56c6c; }
.text-down { color: #67c23a; }
</style>
