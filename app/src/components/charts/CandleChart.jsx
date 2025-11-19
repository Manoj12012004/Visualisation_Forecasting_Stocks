import React from 'react';
import CandlestickChart from '../charts/CandlestickChart.jsx';

export default function CandleChart({ symbol }) {
  return (
    <CandlestickChart
      symbol={symbol}
      show={{ sma: true, ema: true, bb: false, rsi: true, macd: true, cone: true }}
      options={{ limit: 400, sma_window: 20, ema_window: 20, bb_window: 20, rsi_window: 14, macd_fast: 12, macd_slow: 26, macd_signal: 9, bb_k: 2.0, cone_days: 7, cone_confidence: 0.9 }}
    />
  );
}
