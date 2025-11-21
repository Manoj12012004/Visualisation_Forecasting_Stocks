// src/components/charts/CandlestickChart.jsx
import React, { useEffect, useRef, useState, useMemo } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchTechnicalIndicators, forecastCone } from '../../services/apiClient';
import './TradingViewStyles.css';
import useWebsocket from '../../hooks/useWebSocket';

export default function CandlestickChart({
  symbol = 'AAPL',
  show = { sma: true, ema: true, bb: false, rsi: false, macd: false, cone: true },
  options = {
    limit: 400,
    sma_window: 20,
    ema_window: 20,
    bb_window: 20,
    rsi_window: 14,
    macd_fast: 12,
    macd_slow: 26,
    macd_signal: 9,
    bb_k: 2.0,
    cone_days: 7,
    cone_confidence: 0.9,
  },
  live = false,
  enableControls = true,
}) {
  const refMain = useRef(null);
  const refTooltip = useRef(null);
  const refRsi = useRef(null);
  const refMacd = useRef(null);

  const chartMain = useRef(null);
  const chartRsi = useRef(null);
  const chartMacd = useRef(null);

  const candleSeries = useRef(null);
  const volumeSeries = useRef(null);

  // arrays of additional series
  const maSeries = useRef([]);
  const bbUpper = useRef(null);
  const bbLower = useRef(null);

  const rsiSeries = useRef(null);
  const macdLineSeries = useRef(null);
  const macdSignalSeries = useRef(null);
  const macdHistSeries = useRef(null);

  const coneUpperSeries = useRef(null);
  const coneLowerSeries = useRef(null);
  const coneMidSeries = useRef(null);
  const liveSeries = useRef(null);
  const tooltipHandlerRef = useRef(null);

  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState([]);
  const [cone, setCone] = useState([]);
  const [range, setRange] = useState('6M'); // default visible range similar to TradingView
  const [localShow, setLocalShow] = useState(show);

  useEffect(() => { setLocalShow(show); }, [show, symbol]);

  // utility: robust time conversion -> return epoch seconds (lightweight-charts expects number seconds)
  const toTime = (d) => {
    if (d == null) return null;
    // if already a number and looks like seconds (<= 1e10), assume seconds; if > 1e12 assume ms
    if (typeof d === 'number') {
      if (d > 1e12) return Math.floor(d / 1000);
      return Math.floor(d);
    }
    // if it's a string:
    // try parse ISO
    const parsed = Date.parse(d);
    if (!Number.isNaN(parsed)) return Math.floor(parsed / 1000);
    // fallback: try numeric string
    const n = Number(d);
    if (!Number.isNaN(n)) {
      if (n > 1e12) return Math.floor(n / 1000);
      return Math.floor(n);
    }
    return null;
  };

  // init main chart + volume
  useEffect(() => {
    if (!refMain.current || chartMain.current) return;

    chartMain.current = createChart(refMain.current, {
      width: refMain.current.clientWidth,
      height: 420,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#1e293b',
      },
      grid: {
        vertLines: { color: '#f1f5f9' },
        horzLines: { color: '#f1f5f9' },
      },
      crosshair: { mode: 1 },
      timeScale: { rightOffset: 8, barSpacing: 7, borderColor: '#e2e8f0' },
      rightPriceScale: { borderColor: '#e2e8f0' },
    });

    candleSeries.current = chartMain.current.addCandlestickSeries({
      upColor: '#16a34a',
      downColor: '#dc2626',
      borderUpColor: '#16a34a',
      borderDownColor: '#dc2626',
      wickUpColor: '#16a34a',
      wickDownColor: '#dc2626',
    });
    volumeSeries.current = chartMain.current.addHistogramSeries({
      priceFormat: { type: 'volume' },
      scaleMargins: { top: 0.75, bottom: 0 },
      priceScaleId: '',
    });

    // create tooltip container
    const tp = document.createElement('div');
    tp.className = 'tv-tooltip';
    refTooltip.current = tp;
    refMain.current.appendChild(tp);

    const ro = new ResizeObserver(() => {
      try {
        if (refMain.current && chartMain.current) {
          chartMain.current.applyOptions({ width: refMain.current.clientWidth });
        }
        if (refRsi.current && chartRsi.current) {
          chartRsi.current.applyOptions({ width: refRsi.current.clientWidth });
        }
        if (refMacd.current && chartMacd.current) {
          chartMacd.current.applyOptions({ width: refMacd.current.clientWidth });
        }
      } catch (e) {
        // ignore resize application errors
      }
    });

    ro.observe(refMain.current);
    if (refRsi.current) ro.observe(refRsi.current);
    if (refMacd.current) ro.observe(refMacd.current);

    return () => {
      try { ro.disconnect(); } catch (e) {}
      try { if (chartMain.current) chartMain.current.remove(); } catch (e) {}
      try { if (chartRsi.current) chartRsi.current.remove(); } catch (e) {}
      try { if (chartMacd.current) chartMacd.current.remove(); } catch (e) {}
      chartMain.current = null;
      chartRsi.current = null;
      chartMacd.current = null;
      candleSeries.current = null;
      volumeSeries.current = null;
      rsiSeries.current = null;
      macdLineSeries.current = null;
      macdSignalSeries.current = null;
      macdHistSeries.current = null;
      if (refTooltip.current) {
        try { refTooltip.current.remove(); } catch (_) {}
        refTooltip.current = null;
      }
    };
  }, []);

  // lazily create RSI chart
  useEffect(() => {
    if (localShow.rsi && refRsi.current && !chartRsi.current) {
      chartRsi.current = createChart(refRsi.current, {
        width: refRsi.current.clientWidth,
        height: 120,
        layout: { background: { color: '#ffffff' } },
      });
      rsiSeries.current = chartRsi.current.addLineSeries({ lineWidth: 1.5 });
    }
    if (!localShow.rsi && chartRsi.current) {
      try { chartRsi.current.remove(); } catch (e) {}
      chartRsi.current = null;
      rsiSeries.current = null;
    }
  }, [localShow.rsi]);

  // lazily create MACD chart
  useEffect(() => {
    if (localShow.macd && refMacd.current && !chartMacd.current) {
      chartMacd.current = createChart(refMacd.current, {
        width: refMacd.current.clientWidth,
        height: 140,
        layout: { background: { color: '#ffffff' } },
      });
      macdLineSeries.current = chartMacd.current.addLineSeries({ lineWidth: 1 });
      macdSignalSeries.current = chartMacd.current.addLineSeries({ lineWidth: 1 });
      macdHistSeries.current = chartMacd.current.addHistogramSeries({ priceFormat: { type: 'volume' } });
    }
    if (!localShow.macd && chartMacd.current) {
      try { chartMacd.current.remove(); } catch (e) {}
      chartMacd.current = null;
      macdLineSeries.current = null;
      macdSignalSeries.current = null;
      macdHistSeries.current = null;
    }
  }, [localShow.macd]);

  // fetch technical indicators
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchTechnicalIndicators(symbol, options)
      .then((resp) => {
        if (cancelled) return;
        setItems(resp.items || []);
        setLoading(false);
      })
      .catch((e) => {
        console.error('fetchTechnicalIndicators failed', e);
        if (!cancelled) {
          setItems([]);
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [symbol, options]);

  // fetch prediction cone
  useEffect(() => {
    let cancelled = false;
      if (!localShow.cone) {
      setCone([]);
      return () => { cancelled = true; };
    }
    const days = options?.cone_days || 7;
    const confidence = options?.cone_confidence || 0.9;
    forecastCone(symbol, { days, confidence })
      .then((d) => {
        if (cancelled) return;
        setCone(d.path || d || []);
      })
      .catch((e) => {
        console.error('forecastCone failed', e);
        if (!cancelled) setCone([]);
      });
    return () => { cancelled = true; };
  }, [symbol, localShow.cone, options]);

  // helper to extract predicted/mid value
  function pValue(p) {
    if (!p) return null;
    if (p.predicted_price != null) return p.predicted_price;
    if (p.value != null) return p.value;
    if (p.mid != null) return p.mid;
    return null;
  }

  // memo filtered items based on selected range
  const displayItems = useMemo(() => {
    if (!items || !items.length) return [];
    if (range === 'ALL') return items;
    const end = new Date();
    let start;
    switch (range) {
      case '1M': start = new Date(end); start.setMonth(end.getMonth() - 1); break;
      case '3M': start = new Date(end); start.setMonth(end.getMonth() - 3); break;
      case '6M': start = new Date(end); start.setMonth(end.getMonth() - 6); break;
      case 'YTD': start = new Date(end.getFullYear(), 0, 1); break;
      case '1Y': start = new Date(end); start.setFullYear(end.getFullYear() - 1); break;
      default: return items;
    }
    return items.filter(r => {
      const d = new Date(r.date);
      return d >= start && d <= end;
    });
  }, [items, range]);

  // update chart data when items or cone change
  useEffect(() => {
    if (!items || !items.length) {
      // clear data if required
      try {
        if (candleSeries.current) candleSeries.current.setData([]);
        if (volumeSeries.current) volumeSeries.current.setData([]);
      } catch (e) {}
      return;
    }

    try {
      const candles = displayItems.map((r) => {
        const t = toTime(r.date);
        return { time: t, open: r.open, high: r.high, low: r.low, close: r.close };
      });
      const volumes = displayItems.map((r) => {
        const t = toTime(r.date);
        return { time: t, value: r.volume || 0, color: (r.close >= r.open) ? '#22c55e' : '#ef4444' };
      });

      if (candleSeries.current) candleSeries.current.setData(candles);
      if (volumeSeries.current) volumeSeries.current.setData(volumes);

      // remove old MA series
      maSeries.current.forEach((s) => {
        try { if (chartMain.current && s) chartMain.current.removeSeries(s); } catch (e) {}
      });
      maSeries.current = [];

      if (localShow.sma) {
        const s = chartMain.current.addLineSeries({ lineWidth: 1 });
        s.setData(displayItems.filter(x => x.sma != null).map(r => ({ time: toTime(r.date), value: r.sma })));
        maSeries.current.push(s);
      }

      if (localShow.ema) {
        const e = chartMain.current.addLineSeries({ lineWidth: 1 });
        e.setData(displayItems.filter(x => x.ema != null).map(r => ({ time: toTime(r.date), value: r.ema })));
        maSeries.current.push(e);
      }

      // Bollinger Bands
      if (localShow.bb) {
        if (bbUpper.current) { try { chartMain.current.removeSeries(bbUpper.current); } catch (e) {} bbUpper.current = null; }
        if (bbLower.current) { try { chartMain.current.removeSeries(bbLower.current); } catch (e) {} bbLower.current = null; }

        bbUpper.current = chartMain.current.addLineSeries({ lineWidth: 1, lineStyle: 1 });
        bbLower.current = chartMain.current.addLineSeries({ lineWidth: 1, lineStyle: 1 });

        bbUpper.current.setData(displayItems.filter(x => x.bb_upper != null).map(r => ({ time: toTime(r.date), value: r.bb_upper })));
        bbLower.current.setData(displayItems.filter(x => x.bb_lower != null).map(r => ({ time: toTime(r.date), value: r.bb_lower })));
      } else {
        if (bbUpper.current) { try { chartMain.current.removeSeries(bbUpper.current); } catch (e) {} bbUpper.current = null; }
        if (bbLower.current) { try { chartMain.current.removeSeries(bbLower.current); } catch (e) {} bbLower.current = null; }
      }

      // RSI
      if (localShow.rsi && rsiSeries.current) {
        rsiSeries.current.setData(displayItems.filter(x => x.rsi != null).map(r => ({ time: toTime(r.date), value: r.rsi })));
      }

      // MACD
      if (localShow.macd && macdLineSeries.current && macdSignalSeries.current && macdHistSeries.current) {
        macdLineSeries.current.setData(displayItems.filter(x => x.macd != null).map(r => ({ time: toTime(r.date), value: r.macd })));
        macdSignalSeries.current.setData(displayItems.filter(x => x.macd_signal != null).map(r => ({ time: toTime(r.date), value: r.macd_signal })));
        macdHistSeries.current.setData(displayItems.filter(x => x.macd_hist != null).map(r => ({ time: toTime(r.date), value: r.macd_hist, color: (r.macd_hist || 0) >= 0 ? '#22c55e' : '#ef4444' })));
      }

      // Prediction cone overlay
      if (localShow.cone) {
        if (!coneUpperSeries.current) coneUpperSeries.current = chartMain.current.addLineSeries({ lineWidth: 1, lineStyle: 2 });
        if (!coneLowerSeries.current) coneLowerSeries.current = chartMain.current.addLineSeries({ lineWidth: 1, lineStyle: 2 });
        if (!coneMidSeries.current) coneMidSeries.current = chartMain.current.addLineSeries({ lineWidth: 2 });

        const upper = cone.filter(x => x && (x.upper != null)).map(p => ({ time: toTime(p.date), value: p.upper }));
        const lower = cone.filter(x => x && (x.lower != null)).map(p => ({ time: toTime(p.date), value: p.lower }));
        const mid = cone.filter(x => pValue(x) != null).map(p => ({ time: toTime(p.date), value: pValue(p) }));

        coneUpperSeries.current.setData(upper);
        coneLowerSeries.current.setData(lower);
        coneMidSeries.current.setData(mid);
      } else {
        if (coneUpperSeries.current) { try { chartMain.current.removeSeries(coneUpperSeries.current); } catch (e) {} coneUpperSeries.current = null; }
        if (coneLowerSeries.current) { try { chartMain.current.removeSeries(coneLowerSeries.current); } catch (e) {} coneLowerSeries.current = null; }
        if (coneMidSeries.current) { try { chartMain.current.removeSeries(coneMidSeries.current); } catch (e) {} coneMidSeries.current = null; }
      }

      // Live price overlay line
      if (live) {
        if (!liveSeries.current) {
          liveSeries.current = chartMain.current.addLineSeries({ color: '#2563eb', lineWidth: 2 });
        }
      } else {
        if (liveSeries.current) { try { chartMain.current.removeSeries(liveSeries.current); } catch (e) {} liveSeries.current = null; }
      }
      // rebuild tooltip mapping
      if (refTooltip.current) refTooltip.current.style.display = 'none';
      if (chartMain.current) {
        if (tooltipHandlerRef.current) {
          try { chartMain.current.unsubscribeCrosshairMove(tooltipHandlerRef.current); } catch (_) {}
        }
        const handler = (param) => {
          if (!param || !param.time || !refTooltip.current) {
            if (refTooltip.current) refTooltip.current.style.display = 'none';
            return;
          }
          const data = candles.find(c => c.time === param.time);
          if (!data) {
            refTooltip.current.style.display = 'none';
            return;
          }
          refTooltip.current.style.display = 'block';
          refTooltip.current.innerHTML = `
            <div class="tv-tooltip-row"><span>${symbol}</span> <strong>${new Date(data.time * 1000).toLocaleDateString()}</strong></div>
            <div class="tv-tooltip-row">O: ${data.open.toFixed(2)} H: ${data.high.toFixed(2)} L: ${data.low.toFixed(2)} C: ${data.close.toFixed(2)}</div>
          `;
          const rect = refMain.current.getBoundingClientRect();
          const x = (param.point && param.point.x) ? param.point.x : 0;
          refTooltip.current.style.left = Math.min(Math.max(x - 60, 0), rect.width - 140) + 'px';
        };
        chartMain.current.subscribeCrosshairMove(handler);
        tooltipHandlerRef.current = handler;
      }
    } catch (e) {
      console.error('chart setData error', e);
    }
  }, [items, displayItems, localShow.sma, localShow.ema, localShow.bb, localShow.rsi, localShow.macd, localShow.cone, cone, range, symbol, live]);

  // toggle visibility for RSI and MACD if already created
  useEffect(() => {
    try {
      if (rsiSeries.current) rsiSeries.current.applyOptions({ visible: !!localShow.rsi });
      if (macdLineSeries.current) macdLineSeries.current.applyOptions({ visible: !!localShow.macd });
      if (macdSignalSeries.current) macdSignalSeries.current.applyOptions({ visible: !!localShow.macd });
      if (macdHistSeries.current) macdHistSeries.current.applyOptions({ visible: !!localShow.macd });
    } catch (e) {}
  }, [localShow.rsi, localShow.macd]);

  // WebSocket live updates (overlay line)
  const origin = (process.env.NEXT_PUBLIC_API_BASE || process.env.REACT_APP_API_BASE || (typeof window !== 'undefined' ? window.location.origin : ''));
  const wsUrl = origin ? origin.replace(/^http/, 'ws') + `/ws/price/${symbol}` : '';
  useWebsocket(wsUrl, {
    onMessage: (msg) => {
      if (!live || !liveSeries.current) return;
      const price = msg?.last_candle?.close ?? msg?.price ?? null;
      if (price == null) return;
      liveSeries.current.update({ time: Math.floor(Date.now() / 1000), value: Number(price) });
    }
  }, live && !!symbol);

  return (
    <div className="space-y-2">
      <div className="bg-white border rounded p-2 relative">
        <div className="flex items-center justify-between mb-2 text-xs font-medium gap-3">
          <div className="flex items-center gap-2">
          {['1M','3M','6M','YTD','1Y','ALL'].map(r => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={"px-2 py-1 rounded border " + (range === r ? 'bg-slate-800 text-white' : 'bg-white hover:bg-slate-100')}
            >{r}</button>
          ))}
          </div>
          {enableControls && (
            <div className="flex items-center gap-3">
              {['sma','ema','bb','rsi','macd','cone'].map(k => (
                <label key={k} className="flex items-center gap-1 cursor-pointer">
                  <input type="checkbox" checked={!!localShow[k]} onChange={(e)=> setLocalShow(v => ({...v, [k]: e.target.checked}))} />
                  <span className="uppercase">{k}</span>
                </label>
              ))}
            </div>
          )}
        </div>
        <div ref={refMain} />
      </div>

      {localShow.rsi && (
        <div className="bg-white border rounded p-2">
          <div ref={refRsi} />
        </div>
      )}

      {localShow.macd && (
        <div className="bg-white border rounded p-2">
          <div ref={refMacd} />
        </div>
      )}

      {loading && <div className="text-sm text-slate-500">Loading chart…</div>}
    </div>
  );
}
