/**
 * 日K线数据重采样工具
 * 将日K聚合为周K、月K
 */

import type { ChartData } from '@/components/KlineChart.vue';

/**
 * 获取日期所在周的周一（作为周标识）
 */
function getMondayStr(dateStr: string): string {
  const d = new Date(dateStr);
  const day = d.getDay(); // 0=周日, 1=周一, ...
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(d.getFullYear(), d.getMonth(), diff);
  return monday.toISOString().split('T')[0];
}

/**
 * 将日K数据聚合为周K
 * 以每周第一个交易日开盘价为周开盘，最后一个交易日收盘价为周收盘
 */
export const resampleToWeekly = (data: ChartData[]): ChartData[] => {
  if (data.length === 0) return [];

  // 确保按时间排序
  const sorted = [...data].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

  const weeks: Map<string, ChartData[]> = new Map();

  for (const item of sorted) {
    const monday = getMondayStr(item.time);
    if (!weeks.has(monday)) weeks.set(monday, []);
    weeks.get(monday)!.push(item);
  }

  const result: ChartData[] = [];
  let prevWeekClose: number | null = null;

  for (const [, weekData] of weeks) {
    const first = weekData[0];
    const last = weekData[weekData.length - 1];

    const high = Math.max(...weekData.map(d => d.high));
    const low = Math.min(...weekData.map(d => d.low));
    const volume = weekData.reduce((sum, d) => sum + (d.volume || 0), 0);
    const amount = weekData.reduce((sum, d) => sum + (d.amount || 0), 0);

    let pct_chg: number | undefined;
    if (prevWeekClose !== null && prevWeekClose !== 0) {
      pct_chg = (last.close - prevWeekClose) / prevWeekClose * 100;
    } else if (first.open !== 0) {
      pct_chg = (last.close - first.open) / first.open * 100;
    }

    result.push({
      time: last.time,
      open: first.open,
      high,
      low,
      close: last.close,
      volume,
      amount,
      turnover: last.turnover,
      pct_chg,
    });

    prevWeekClose = last.close;
  }

  return result;
};

/**
 * 将日K数据聚合为月K
 * 以每月第一个交易日开盘价为月开盘，最后一个交易日收盘价为月收盘
 */
export const resampleToMonthly = (data: ChartData[]): ChartData[] => {
  if (data.length === 0) return [];

  const sorted = [...data].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

  const months: Map<string, ChartData[]> = new Map();

  for (const item of sorted) {
    const monthKey = item.time.slice(0, 7); // YYYY-MM
    if (!months.has(monthKey)) months.set(monthKey, []);
    months.get(monthKey)!.push(item);
  }

  const result: ChartData[] = [];
  let prevMonthClose: number | null = null;

  for (const [, monthData] of months) {
    const first = monthData[0];
    const last = monthData[monthData.length - 1];

    const high = Math.max(...monthData.map(d => d.high));
    const low = Math.min(...monthData.map(d => d.low));
    const volume = monthData.reduce((sum, d) => sum + (d.volume || 0), 0);
    const amount = monthData.reduce((sum, d) => sum + (d.amount || 0), 0);

    let pct_chg: number | undefined;
    if (prevMonthClose !== null && prevMonthClose !== 0) {
      pct_chg = (last.close - prevMonthClose) / prevMonthClose * 100;
    } else if (first.open !== 0) {
      pct_chg = (last.close - first.open) / first.open * 100;
    }

    result.push({
      time: last.time,
      open: first.open,
      high,
      low,
      close: last.close,
      volume,
      amount,
      turnover: last.turnover,
      pct_chg,
    });

    prevMonthClose = last.close;
  }

  return result;
};
