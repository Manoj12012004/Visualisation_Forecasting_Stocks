import { useEffect, useRef, useState } from 'react';
import useWebsocket from '../../hooks/useWebSocket';
import { createChart } from 'lightweight-charts';

// Props: symbol (string), wsUrl factory (optional)
export default function LivePriceChart({ symbol, height = 260 }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const [lastPrice, setLastPrice] = useState(null);

  // Build websocket URL from env base
  const base = process.env.NEXT_PUBLIC_API_BASE || process.env.REACT_APP_API_BASE || '';
  // Backend currently exposes /ws/price/{symbol}
  const wsUrl = base.replace(/^http/, 'ws') + `/ws/price/${symbol}`;

  useWebsocket(wsUrl, {
    onMessage: (msg) => {
      const price = msg?.last_candle?.close;
      if (!seriesRef.current || price == null) return;
      const point = { time: Math.floor(Date.now() / 1000), value: price };
      seriesRef.current.update(point);
      setLastPrice(price);
    }
  }, !!symbol);

  useEffect(() => {
    if (!containerRef.current) return;
    chartRef.current = createChart(containerRef.current, {
      height,
      layout: { background: { type: 'Solid', color: '#ffffff' }, textColor: '#1f2937' },
      grid: { vertLines: { color: '#f1f5f9' }, horzLines: { color: '#f1f5f9' } },
      timeScale: { timeVisible: true, secondsVisible: true }
    });
    seriesRef.current = chartRef.current.addLineSeries({ color: '#2563eb', lineWidth: 2 });
    return () => { chartRef.current?.remove(); };
  }, [symbol, height]);

  return (
    <div className="bg-white rounded shadow p-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold">Live Price - {symbol}</h3>
        <div className="text-xs text-gray-600">{lastPrice ? `₹${lastPrice.toFixed(2)}` : 'Waiting...'}</div>
      </div>
      <div ref={containerRef} />
    </div>
  );
}
