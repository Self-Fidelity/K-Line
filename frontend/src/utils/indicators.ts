/**
 * Technical Indicators Calculation Utilities
 */

import type { ChartData } from '@/components/KlineChart.vue';

export interface IndicatorData {
  time: string;
  value: number;
  color?: string;
}

/**
 * Calculate Simple Moving Average (MA)
 */
export const calculateMA = (dayCount: number, data: ChartData[]): IndicatorData[] => {
  const result: IndicatorData[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount - 1) {
      result.push({ time: data[i].time, value: NaN });
      continue;
    }
    let sum = 0;
    for (let j = 0; j < dayCount; j++) {
      sum += data[i - j].close;
    }
    result.push({
      time: data[i].time,
      value: sum / dayCount,
    });
  }
  return result;
};

/**
 * Calculate Exponential Moving Average (EMA)
 */
export const calculateEMA = (dayCount: number, data: ChartData[]): IndicatorData[] => {
  const result: IndicatorData[] = [];
  if (data.length === 0) return result;

  const k = 2 / (dayCount + 1);
  let ema = data[0].close;
  
  result.push({ time: data[0].time, value: ema });

  for (let i = 1; i < data.length; i++) {
    ema = data[i].close * k + ema * (1 - k);
    result.push({ time: data[i].time, value: ema });
  }
  return result;
};

/**
 * Calculate Bollinger Bands (BOLL)
 */
export const calculateBOLL = (period: number, stdDevMultiplier: number, data: ChartData[]) => {
  const upper: IndicatorData[] = [];
  const mid: IndicatorData[] = [];
  const lower: IndicatorData[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      upper.push({ time: data[i].time, value: NaN });
      mid.push({ time: data[i].time, value: NaN });
      lower.push({ time: data[i].time, value: NaN });
      continue;
    }

    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close;
    }
    const ma = sum / period;

    let sumSqDiff = 0;
    for (let j = 0; j < period; j++) {
      sumSqDiff += Math.pow(data[i - j].close - ma, 2);
    }
    const stdDev = Math.sqrt(sumSqDiff / period);

    mid.push({ time: data[i].time, value: ma });
    upper.push({ time: data[i].time, value: ma + stdDev * stdDevMultiplier });
    lower.push({ time: data[i].time, value: ma - stdDev * stdDevMultiplier });
  }

  return { upper, mid, lower };
};

/**
 * Calculate MACD
 * Standard parameters: 12, 26, 9
 */
export const calculateMACD = (shortPeriod: number, longPeriod: number, signalPeriod: number, data: ChartData[]) => {
  const dif: IndicatorData[] = [];
  const dea: IndicatorData[] = [];
  const macd: IndicatorData[] = [];

  if (data.length === 0) return { dif, dea, macd };

  const shortK = 2 / (shortPeriod + 1);
  const longK = 2 / (longPeriod + 1);
  const signalK = 2 / (signalPeriod + 1);

  let shortEma = data[0].close;
  let longEma = data[0].close;
  let deaValue = 0;

  // Initialize with 0 or first values
  dif.push({ time: data[0].time, value: 0 });
  dea.push({ time: data[0].time, value: 0 });
  macd.push({ time: data[0].time, value: 0 });

  for (let i = 1; i < data.length; i++) {
    shortEma = data[i].close * shortK + shortEma * (1 - shortK);
    longEma = data[i].close * longK + longEma * (1 - longK);
    
    const difValue = shortEma - longEma;
    deaValue = difValue * signalK + deaValue * (1 - signalK);
    const macdValue = 2 * (difValue - deaValue);

    dif.push({ time: data[i].time, value: difValue });
    dea.push({ time: data[i].time, value: deaValue });
    macd.push({ 
        time: data[i].time, 
        value: macdValue,
        color: macdValue >= 0 ? '#ef5350' : '#26a69a' 
    });
  }

  return { dif, dea, macd };
};

/**
 * Calculate KDJ
 * Standard parameters: 9, 3, 3
 */
export const calculateKDJ = (period: number, kPeriod: number, dPeriod: number, data: ChartData[]) => {
  const kLine: IndicatorData[] = [];
  const dLine: IndicatorData[] = [];
  const jLine: IndicatorData[] = [];

  let k = 50;
  let d = 50;

  for (let i = 0; i < data.length; i++) {
    // Need lookback for RSV
    let rsv = 50;
    if (i >= period - 1) {
        let low = data[i].low;
        let high = data[i].high;
        for (let j = 0; j < period; j++) {
            low = Math.min(low, data[i - j].low);
            high = Math.max(high, data[i - j].high);
        }
        if (high - low !== 0) {
            rsv = (data[i].close - low) / (high - low) * 100;
        }
    }

    k = (2 * k + rsv) / 3; 
    d = (2 * d + k) / 3;   
    const j = 3 * k - 2 * d;

    kLine.push({ time: data[i].time, value: k });
    dLine.push({ time: data[i].time, value: d });
    jLine.push({ time: data[i].time, value: j });
  }

  return { k: kLine, d: dLine, j: jLine };
};

