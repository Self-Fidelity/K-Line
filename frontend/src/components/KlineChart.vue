<template>
  <div class="chart-container" ref="chartContainer"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, defineProps, withDefaults, nextTick } from 'vue';
import { 
  createChart, 
  ColorType, 
  CrosshairMode,
  CandlestickSeries,
  HistogramSeries,
  LineSeries
} from 'lightweight-charts';
import type { IChartApi, ISeriesApi } from 'lightweight-charts';

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
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
        entireTextOnly: false,
      },
      leftPriceScale: {
        visible: false,
      },
      timeScale: {
        borderColor: props.darkMode ? '#404040' : '#d1d4dc',
        timeVisible: true,
        rightOffset: 12,
        barSpacing: 3,
        rightBarStaysOnScroll: true,
        lockVisibleTimeRangeOnResize: false,
      },
    width: chartContainer.value.clientWidth,
    height: props.height,
  };

  try {
    // 创建图表实例
    chart = createChart(chartContainer.value, chartOptions);
    
    // 调试：确保 chart 创建成功
    if (!chart) {
      console.error('Failed to create chart instance');
      return;
    }
    
    // 调试：检查 chart 对象的方法
    const chartProto = Object.getPrototypeOf(chart);
    const chartMethods = Object.getOwnPropertyNames(chartProto)
      .filter(name => typeof (chart as any)[name] === 'function' && !name.startsWith('_'));
    console.log('Chart available methods (first 30):', chartMethods.slice(0, 30));
    
    // 检查是否有 addCandlestickSeries 方法
    if (!('addCandlestickSeries' in chart)) {
      console.error('addCandlestickSeries method not found in chart instance');
      console.error('Chart object keys:', Object.keys(chart));
      console.error('Chart prototype keys:', Object.keys(chartProto));
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
    // 只有当有K线数据时才创建K线系列
    if (props.data && props.data.length > 0 && chart) {
      try {
        // lightweight-charts v5 使用 addSeries(SeriesDefinition, options) API
        candlestickSeries = chart.addSeries(CandlestickSeries, {
          upColor: '#ef5350',
          downColor: '#26a69a',
          borderVisible: false,
          wickUpColor: '#ef5350',
          wickDownColor: '#26a69a',
        }) as any;

        // 创建成交量系列（覆盖在底部）
        volumeSeries = chart.addSeries(HistogramSeries, {
          color: '#26a69a',
          priceFormat: {
            type: 'volume',
          },
          priceScaleId: '', // Set as an overlay
        }) as any;
        
        // 设置成交量位置
        if (volumeSeries && volumeSeries.priceScale) {
          volumeSeries.priceScale().applyOptions({
            scaleMargins: {
              top: 0.8, // Highest point of the series will be 80% away from the top
              bottom: 0,
            },
          });
        }
      } catch (seriesError) {
        console.error('Error creating series:', seriesError);
        console.error('Chart object:', chart);
        // 即使创建系列失败，也继续尝试显示线图
      }
    }

    updateChartData();
  } catch (e) {
    console.error('Error adding series to chart:', e);
    console.error('Error details:', e);
    // 如果初始化失败，清理资源
    if (chart) {
      try {
        chart.remove();
      } catch (removeError) {
        console.error('Error removing chart:', removeError);
      }
      chart = null;
    }
  }
};

