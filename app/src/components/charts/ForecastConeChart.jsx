import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { forecastCone } from '../../services/apiClient';

// Displays forecast cone bands (mid, upper, lower) using area + line series
export default function ForecastConeChart({ symbol, days = 7, confidence = 0.9, height = 260 }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const midRef = useRef(null);
  const upperRef = useRef(null);
  const lowerRef = useRef(null);
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
    midRef.current = chartRef.current.addLineSeries({ color: '#2563eb', lineWidth: 2 });
    upperRef.current = chartRef.current.addLineSeries({ color: '#10b981', lineWidth: 1, lineStyle: 2 });
    lowerRef.current = chartRef.current.addLineSeries({ color: '#ef4444', lineWidth: 1, lineStyle: 2 });
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
      if (!symbol || !midRef.current) return;
      setLoading(true); setError(null);
      try {
        const data = await forecastCone(symbol, { days, confidence });
        const path = data?.path || [];
        const toPoint = (r, key) => {
          const ts = r?.date ? Math.floor(new Date(r.date).getTime() / 1000) : undefined;
          const v = Number(r?.[key]);
          if (!ts || !Number.isFinite(v)) return null;
          return { time: ts, value: v };
        };
        const mid = path.map(r => toPoint(r,'predicted_price') || toPoint(r,'mid')).filter(Boolean);
        const upper = path.map(r => toPoint(r,'upper')).filter(Boolean);
        const lower = path.map(r => toPoint(r,'lower')).filter(Boolean);
        if (!cancelled) {
          midRef.current.setData(mid);
          upperRef.current.setData(upper);
          lowerRef.current.setData(lower);
        }
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load forecast cone');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [symbol, days, confidence]);

  return (
    <div className="bg-white rounded shadow p-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold">Forecast Cone - {symbol}</h3>
        <div className="text-xs text-gray-600">{days} day horizon @ {Math.round(confidence*100)}%</div>
      </div>
      {error && <div className="text-xs text-red-600 mb-2">{error}</div>}
      {loading && <div className="text-xs text-gray-500 mb-2">Loading…</div>}
      <div ref={containerRef} />
    </div>
  );
}
