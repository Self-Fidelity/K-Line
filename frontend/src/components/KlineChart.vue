<template>
  <div class="chart-container" ref="chartContainer"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, defineProps, withDefaults, nextTick } from 'vue';
import { createChart, ColorType, CrosshairMode, IChartApi, ISeriesApi } from 'lightweight-charts';

// 定义数据接口
export interface ChartData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
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
  data: { time: string; value: number }[];
  color: string;
  lineWidth?: number;
  priceScaleId?: string; // 'right', 'left', or custom
}

const props = withDefaults(defineProps<{
  data: ChartData[];
  markers?: Marker[];
  lines?: LineData[];
  height?: number;
  watermark?: string;
  darkMode?: boolean;
}>(), {
  height: 500,
  markers: () => [],
  lines: () => [],
  darkMode: false
});

const chartContainer = ref<HTMLElement | null>(null);
// 使用普通变量而非 ref 来存储 chart 实例，避免 Vue Proxy 干扰
let chart: IChartApi | null = null;
let candlestickSeries: ISeriesApi<"Candlestick"> | null = null;
let volumeSeries: ISeriesApi<"Histogram"> | null = null;
const lineSeriesMap = new Map<string, ISeriesApi<"Line">>();

// 初始化图表
const initChart = async () => {
  if (!chartContainer.value) return;
  
  // 销毁旧图表
  if (chart) {
    try {
        chart.remove();
    } catch (e) {
        console.warn('Error removing chart:', e);
    }
    chart = null;
    candlestickSeries = null;
    volumeSeries = null;
    lineSeriesMap.clear();
  }
  
  // 等待DOM完全准备好
  await nextTick();

  // 二次检查，确保在nextTick后元素仍然存在
  if (!chartContainer.value) return;

  const chartOptions = {
    layout: {
      background: { type: ColorType.Solid, color: props.darkMode ? '#1b1b1f' : '#ffffff' },
      textColor: props.darkMode ? '#d1d4dc' : '#333',
    },
    grid: {
      vertLines: { color: props.darkMode ? '#404040' : '#f0f3fa' },
      horzLines: { color: props.darkMode ? '#404040' : '#f0f3fa' },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
    },
    rightPriceScale: {
      borderColor: props.darkMode ? '#404040' : '#d1d4dc',
    },
    timeScale: {
      borderColor: props.darkMode ? '#404040' : '#d1d4dc',
      timeVisible: true,
    },
    width: chartContainer.value.clientWidth,
    height: props.height,
  };

  try {
    // 强制转换为 any 以绕过可能得 TS 类型错误，实际 createChart 返回的对象应该包含这些方法
    chart = createChart(chartContainer.value, chartOptions) as any;
    
    // 调试：确保 chart 创建成功
    if (!chart) {
      console.error('Failed to create chart instance');
      return;
    }
    
    // 检查方法是否存在
    if (typeof (chart as any).addCandlestickSeries !== 'function') {
        console.error('addCandlestickSeries method missing on chart instance', chart);
        // 如果是 v5，API 可能已经变了，但 addCandlestickSeries 应该是标准的
        // 尝试另一种调用方式或检查 chart 对象结构
        // 临时回退：如果方法不存在，打印对象结构
        return;
    }

  } catch (e) {
    console.error('Error creating chart:', e);
    return;
  }

  // 添加水印
  if (props.watermark) {
    chart.applyOptions({
      watermark: {
        color: props.darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        visible: true,
        text: props.watermark,
        fontSize: 24,
        horzAlign: 'center',
        vertAlign: 'center',
      },
    });
  }

  try {
    // 创建K线系列
    candlestickSeries = chart.addCandlestickSeries({
      upColor: '#ef5350',
      downColor: '#26a69a',
      borderVisible: false,
      wickUpColor: '#ef5350',
      wickDownColor: '#26a69a',
    });

    // 创建成交量系列（覆盖在底部）
    volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // Set as an overlay
    });
    
    // 设置成交量位置
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8, // Highest point of the series will be 80% away from the top
        bottom: 0,
      },
    });

    updateChartData();
  } catch (e) {
    console.error('Error adding series to chart:', e);
    // 如果初始化失败，清理资源
    if (chart) {
      chart.remove();
      chart = null;
    }
  }
};