/**
 * Calculate RSI
 * Standard: 14
 */
export const calculateRSI = (period: number, data: ChartData[]): IndicatorData[] => {
  const result: IndicatorData[] = [];
  
  if (data.length < period + 1) {
      for(const d of data) result.push({ time: d.time, value: NaN });
      return result;
  }

  let gainSum = 0;
  let lossSum = 0;
  
  for (let i = 1; i <= period; i++) {
      const change = data[i].close - data[i-1].close;
      if (change > 0) gainSum += change;
      else lossSum -= change;
  }

  let avgGain = gainSum / period;
  let avgLoss = lossSum / period;

  for(let i = 0; i <= period; i++) {
      result.push({ time: data[i].time, value: NaN }); 
  }
  
  let rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
  let rsi = 100 - (100 / (1 + rs));
  result[period].value = rsi;

  for (let i = period + 1; i < data.length; i++) {
      const change = data[i].close - data[i-1].close;
      let gain = 0;
      let loss = 0;
      if (change > 0) gain = change;
      else loss = -change;

      avgGain = (avgGain * (period - 1) + gain) / period;
      avgLoss = (avgLoss * (period - 1) + loss) / period;

      rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      rsi = 100 - (100 / (1 + rs));
      
      result.push({ time: data[i].time, value: rsi });
  }

  return result;
};

/**
 * Calculate WR (Williams %R)
 * Standard: 14
 * Formula: (Hn - C) / (Hn - Ln) * -100
 */
export const calculateWR = (period: number, data: ChartData[]): IndicatorData[] => {
    const result: IndicatorData[] = [];
    
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            result.push({ time: data[i].time, value: NaN });
            continue;
        }
        
        let high = data[i].high;
        let low = data[i].low;
        for (let j = 0; j < period; j++) {
            high = Math.max(high, data[i - j].high);
            low = Math.min(low, data[i - j].low);
        }
        
        let wr = -50; // Default
        if (high - low !== 0) {
            wr = (high - data[i].close) / (high - low) * -100;
        }
        
        result.push({ time: data[i].time, value: wr });
    }
    return result;
};

/**
 * Calculate CCI (Commodity Channel Index)
 * Standard: 14
 * Formula: (TP - MA) / (0.015 * MD)
 * TP = (H+L+C)/3
 */
export const calculateCCI = (period: number, data: ChartData[]): IndicatorData[] => {
    const result: IndicatorData[] = [];
    const tps = data.map(d => (d.high + d.low + d.close) / 3);
    
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            result.push({ time: data[i].time, value: NaN });
            continue;
        }
        
        let sum = 0;
        for(let j=0; j<period; j++) sum += tps[i-j];
        const ma = sum / period;
        
        let mdSum = 0;
        for(let j=0; j<period; j++) mdSum += Math.abs(tps[i-j] - ma);
        const md = mdSum / period;
        
        let cci = 0;
        if (md !== 0) {
            cci = (tps[i] - ma) / (0.015 * md);
        }
        
        result.push({ time: data[i].time, value: cci });
    }
    return result;
};

/**
 * Calculate BIAS
 * Standard: [6, 12, 24] but here simplified to single line calculator
 * Formula: (C - MA) / MA * 100
 */
export const calculateBIAS = (period: number, data: ChartData[]): IndicatorData[] => {
    const result: IndicatorData[] = [];
    
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            result.push({ time: data[i].time, value: NaN });
            continue;
        }
        
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j].close;
        }
        const ma = sum / period;
        
        const bias = (data[i].close - ma) / ma * 100;
        result.push({ time: data[i].time, value: bias });
    }
    return result;
};

/**
 * Calculate OBV (On-Balance Volume)
 * Formula: Cumulative volume (+ if close > prev close, - if close < prev close)
 */
export const calculateOBV = (data: ChartData[]): IndicatorData[] => {
    const result: IndicatorData[] = [];
    let obv = 0;
    
    // First point
    if (data.length > 0) {
        result.push({ time: data[0].time, value: obv });
    }
    
    for (let i = 1; i < data.length; i++) {
        const curr = data[i].close;
        const prev = data[i-1].close;
        const vol = data[i].volume || 0;
        
        if (curr > prev) obv += vol;
        else if (curr < prev) obv -= vol;
        // else obv stays same
        
        result.push({ time: data[i].time, value: obv });
    }
    return result;
};
