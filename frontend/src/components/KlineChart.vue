<template>
  <div class="kline-chart-wrapper" :style="{ height: autosize ? '100%' : height + 'px' }">
    <!-- Main Chart -->
    <div class="chart-container main-chart" ref="mainChartContainer" :style="{ flex: showSubChart ? 2 : 1, borderBottom: showSubChart ? '' : 'none' }">
      <div class="chart-legend" :class="{ 'dark-mode': darkMode }">
        <div class="legend-row symbol-info" v-if="currentOHLC">
          <span class="symbol-name">{{ watermark || 'Unknown' }}</span>
          <div class="ohlc-values" v-if="!simpleLegend">
            <span class="item">O: <span :class="getColor(currentOHLC.open, currentOHLC.prevClose)">{{ formatPrice(currentOHLC.open) }}</span></span>
            <span class="item">H: <span :class="getColor(currentOHLC.high, currentOHLC.prevClose)">{{ formatPrice(currentOHLC.high) }}</span></span>
            <span class="item">L: <span :class="getColor(currentOHLC.low, currentOHLC.prevClose)">{{ formatPrice(currentOHLC.low) }}</span></span>
            <span class="item">C: <span :class="getColor(currentOHLC.close, currentOHLC.prevClose)">{{ formatPrice(currentOHLC.close) }}</span></span>
            <span class="item change" :class="getColor(currentOHLC.close, currentOHLC.prevClose)">
              {{ formatChange(currentOHLC.close, currentOHLC.prevClose) }}
            </span>
          </div>
          <div class="ohlc-values" v-else>
            <span class="item change" :class="getColor(currentOHLC.close, currentOHLC.prevClose)">
              {{ formatChange(currentOHLC.close, currentOHLC.prevClose) }}
            </span>
          </div>
        </div>
        <div class="legend-row indicators" v-if="!simpleLegend">
          <div v-for="ind in currentMainIndicators" :key="ind.name" class="indicator-item" :style="{ color: ind.color }">
            <span class="name">{{ ind.name }}:</span>
            <span class="value">{{ formatPrice(ind.value) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Sub Chart -->
    <div v-if="showSubChart" class="chart-container sub-chart" ref="subChartContainer">
      <div class="chart-legend" :class="{ 'dark-mode': darkMode }">
        <div class="legend-row indicators">
          <div v-for="ind in currentSubIndicators" :key="ind.name" class="indicator-item" :style="{ color: ind.color }">
            <span class="name">{{ ind.name }}:</span>
            <span class="value">{{ formatPrice(ind.value) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { 
  createChart, 
  ColorType, 
  CrosshairMode,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createSeriesMarkers,
  type LineWidth
} from 'lightweight-charts';
import type { IChartApi, ISeriesApi, MouseEventParams, ISeriesMarkersPluginApi } from 'lightweight-charts';

// Data Interfaces
import ChipDistributionSeries, { type ChipDistributionData } from '@/plugins/ChipDistributionSeries';

export interface ChartData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
  pct_chg?: number; // 涨跌幅（百分比，如 2.5 表示 2.5%）
}

export interface Marker {
  time: string;
  position: 'aboveBar' | 'belowBar' | 'inBar';
  color: string;
  shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown';
  text: string;
}

export interface LineData {
  name: string;
  data: { time: string; value: number; color?: string }[];
  color: string;
  lineWidth?: number;
  pane?: 'main' | 'sub'; // 'main' or 'sub'
  style?: 'line' | 'histogram';
}

const props = withDefaults(defineProps<{
  data: ChartData[];
  markers?: Marker[];
  lines?: LineData[];
  height?: number;
  watermark?: string;
  darkMode?: boolean;
  autosize?: boolean;
  showSubChart?: boolean; // Prop to control sub-chart visibility
  simpleLegend?: boolean; // Prop to simplify legend (hide OHLC and indicators)
  chipData?: ChipDistributionData | null;
}>(), {
  height: 600,
  markers: () => [],
  lines: () => [],
  darkMode: false,
  autosize: false,
  showSubChart: true,
  simpleLegend: false,
  chipData: null
});

const emit = defineEmits(['visible-range-change']);


// ... existing refs
let candlestickSeries: ISeriesApi<"Candlestick"> | null = null;
let cyqSeries: ChipDistributionSeries | null = null;

// ... existing code ...

const updateCYQ = () => {
    if (!candlestickSeries) return;
    
    if (props.chipData) {
        if (!cyqSeries) {
            cyqSeries = new ChipDistributionSeries();
            candlestickSeries.attachPrimitive(cyqSeries);
        }
        cyqSeries.setData(props.chipData);
    } else {
        if (cyqSeries) {
            candlestickSeries.detachPrimitive(cyqSeries);
            cyqSeries = null;
        }
    }
};

watch(() => props.chipData, () => {
    updateCYQ();
}, { deep: true });

// Modify initCharts to call updateCYQ
// ... inside initCharts, after candlestickSeries creation:
// candlestickSeries = mainChart.addSeries(CandlestickSeries, ...);
// markersPlugin = ...
// updateCYQ(); // Add this line

// ... existing onUnmounted
onUnmounted(() => {
    if (mainChart) { mainChart.remove(); mainChart = null; }
    if (subChart) { subChart.remove(); subChart = null; }
    if (mainResizeObserver) mainResizeObserver.disconnect();
    if (subResizeObserver) subResizeObserver.disconnect();
    cyqSeries = null;
});


// Containers
const mainChartContainer = ref<HTMLElement | null>(null);
const subChartContainer = ref<HTMLElement | null>(null);

// Chart Instances
let mainChart: IChartApi | null = null;
let subChart: IChartApi | null = null;

// Series
let markersPlugin: ISeriesMarkersPluginApi<any> | null = null;
const mainSeriesMap = new Map<string, ISeriesApi<"Line" | "Histogram">>();
const subSeriesMap = new Map<string, ISeriesApi<"Line" | "Histogram">>();

// Observers
let mainResizeObserver: ResizeObserver | null = null;
let subResizeObserver: ResizeObserver | null = null;

// Tooltip State
const currentOHLC = ref<any>(null);
const currentMainIndicators = ref<any[]>([]);
const currentSubIndicators = ref<any[]>([]);

// Helper to safely set markers (Removed as we use plugin now)
// const safelySetMarkers = (series: ISeriesApi<"Candlestick"> | null, markers: Marker[]) => { ... }

// Formatters
const formatPrice = (val: number) => val !== undefined && val !== null ? Number(val.toFixed(2)) : '--';
const formatChange = (curr: number, prev: number) => {
  if (!curr || !prev) return '';
  const chg = (curr - prev) / prev * 100;
  return `${chg > 0 ? '+' : ''}${chg.toFixed(2)}%`;
};
const getColor = (curr: number, prev: number) => {
  if (!curr || !prev) return '';
  return curr >= prev ? 'text-up' : 'text-down';
};

// Colors
// const chartColors = { ... }; // Removed unused

// Sync Logic
const syncCharts = (source: IChartApi, target: IChartApi) => {
    source.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (range) {
            target.timeScale().setVisibleLogicalRange(range);
        }
    });
};

const handleVisibleRangeChange = () => {
    if (!mainChart || !mainChartContainer.value) return;
    
    // Get visible price range from the main chart's right scale
    // IPriceScaleApi doesn't have getVisiblePriceRange directly in all versions, 
    // so we use coordinateToPrice conversion which is robust.
    const height = mainChartContainer.value.clientHeight;
    const series = candlestickSeries; // Use the main series for conversion
    
    if (series) {
        const topPrice = series.coordinateToPrice(0);
        const bottomPrice = series.coordinateToPrice(height);
        
        if (topPrice !== null && bottomPrice !== null) {
             emit('visible-range-change', {
                min: Math.min(topPrice, bottomPrice),
                max: Math.max(topPrice, bottomPrice),
                height: height
            });
        }
    }
};

const initCharts = async () => {
    if (!mainChartContainer.value) return;
    
    // Cleanup
    if (mainChart) { mainChart.remove(); mainChart = null; }
    if (subChart) { subChart.remove(); subChart = null; }
    mainSeriesMap.clear();
    subSeriesMap.clear();

  await nextTick();

    // Debug log
    console.log('Initializing KlineChart', {
        width: mainChartContainer.value.clientWidth,
        height: mainChartContainer.value.clientHeight,
        dataLength: props.data.length,
        linesLength: props.lines.length
    });

    // Custom price formatter for consistent digit width across all charts
    const formatPrice = (price: number): string => {
        const abs = Math.abs(price);
        const sign = price < 0 ? '-' : '';
        
        if (abs >= 1000000) {
            return sign + (abs / 1000000).toFixed(2) + 'M';
        } else if (abs >= 1000) {
            return sign + (abs / 1000).toFixed(2) + 'K';
        } else if (abs >= 1) {
            return sign + abs.toFixed(2);
        } else if (abs > 0) {
            return sign + abs.toFixed(4);
        } else {
            return '0.00';
        }
    };

    // Chart Config
    const commonOptions = {
    layout: {
      background: { type: ColorType.Solid, color: props.darkMode ? '#1b1b1f' : '#ffffff' },
      textColor: props.darkMode ? '#d1d4dc' : '#333',
    },
    grid: {
            vertLines: { color: props.darkMode ? '#2B2B43' : '#f0f3fa' },
            horzLines: { color: props.darkMode ? '#2B2B43' : '#f0f3fa' },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
            vertLine: { width: 1 as LineWidth, color: props.darkMode ? '#555' : '#9B7DFF', style: 3 },
            horzLine: { width: 1 as LineWidth, color: props.darkMode ? '#555' : '#9B7DFF', style: 3 },
    },
      leftPriceScale: {
            visible: false,  // Hide left price scale to ensure consistent layout
        },
      rightPriceScale: {
            borderColor: props.darkMode ? '#2B2B43' : '#d1d4dc',
            scaleMargins: { top: 0.1, bottom: 0.1 },
            minimumWidth: 80,  // Increased to accommodate wider volume numbers
        },
        localization: {
            priceFormatter: formatPrice,
        },
    };

    // --- Main Chart ---
    mainChart = createChart(mainChartContainer.value, {
        ...commonOptions,
      timeScale: {
            borderColor: props.darkMode ? '#2B2B43' : '#d1d4dc',
            visible: true,
        timeVisible: true,
        },
        width: mainChartContainer.value.clientWidth,
        height: mainChartContainer.value.clientHeight,
    });

    // Subscribe to visible range changes (Logical range changes often trigger price scale updates)
    mainChart.timeScale().subscribeVisibleLogicalRangeChange(() => {
        handleVisibleRangeChange();
    });

    // Subscribe to crosshair move on main chart to update legend
    mainChart.subscribeCrosshairMove((param) => handleCrosshairMove(param, 'main'));

    mainResizeObserver = new ResizeObserver(entries => {
        if (!mainChart || entries.length === 0) return;
        mainChart.applyOptions({ width: entries[0].contentRect.width, height: entries[0].contentRect.height });
        handleVisibleRangeChange();
    });
    mainResizeObserver.observe(mainChartContainer.value);

    candlestickSeries = mainChart.addSeries(CandlestickSeries, {
        upColor: '#ef5350', downColor: '#26a69a',
        borderVisible: false, wickUpColor: '#ef5350', wickDownColor: '#26a69a',
    });
    
    // Initialize markers plugin
    markersPlugin = createSeriesMarkers(candlestickSeries, []);
    
    // Debug series creation
    console.log('Series created:', candlestickSeries);

    // --- Sub Chart ---
    if (props.showSubChart && subChartContainer.value) {
        subChart = createChart(subChartContainer.value, {
            ...commonOptions,
      timeScale: {
                borderColor: props.darkMode ? '#2B2B43' : '#d1d4dc',
        visible: false,  // Hide time scale on sub chart to prevent misalignment
        timeVisible: false,
            },
            rightPriceScale: {
                ...commonOptions.rightPriceScale,
                visible: true,  // Ensure price scale is visible for VOL
            },
            width: subChartContainer.value.clientWidth,
            height: subChartContainer.value.clientHeight,
        });

        // Sync
        syncCharts(mainChart, subChart);
        syncCharts(subChart, mainChart);
        
        // subChart.subscribeCrosshairMove((param) => handleCrosshairMove(param, 'sub')); // This is handled by sync, but we might want legend update
        // Actually, main chart crosshair move is enough if synced, but let's keep it consistent
        subChart.subscribeCrosshairMove((param) => handleCrosshairMove(param, 'sub'));
        
        subResizeObserver = new ResizeObserver(entries => {
            if (!subChart || entries.length === 0) return;
            subChart.applyOptions({ width: entries[0].contentRect.width, height: entries[0].contentRect.height });
        });
        subResizeObserver.observe(subChartContainer.value);
    } else {
        // If no sub chart, we might want to ensure main chart resize observer is still active (it is)
    }

    updateData(true);
};

const handleCrosshairMove = (param: MouseEventParams, type: 'main' | 'sub') => {
    const time = param.time;
    
    // Check if mouse is out of chart
    if (!time || param.point === undefined || param.point.x < 0 || param.point.x > (mainChartContainer.value?.clientWidth || 0) || param.point.y < 0 || param.point.y > (mainChartContainer.value?.clientHeight || 0)) {
        // Reset to last if valid
        if (props.data.length > 0) {
            const last = props.data[props.data.length - 1];
            const prev = props.data.length > 1 ? props.data[props.data.length - 2] : last;
            // Always update main legend regardless of source type
            // 对于最后一根K线，如果有pct_chg则使用，否则计算
            let prevClose = prev.close;
            if (last.pct_chg !== undefined && last.pct_chg !== null) {
                // 如果有pct_chg，反推前一日收盘价
                prevClose = last.close / (1 + last.pct_chg / 100);
            }
            currentOHLC.value = { ...last, prevClose };
            
            // Reset indicators
            updateIndicatorLegend(props.lines.filter(l => l.pane !== 'sub'), props.data.length - 1, currentMainIndicators);
            if (props.showSubChart) {
                updateIndicatorLegend(props.lines.filter(l => l.pane === 'sub'), props.data.length - 1, currentSubIndicators);
            }
        }
        return;
    }
    
    // Find logical index? Or match time.
    // param.time is the string time we pushed.
    // However, lightweight-charts might convert it to BusinessDay object if it detects date pattern.
    // We need to handle both string and object.
    
    let timeStr = time as string;
    if (typeof time === 'object') {
        // BusinessDay: { year, month, day }
        const d = time as { year: number, month: number, day: number };
        timeStr = `${d.year}-${String(d.month).padStart(2, '0')}-${String(d.day).padStart(2, '0')}`;
    }

    const index = props.data.findIndex(d => d.time === timeStr);
    if (index >= 0) {
        // Update legends for both charts
        const d = props.data[index];
        let prevClose: number;
        
        if (index > 0) {
            // 有前一日数据，直接使用前一日收盘价
            prevClose = props.data[index - 1].close;
        } else {
            // 第一根K线：优先使用数据中的pct_chg字段
            if (d.pct_chg !== undefined && d.pct_chg !== null) {
                // 如果有pct_chg，反推前一日收盘价
                prevClose = d.close / (1 + d.pct_chg / 100);
            } else {
                // 如果没有pct_chg，使用当前收盘价（显示0%）
                prevClose = d.close;
            }
        }
        
        currentOHLC.value = { ...d, prevClose };
        
        updateIndicatorLegend(props.lines.filter(l => l.pane !== 'sub'), index, currentMainIndicators);
        if (props.showSubChart) {
            updateIndicatorLegend(props.lines.filter(l => l.pane === 'sub'), index, currentSubIndicators);
        }
    }
};

const updateIndicatorLegend = (lines: LineData[], index: number, targetRef: any) => {
    const values = [];
    for (const line of lines) {
        const item = line.data[index]; // Assuming data aligns with main kline data (same length/time)
        // If data is sparse, we need to find by time
        // Optimization: Assume aligned for now or search
        if (item && item.time === props.data[index].time) {
             values.push({ name: line.name, value: item.value, color: line.color });
        } else {
             // Search fallback
             const exact = line.data.find(d => d.time === props.data[index].time);
             if (exact) values.push({ name: line.name, value: exact.value, color: line.color });
        }
    }
    targetRef.value = values;
};

const updateData = (fitContent = false) => {
    // We only need mainChart to be present. 
    // subChart is optional (depending on props.showSubChart)
    if (!mainChart) return; 

    // K-Line Data
    if (props.data.length > 0) {
        // Sort
        const sorted = [...props.data].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
        // Clean
        const unique = sorted.filter((item, index, self) => index === self.findIndex((t) => (t.time === item.time)));
        
        candlestickSeries?.setData(unique.map(d => ({
            time: d.time,
            open: d.open, high: d.high, low: d.low, close: d.close
        })));

        // Set Markers
        if (props.markers && props.markers.length > 0) {
            // Ensure sorted by time
            const sortedMarkers = [...props.markers].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
            if (markersPlugin) {
                 markersPlugin.setMarkers(sortedMarkers as any);
            }
        } else {
            if (markersPlugin) {
                 markersPlugin.setMarkers([]);
            }
        }

        // Init Legend
        const lastIndex = unique.length - 1;
        const last = unique[lastIndex];
        let prevClose: number;
        if (lastIndex > 0) {
            prevClose = unique[lastIndex - 1].close;
        } else {
            // 第一根K线：优先使用数据中的pct_chg字段
            if (last.pct_chg !== undefined && last.pct_chg !== null) {
                // 如果有pct_chg，反推前一日收盘价
                prevClose = last.close / (1 + last.pct_chg / 100);
            } else {
                // 如果没有pct_chg，使用当前收盘价（显示0%）
                prevClose = last.close;
            }
        }
        currentOHLC.value = { ...last, prevClose };
    }

    // Lines
    // const mainLines = props.lines.filter(l => l.pane !== 'main'); // Removed
    // Actually pane logic: if pane is explicitly 'sub', go to sub. Else main.
    // Correct logic:
    const mainLinesData = props.lines.filter(l => l.pane !== 'sub');
    const subLinesData = props.lines.filter(l => l.pane === 'sub');

    // Helper to update series map
    const updateSeriesMap = (chartInstance: IChartApi, lines: LineData[], map: Map<string, ISeriesApi<"Line" | "Histogram">>) => {
        if (!chartInstance) return; // Guard if sub chart not created
        
        // Remove unused
        const currentNames = new Set(lines.map(l => l.name));
        for (const [name, series] of map) {
            if (!currentNames.has(name)) {
                chartInstance.removeSeries(series);
                map.delete(name);
            }
        }

        // Add/Update
        lines.forEach(line => {
            let series = map.get(line.name);
            const options: any = {
                color: line.color,
                lineWidth: line.lineWidth || 1,
                title: line.name,
                priceScaleId: 'right', // Use right scale for all series
            };
            
            // Note: All series now use the same 'right' price scale for consistency

            if (!series) {
                if (line.style === 'histogram') {
                    series = chartInstance.addSeries(HistogramSeries, options);
                } else {
                    series = chartInstance.addSeries(LineSeries, options);
                }
                map.set(line.name, series);
            } else {
                series.applyOptions(options);
            }

            // Data
            const seriesData = line.data
                .filter(d => d.time && !isNaN(d.value))
                .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
                .map(d => ({ time: d.time, value: d.value, color: d.color }));
            
            // Debug log
            if (seriesData.length === 0) {
                console.warn(`Line ${line.name} has no valid data`);
            }
            
            series.setData(seriesData as any);
        });
    };

    updateSeriesMap(mainChart, mainLinesData, mainSeriesMap);
    if (subChart) {
        updateSeriesMap(subChart, subLinesData, subSeriesMap);
    }

    // Initial Legend for Indicators
    if (props.data.length > 0) {
        updateIndicatorLegend(mainLinesData, props.data.length - 1, currentMainIndicators);
        updateIndicatorLegend(subLinesData, props.data.length - 1, currentSubIndicators);
    }

    if (fitContent) {
        // 使用requestAnimationFrame确保在数据设置后的下一帧调用fitContent
        // 这样可以避免闪烁，让图表在绘制时就直接占满画布
        requestAnimationFrame(() => {
            // 只要有数据或有线图数据，就调用fitContent
            if (mainChart && (props.data.length > 0 || props.lines.length > 0)) {
                mainChart.timeScale().fitContent();
            }
        });
        // Sub chart syncs automatically via logic range
    }
};

watch(() => props.data, () => {
    if (!mainChart) initCharts();
    else {
        updateData(true);
        // 使用requestAnimationFrame确保在下一帧渲染时调用fitContent，避免闪烁
        requestAnimationFrame(() => {
            if (mainChart && (props.data.length > 0 || props.lines.length > 0)) {
                mainChart.timeScale().fitContent();
            }
        });
    }
}, { deep: true });

// 监听 lines 变化（用于纯线图场景，如收益率曲线）
watch(() => props.lines, () => {
    if (!mainChart) initCharts();
    else {
        updateData(true);
        // 使用requestAnimationFrame确保在下一帧渲染时调用fitContent，避免闪烁
        requestAnimationFrame(() => {
            if (mainChart && (props.data.length > 0 || props.lines.length > 0)) {
                mainChart.timeScale().fitContent();
            }
        });
    }
}, { deep: true });

// 暴露fitContent方法供父组件调用
const fitContent = () => {
    if (mainChart && (props.data.length > 0 || props.lines.length > 0)) {
        mainChart.timeScale().fitContent();
    }
};

defineExpose({
    fitContent
});

watch(() => props.markers, () => {
    if (markersPlugin && props.data.length > 0) {
        if (props.markers && props.markers.length > 0) {
            const sortedMarkers = [...props.markers].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
            markersPlugin.setMarkers(sortedMarkers as any);
  } else {
            markersPlugin.setMarkers([]);
        }
    }
}, { deep: true });

watch(() => props.lines, () => {
    if (mainChart) updateData(false); // No fit content
}, { deep: true });

watch(() => props.darkMode, () => {
    if (!mainChart) return;
    const theme = {
        layout: { background: { color: props.darkMode ? '#1b1b1f' : '#ffffff' }, textColor: props.darkMode ? '#d1d4dc' : '#333' },
        grid: { vertLines: { color: props.darkMode ? '#2B2B43' : '#f0f3fa' }, horzLines: { color: props.darkMode ? '#2B2B43' : '#f0f3fa' } },
        rightPriceScale: { borderColor: props.darkMode ? '#2B2B43' : '#d1d4dc' },
        timeScale: { borderColor: props.darkMode ? '#2B2B43' : '#d1d4dc' },
    };
    mainChart.applyOptions(theme as any);
    if (subChart) {
        subChart.applyOptions(theme as any);
    }
});

onMounted(initCharts);
onUnmounted(() => {
    if (mainChart) { mainChart.remove(); mainChart = null; }
    if (subChart) { subChart.remove(); subChart = null; }
    if (mainResizeObserver) mainResizeObserver.disconnect();
    if (subResizeObserver) subResizeObserver.disconnect();
});
</script>

<style scoped lang="scss">
.kline-chart-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.chart-container {
  width: 100%;
  position: relative;
  
  &.main-chart {
    flex: 2; /* 2/3 height */
    border-bottom: 1px solid rgba(128, 128, 128, 0.1);
  }
  
  &.sub-chart {
    flex: 1; /* 1/3 height */
  }
}

.chart-legend {
  position: absolute;
  top: 4px;
  left: 4px;
  z-index: 20;
  font-family: 'Roboto Mono', monospace;
  font-size: 12px;
  pointer-events: none;
  background: rgba(255, 255, 255, 0.8);
  padding: 4px;
  border-radius: 4px;
  
  &.dark-mode {
    background: rgba(27, 27, 31, 0.8);
    .symbol-name { color: #e0e0e0; }
    .ohlc-values { color: #a0a0a0; }
  }

  .legend-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 2px;
  }

  .symbol-name {
    font-weight: bold;
    font-size: 13px;
    color: #333;
  }

  .ohlc-values {
    display: flex;
    gap: 8px;
    color: #666;
    font-size: 11px;
    
    .item span {
      font-weight: 500;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
  }

  .indicators {
    .indicator-item {
      display: flex;
      gap: 4px;
      margin-right: 8px;
      .name { opacity: 0.8; }
      .value { 
        font-weight: 500;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      }
    }
  }
}

.text-up { color: #ef5350 !important; }
.text-down { color: #26a69a !important; }
</style>
