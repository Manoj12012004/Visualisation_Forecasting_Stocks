import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchRawData } from '../../services/apiClient';

// Realized volatility (rolling std of returns) and volume overlay
export default function VolatilityChart({ symbol, limit = 250, volWindow = 20, height = 200 }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const volSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!containerRef.current) return;
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
    volSeriesRef.current = chartRef.current.addLineSeries({ color: '#9333ea', lineWidth: 2 });
    volumeSeriesRef.current = chartRef.current.addHistogramSeries({ color: '#94a3b8', priceFormat: { type: 'volume' }, scaleMargins: { top: 0.7, bottom: 0 } });
    return () => { 
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [symbol, height]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!symbol || !volSeriesRef.current) return;
      setLoading(true); setError(null);
      try {
        const raw = await fetchRawData(symbol, limit);
        const rows = raw?.rows || [];
        const points = [];
        const volPoints = [];
        const closes = [];
        rows.forEach(r => {
          const ts = r?.date ? Math.floor(new Date(r.date).getTime() / 1000) : undefined;
          const close = Number(r?.close);
          const volume = Number(r?.volume);
          if (!ts || !Number.isFinite(close)) return;
          closes.push({ ts, close });
          points.push({ time: ts, value: volume });
        });
        // realized volatility on pct returns
        const returns = [];
        for (let i = 1; i < closes.length; i++) {
          const ret = (closes[i].close - closes[i-1].close) / closes[i-1].close;
          returns.push({ ts: closes[i].ts, ret });
        }
        for (let i = 0; i < returns.length; i++) {
          const windowSlice = returns.slice(Math.max(0, i - volWindow + 1), i + 1);
          const std = Math.sqrt(windowSlice.reduce((acc, r) => acc + Math.pow(r.ret,2), 0) / Math.max(1, windowSlice.length));
          const ts = returns[i].ts;
          volPoints.push({ time: ts, value: std });
        }
        if (!cancelled) {
          volumeSeriesRef.current.setData(points);
          volSeriesRef.current.setData(volPoints);
        }
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load volatility');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [symbol, limit, volWindow]);

  return (
    <div className="bg-white rounded shadow p-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold">Volatility & Volume - {symbol}</h3>
        <div className="text-xs text-gray-600">Rolling {volWindow}d std</div>
      </div>
      {error && <div className="text-xs text-red-600 mb-2">{error}</div>}
      {loading && <div className="text-xs text-gray-500 mb-2">Loading…</div>}
      <div ref={containerRef} />
    </div>
  );
}