// 更新数据
const updateChartData = () => {
  if (!chart) {
    console.warn('Chart not initialized, cannot update data');
    return;
  }

  try {
    console.log('Updating chart data:', {
      dataLength: props.data?.length || 0,
      linesLength: props.lines?.length || 0,
      markersLength: props.markers?.length || 0,
      hasCandlestick: !!candlestickSeries,
      hasVolume: !!volumeSeries
    });

    // 1. 设置K线数据（如果有数据且需要显示K线）
    if (props.data && props.data.length > 0) {
      // 只有当有 candlestickSeries 时才设置K线数据
      if (candlestickSeries && volumeSeries) {
        // 格式化时间：确保是 YYYY-MM-DD 格式
        const formatTime = (time: string): string => {
          if (!time) return ''
          // 如果已经是 YYYY-MM-DD 格式，直接返回
          if (/^\d{4}-\d{2}-\d{2}$/.test(time)) {
            return time
          }
          // 尝试解析其他格式
          const date = new Date(time)
          if (isNaN(date.getTime())) {
            console.warn('Invalid time format:', time)
            return ''
          }
          const year = date.getFullYear()
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          return `${year}-${month}-${day}`
        }

        // 验证和格式化K线数据
        const formatCandlestickData = (d: any) => {
          const time = formatTime(d.time)
          if (!time) return null
          
          const open = Number(d.open)
          const high = Number(d.high)
          const low = Number(d.low)
          const close = Number(d.close)
          
          // 验证数据有效性
          if (isNaN(open) || isNaN(high) || isNaN(low) || isNaN(close)) {
            console.warn('Invalid OHLC data:', d)
            return null
          }
          
          // 确保 high >= max(open, close) 且 low <= min(open, close)
          const maxPrice = Math.max(open, close)
          const minPrice = Math.min(open, close)
          
          return {
            time: time,
            open: open,
            high: Math.max(high, maxPrice), // 确保 high 不小于 open 和 close 的最大值
            low: Math.min(low, minPrice),   // 确保 low 不大于 open 和 close 的最小值
            close: close,
          }
        }

        // Ensure data is sorted by time and unique
        const sortedData = [...props.data]
          .map(formatCandlestickData)
          .filter((d): d is NonNullable<typeof d> => d !== null)
          .sort((a, b) => {
            const timeA = new Date(a.time).getTime()
            const timeB = new Date(b.time).getTime()
            return timeA - timeB
          });
          
        // Remove duplicates based on time
        const uniqueData = sortedData.filter((item, index, self) =>
          index === self.findIndex((t) => (t.time === item.time))
        );
        
        console.log('Formatted K-line data sample:', uniqueData.slice(0, 5))
        console.log('Total K-line data points:', uniqueData.length)
        
        if (uniqueData.length === 0) {
          console.warn('No valid K-line data after formatting')
          return
        }
    
        candlestickSeries.setData(uniqueData);

        // 2. 设置成交量数据
        const volumeData = uniqueData.map(d => {
          const volume = Number(d.volume) || 0
          const originalData = props.data.find(item => formatTime(item.time) === d.time)
          const isUp = d.close >= d.open
          
          return {
            time: d.time,
            value: volume,
            color: isUp ? 'rgba(239, 83, 80, 0.5)' : 'rgba(38, 166, 154, 0.5)',
          }
        }).filter(d => d.value > 0) // 只显示有成交量的数据
        
        volumeSeries.setData(volumeData);

        // 3. 设置标记
        // 确保标记时间在数据范围内
        const dataTimes = new Set(uniqueData.map(d => d.time))
        const validMarkers = props.markers
          .map(m => ({
            ...m,
            time: formatTime(m.time)
          }))
          .filter(m => m.time && dataTimes.has(m.time))
        
        if (validMarkers.length > 0) {
          candlestickSeries.setMarkers(validMarkers.map(m => ({
            time: m.time,
            position: m.position as any,
            color: m.color,
            shape: m.shape as any,
            text: m.text,
          })))
        }
      }
    }

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
    if (props.lines && props.lines.length > 0) {
      // 获取所有数据的时间集合（用于过滤线数据）
      const allDataTimes = new Set<string>()
      if (props.data && props.data.length > 0) {
        props.data.forEach(d => {
          if (d.time) allDataTimes.add(d.time)
        })
      }
      // 如果只有线数据没有K线数据，则使用线数据的时间
      if (allDataTimes.size === 0 && props.lines.length > 0) {
        props.lines.forEach(line => {
          line.data.forEach(d => {
            if (d.time) allDataTimes.add(d.time)
          })
        })
      }
      
      props.lines.forEach(line => {
        if (!chart || !line.data || line.data.length === 0) {
          console.warn('Skipping line series:', line.name, 'data length:', line.data?.length);
          return;
        }
        
        // lightweight-charts v5 使用 addSeries API
        const lineSeries = chart.addSeries(LineSeries, {
          color: line.color,
          lineWidth: line.lineWidth || 2,
          priceScaleId: line.priceScaleId || 'right',
          title: line.name,
        }) as any;
        
        // 格式化时间
        const formatTime = (time: string): string => {
          if (!time) return ''
          if (/^\d{4}-\d{2}-\d{2}$/.test(time)) {
            return time
          }
          const date = new Date(time)
          if (isNaN(date.getTime())) return ''
          const year = date.getFullYear()
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          return `${year}-${month}-${day}`
        }

        // Ensure line data is also sorted and valid
        const sortedLineData = [...line.data]
           .map(d => ({
             ...d,
             time: formatTime(d.time)
           }))
           .filter(d => d.time && (allDataTimes.size === 0 || allDataTimes.has(d.time)))
           .sort((a, b) => {
             const timeA = new Date(a.time).getTime()
             const timeB = new Date(b.time).getTime()
             return timeA - timeB
           });

        const uniqueLineData = sortedLineData.filter((item, index, self) =>
           index === self.findIndex((t) => (t.time === item.time))
        ).map(d => {
          const value = Number(d.value)
          return {
            time: d.time,
            value: isNaN(value) ? 0 : value
          }
        }).filter(d => d.time && !isNaN(d.value)); // 移除 value > 0 的限制，允许负值
        
        console.log(`Line series "${line.name}": ${uniqueLineData.length} data points`);
        
        if (uniqueLineData.length > 0) {
          lineSeries.setData(uniqueLineData);
          lineSeriesMap.set(line.name, lineSeries);
        } else {
          console.warn(`Line series "${line.name}" has no valid data points`);
        }
      });
    }
    
    // 适配内容并确保正确显示
    if (chart) {
      const timeScale = chart.timeScale()
      timeScale.fitContent()
      
      // 如果数据更新，延迟一下再适配，确保数据已完全设置
      if (props.data && props.data.length > 0) {
        setTimeout(() => {
          if (chart) {
            timeScale.fitContent()
          }
        }, 100)
      }
    }
    
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
    if (chart) {
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
    }
    // 延迟更新数据，确保DOM已更新
    nextTick(() => {
      updateChartData();
    });
  }
}, { deep: true, immediate: false });

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
