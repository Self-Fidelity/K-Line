<template>
  <div class="kline-chart-wrapper" :style="{ height: autosize ? '100%' : height + 'px' }">
    <!-- Main Chart -->
    <div class="chart-container main-chart" ref="mainChartContainer" :style="{ flex: showSubChart ? 2 : 1, borderBottom: showSubChart ? '' : 'none' }">
    </div>

    <!-- Sub Chart -->
    <div v-if="showSubChart" class="chart-container sub-chart" ref="subChartContainer">
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
  showSubChart?: boolean;
  simpleLegend?: boolean;
  chipData?: ChipDistributionData | null;
  loadingMore?: boolean;
}>(), {
  height: 600,
  markers: () => [],
  lines: () => [],
  darkMode: false,
  autosize: false,
  showSubChart: true,
  simpleLegend: false,
  chipData: null,
  loadingMore: false
});

const emit = defineEmits<{
  (e: 'load-more'): void;
}>();

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

// Sync Logic
const syncCharts = (source: IChartApi, target: IChartApi) => {
    source.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (range) {
            target.timeScale().setVisibleLogicalRange(range);
        }
    });
};

// Lazy loading: detect when user scrolls near left edge
let loadMoreDebounceTimer: ReturnType<typeof setTimeout> | null = null;
let lastDataLength = 0;

const attachLazyLoadListener = () => {
    if (!mainChart) return;
    mainChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (!range || props.data.length === 0 || props.loadingMore) return;
        // Trigger when viewport start is near the beginning of data
        if (range.from <= 15) {
            if (loadMoreDebounceTimer) clearTimeout(loadMoreDebounceTimer);
            loadMoreDebounceTimer = setTimeout(() => {
                emit('load-more');
            }, 400);
        }
    });
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

    // Price formatter: always show 2 decimal places
    const formatPrice = (price: number): string => {
        if (price === 0 || isNaN(price)) return '0.00';
        return price.toFixed(2);
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
        watermark: props.watermark ? {
            visible: true,
            text: props.watermark,
            fontSize: 24,
            lineHeight: 36,
            fontFamily: 'Arial, sans-serif',
            fontStyle: '',
            color: props.darkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
            textAlign: 'center',
            vertAlign: 'center',
            horzAlign: 'center',
        } : undefined,
    });

    mainResizeObserver = new ResizeObserver(entries => {
        if (!mainChart || entries.length === 0) return;
        mainChart.applyOptions({ width: entries[0].contentRect.width, height: entries[0].contentRect.height });
    });
    mainResizeObserver.observe(mainChartContainer.value);

    candlestickSeries = mainChart.addSeries(CandlestickSeries, {
        upColor: '#ef5350', downColor: '#26a69a',
        borderVisible: false, wickUpColor: '#ef5350', wickDownColor: '#26a69a',
        title: 'K线',
        lastValueVisible: true,
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
        
        subResizeObserver = new ResizeObserver(entries => {
            if (!subChart || entries.length === 0) return;
            subChart.applyOptions({ width: entries[0].contentRect.width, height: entries[0].contentRect.height });
        });
        subResizeObserver.observe(subChartContainer.value);
    } else {
        // If no sub chart, we might want to ensure main chart resize observer is still active (it is)
    }

    updateData(true);
    attachLazyLoadListener();
    lastDataLength = props.data.length;
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
        watermark: props.watermark ? {
            color: props.darkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
        } : undefined,
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
    if (loadMoreDebounceTimer) clearTimeout(loadMoreDebounceTimer);
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


</style>
