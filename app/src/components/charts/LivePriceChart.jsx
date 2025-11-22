import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchRawData } from '../../services/apiClient';

// Props: symbol (string)
export default function LivePriceChart({ symbol, height = 260 }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);

  // Static chart placeholder – no live updates or polling.

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
      timeScale: { timeVisible: true, secondsVisible: true }
    });
    seriesRef.current = chartRef.current.addLineSeries({ color: '#2563eb', lineWidth: 2 });
    return () => { 
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [symbol, height]);

  // No polling effect – intentionally left static.
  // One-time historical load
  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!symbol || !seriesRef.current) return;
      try {
        const data = await fetchRawData(symbol, 200); // limit can be adjusted
        const rows = data?.rows || data?.items || [];
        const points = rows
          .map(r => {
            const t = r?.date ? Math.floor(new Date(r.date).getTime() / 1000) : undefined;
            const price = Number(r?.close);
            if (!t || !Number.isFinite(price)) return null;
            return { time: t, value: price };
          })
          .filter(Boolean);
        if (!cancelled && points.length) {
          seriesRef.current.setData(points);
        }
      } catch (_) {
        // silent fail
      }
    }
    load();
    return () => { cancelled = true; };
  }, [symbol]);

  return (
    <div className="bg-white rounded shadow p-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold">Price - {symbol}</h3>
        <div className="text-xs text-gray-600">Static snapshot (loaded once)</div>
      </div>
      <div ref={containerRef} />
    </div>
  );
}
