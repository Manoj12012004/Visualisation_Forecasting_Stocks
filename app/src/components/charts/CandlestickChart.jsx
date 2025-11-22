import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchRawData, fetchTechnicalIndicators } from '../../services/apiClient';
import useWebSocket from '../../hooks/useWebSocket';

// Props:
// - symbol: ticker string
// - show: { sma, ema, bb, rsi, macd, cone } optional feature flags (unused placeholder for now)
// - options: indicator calculation windows etc.
// - limit: number of rows to load (fallback 5000)
export default function CandlestickChart({ symbol, show = {}, options = {}, limit = 5000, period = '1y', height = 320, live = false }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const smaSeriesRef = useRef(null);
  const emaSeriesRef = useRef(null);
  const bbMidRef = useRef(null);
  const bbUpperRef = useRef(null);
  const bbLowerRef = useRef(null);

  // WebSocket for live updates
  const wsBase = (process.env.REACT_APP_API_BASE || 'http://localhost:8000').replace(/^http/, 'ws');
  const wsUrl = live ? `${wsBase}/ws/price/${symbol}` : null;

  useWebSocket(wsUrl, {
    onMessage: (data) => {
      if (data?.last_candle && candleSeriesRef.current) {
        const c = data.last_candle;
        const time = c.time ? Math.floor(new Date(c.time).getTime() / 1000) : undefined;
        if (time) {
           candleSeriesRef.current.update({
             time,
             open: Number(c.open),
             high: Number(c.high),
             low: Number(c.low),
             close: Number(c.close)
           });
        }
      }
    },
    disabled: !live
  });

  // Init chart
  useEffect(() => {
    if (!containerRef.current) return;
    // Recreate chart on indicator toggle for simplicity
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }
    
    chartRef.current = createChart(containerRef.current, {
      height,
      layout: { background: { type: 'Solid', color: '#ffffff' }, textColor: '#1f2937' },
      grid: { vertLines: { color: '#f1f5f9' }, horzLines: { color: '#f1f5f9' } },
      timeScale: { timeVisible: true, secondsVisible: false }
    });
    candleSeriesRef.current = chartRef.current.addCandlestickSeries({
      upColor: '#16a34a', downColor: '#dc2626', borderUpColor: '#16a34a', borderDownColor: '#dc2626', wickUpColor: '#16a34a', wickDownColor: '#dc2626'
    });
    if (show.sma) smaSeriesRef.current = chartRef.current.addLineSeries({ color: '#6366f1', lineWidth: 2 });
    if (show.ema) emaSeriesRef.current = chartRef.current.addLineSeries({ color: '#f59e0b', lineWidth: 2 });
    if (show.bb) {
      bbMidRef.current = chartRef.current.addLineSeries({ color: '#0ea5e9', lineWidth: 1 });
      bbUpperRef.current = chartRef.current.addLineSeries({ color: '#0ea5e9', lineWidth: 1, lineStyle: 2 });
      bbLowerRef.current = chartRef.current.addLineSeries({ color: '#0ea5e9', lineWidth: 1, lineStyle: 2 });
    }
    
    return () => { 
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [symbol, height, show.sma, show.ema, show.bb]);

  // One-time data load
  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!symbol || !candleSeriesRef.current) return;
      try {
        const raw = await fetchRawData(symbol, { limit, period });
        const rows = raw?.rows || raw?.items || [];
        const candles = rows.map(r => {
          const t = r?.date ? Math.floor(new Date(r.date).getTime() / 1000) : undefined;
          const open = Number(r?.open);
          const high = Number(r?.high);
          const low = Number(r?.low);
          const close = Number(r?.close);
          if (!t || !Number.isFinite(open) || !Number.isFinite(high) || !Number.isFinite(low) || !Number.isFinite(close)) return null;
          return { time: t, open, high, low, close };
        }).filter(Boolean);
        if (!cancelled && candles.length) {
          candleSeriesRef.current.setData(candles);
          if (chartRef.current) chartRef.current.timeScale().fitContent();
        }
        // Optional indicators (simple moving average placeholder)
        if (!cancelled && (show.sma || show.ema || show.bb)) {
          const tech = await fetchTechnicalIndicators(symbol, { limit, period, ...options });
          const items = tech?.items || tech?.rows || [];
          if (show.sma && smaSeriesRef.current) {
            const smaPoints = items.map(i => {
              const t = i?.date ? Math.floor(new Date(i.date).getTime() / 1000) : undefined;
              const v = Number(i?.sma);
              if (!t || !Number.isFinite(v)) return null;
              return { time: t, value: v };
            }).filter(Boolean);
            if (smaPoints.length) smaSeriesRef.current.setData(smaPoints);
          }
          if (show.ema && emaSeriesRef.current) {
            const emaPoints = items.map(i => {
              const t = i?.date ? Math.floor(new Date(i.date).getTime() / 1000) : undefined;
              const v = Number(i?.ema);
              if (!t || !Number.isFinite(v)) return null;
              return { time: t, value: v };
            }).filter(Boolean);
            if (emaPoints.length) emaSeriesRef.current.setData(emaPoints);
          }
          if (show.bb && bbMidRef.current && bbUpperRef.current && bbLowerRef.current) {
            const mid = [], upper = [], lower = [];
            for (const i of items) {
              const t = i?.date ? Math.floor(new Date(i.date).getTime() / 1000) : undefined;
              const m = Number(i?.bb_mid); const u = Number(i?.bb_upper); const l = Number(i?.bb_lower);
              if (!t || !Number.isFinite(m) || !Number.isFinite(u) || !Number.isFinite(l)) continue;
              mid.push({ time: t, value: m });
              upper.push({ time: t, value: u });
              lower.push({ time: t, value: l });
            }
            if (mid.length) bbMidRef.current.setData(mid);
            if (upper.length) bbUpperRef.current.setData(upper);
            if (lower.length) bbLowerRef.current.setData(lower);
          }
        }
      } catch (_) {
        // silent fail
      }
    }
    load();
    return () => { cancelled = true; };
  }, [symbol, limit, period, show.sma, show.ema, show.bb, options]);

  return (
    <div className="bg-white rounded shadow p-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold">Candlesticks - {symbol}</h3>
        <div className="text-xs text-gray-600">Snapshot (Candles{show.sma?'+SMA':''}{show.ema?'+EMA':''}{show.bb?'+Bollinger':''})</div>
      </div>
      <div ref={containerRef} />
    </div>
  );
}
