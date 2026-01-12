/**
 * Financial Statistics Utilities
 */

interface KlineData {
  date?: string;
  time?: string;
  close: number;
  [key: string]: any;
}

export const calculateStatistics = (data: KlineData[]) => {
  if (!data || data.length === 0) {
    return {
      totalReturn: 0,
      maxDrawdown: 0,
      startPrice: 0,
      endPrice: 0
    };
  }

  // Ensure sorted by date/time
  const sortedData = [...data].sort((a, b) => {
    const t1 = a.date || a.time || '';
    const t2 = b.date || b.time || '';
    return new Date(t1).getTime() - new Date(t2).getTime();
  });

  const startPrice = sortedData[0].close;
  const endPrice = sortedData[sortedData.length - 1].close;
  
  // Calculate Total Return
  const totalReturn = startPrice !== 0 ? ((endPrice - startPrice) / startPrice) * 100 : 0;

  // Calculate Max Drawdown
  let maxDrawdown = 0;
  let peak = -Infinity;

  for (const candle of sortedData) {
    if (candle.close > peak) {
      peak = candle.close;
    }
    
    const drawdown = peak !== 0 ? ((peak - candle.close) / peak) * 100 : 0;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }

  return {
    totalReturn: Number(totalReturn.toFixed(2)),
    maxDrawdown: Number(maxDrawdown.toFixed(2)),
    startPrice,
    endPrice
  };
};
