import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchTechnicalIndicators } from '../../services/apiClient';

export default function TechnicalIndicatorsChart({ symbol, height = 200 }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const signalSeriesRef = useRef(null);
  const histSeriesRef = useRef(null);
  const [type, setType] = useState('RSI'); // RSI, MACD, SMA, EMA

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
      timeScale: { timeVisible: true, secondsVisible: false },
      rightPriceScale: {
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
    });

    if (type === 'RSI') {
      seriesRef.current = chartRef.current.addLineSeries({
        color: '#7c3aed',
        lineWidth: 2,
      });
      // Add 70/30 lines
      chartRef.current.addLineSeries({ color: '#ef4444', lineWidth: 1, lineStyle: 2, priceScaleId: 'right' });
      chartRef.current.addLineSeries({ color: '#10b981', lineWidth: 1, lineStyle: 2, priceScaleId: 'right' });
      // We'll set data for these later or just let them be static if we could (but we need time points)
    } else if (type === 'MACD') {
      // Histogram
      histSeriesRef.current = chartRef.current.addHistogramSeries({
        color: '#26a69a',
        priceFormat: { type: 'volume' },
        priceScaleId: 'right',
      });
      // MACD Line
      seriesRef.current = chartRef.current.addLineSeries({
        color: '#2962FF',
        lineWidth: 2,
      });
      // Signal Line
      signalSeriesRef.current = chartRef.current.addLineSeries({
        color: '#FF6D00',
        lineWidth: 2,
      });
    } else if (type === 'SMA' || type === 'EMA') {
      seriesRef.current = chartRef.current.addLineSeries({
        color: type === 'SMA' ? '#2563eb' : '#f59e0b',
        lineWidth: 2,
      });
    }

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [symbol, height, type]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!symbol || !chartRef.current) return;
      try {
        const data = await fetchTechnicalIndicators(symbol, { limit: 200 });
        const items = data?.items || data?.rows || [];
        
        if (cancelled) return;

        if (type === 'RSI' && seriesRef.current) {
          const points = items.map(i => {
            const time = i?.date ? Math.floor(new Date(i.date).getTime() / 1000) : undefined;
            const value = Number(i?.rsi);
            if (!time || !Number.isFinite(value)) return null;
            return { time, value };
          }).filter(Boolean);
          seriesRef.current.setData(points);
        } else if (type === 'MACD' && seriesRef.current && signalSeriesRef.current && histSeriesRef.current) {
          const macd = [], signal = [], hist = [];
          items.forEach(i => {
            const time = i?.date ? Math.floor(new Date(i.date).getTime() / 1000) : undefined;
            if (!time) return;
            const m = Number(i?.macd);
            const s = Number(i?.macd_signal);
            const h = Number(i?.macd_hist);
            if (Number.isFinite(m)) macd.push({ time, value: m });
            if (Number.isFinite(s)) signal.push({ time, value: s });
            if (Number.isFinite(h)) hist.push({ time, value: h, color: h >= 0 ? '#26a69a' : '#ef5350' });
          });
          seriesRef.current.setData(macd);
          signalSeriesRef.current.setData(signal);
          histSeriesRef.current.setData(hist);
        } else if ((type === 'SMA' || type === 'EMA') && seriesRef.current) {
          const points = items.map(i => {
            const time = i?.date ? Math.floor(new Date(i.date).getTime() / 1000) : undefined;
            const value = Number(i?.[type.toLowerCase()]);
            if (!time || !Number.isFinite(value)) return null;
            return { time, value };
          }).filter(Boolean);
          seriesRef.current.setData(points);
        }
      } catch (e) {
        console.error(e);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [symbol, type]);

  return (
    <div className="bg-white rounded shadow p-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold">Technical Indicators</h3>
        <div className="flex gap-2 text-xs">
          {['RSI', 'MACD', 'SMA', 'EMA'].map(t => (
            <button 
              key={t}
              onClick={() => setType(t)}
              className={`px-2 py-1 rounded ${type === t ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-500 hover:bg-gray-100'}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div ref={containerRef} />
    </div>
  );
}