// 更新数据
const updateChartData = () => {
  if (!chart || !candlestickSeries || !volumeSeries) return;

  try {
    // 1. 设置K线数据
    if (!props.data || props.data.length === 0) return;

    // Ensure data is sorted by time and unique
    const sortedData = [...props.data]
      .filter(d => d.time) // Ensure time exists
      .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
      
    // Remove duplicates based on time
    const uniqueData = sortedData.filter((item, index, self) =>
      index === self.findIndex((t) => (t.time === item.time))
    );
    
    candlestickSeries.setData(uniqueData.map(d => ({
      time: d.time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    })));

    // 2. 设置成交量数据
    volumeSeries.setData(uniqueData.map(d => ({
      time: d.time,
      value: d.volume || 0,
      color: d.close >= d.open ? 'rgba(239, 83, 80, 0.5)' : 'rgba(38, 166, 154, 0.5)',
    })));

    // 3. 设置标记
    // 确保标记时间在数据范围内
    const dataTimes = new Set(uniqueData.map(d => d.time));
    const validMarkers = props.markers.filter(m => dataTimes.has(m.time));
    
    candlestickSeries.setMarkers(validMarkers.map(m => ({
      ...m,
      time: m.time,
    })));

    // 4. 清除旧的线系列
    lineSeriesMap.forEach(series => {
      try {
        chart?.removeSeries(series);
      } catch (e) {
        console.warn('Failed to remove series:', e);
      }
    });
    lineSeriesMap.clear();

    // 5. 添加新的线系列
    if (props.lines) {
      props.lines.forEach(line => {
        if (!chart) return;
        
        const lineSeries = chart.addLineSeries({
          color: line.color,
          lineWidth: line.lineWidth || 2,
          priceScaleId: line.priceScaleId || 'right',
          title: line.name,
        });
        
        // Ensure line data is also sorted and valid
        const sortedLineData = [...line.data]
           .filter(d => d.time && dataTimes.has(d.time)) // Match main data timeframe usually
           .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

        const uniqueLineData = sortedLineData.filter((item, index, self) =>
           index === self.findIndex((t) => (t.time === item.time))
        );
        
        lineSeries.setData(uniqueLineData);
        lineSeriesMap.set(line.name, lineSeries);
      });
    }
    
    // 适配内容
    chart.timeScale().fitContent();
    
  } catch (e) {
    console.error('Error updating chart data:', e);
  }
};

// 监听数据变化
watch(() => [props.data, props.markers, props.lines, props.darkMode], () => {
  // 如果数据更新但 chart 未初始化，尝试初始化
  if (!chart) {
    initChart();
  } else {
    // 如果暗黑模式改变，需要更新options
    chart.applyOptions({
      layout: {
        background: { type: ColorType.Solid, color: props.darkMode ? '#1b1b1f' : '#ffffff' },
        textColor: props.darkMode ? '#d1d4dc' : '#333',
      },
      grid: {
        vertLines: { color: props.darkMode ? '#404040' : '#f0f3fa' },
        horzLines: { color: props.darkMode ? '#404040' : '#f0f3fa' },
      },
    });
    updateChartData();
  }
}, { deep: true });

// 窗口大小调整
const handleResize = () => {
  if (chart && chartContainer.value) {
    chart.applyOptions({ width: chartContainer.value.clientWidth });
  }
};

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (chart) {
    chart.remove();
    chart = null;
    candlestickSeries = null;
    volumeSeries = null;
    lineSeriesMap.clear();
  }
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  position: relative;
}
</style>
