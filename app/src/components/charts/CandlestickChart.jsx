import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchTechnicalIndicators, forecastCone } from '../../services/apiClient';

export default function CandlestickChart({ symbol = 'AAPL', show = { sma: true, ema: true, bb: true, rsi: true, macd: true, cone: false }, options = { limit: 400, sma_window: 20, ema_window: 20, bb_window: 20, rsi_window: 14, macd_fast: 12, macd_slow: 26, macd_signal: 9, bb_k: 2.0, cone_days: 7, cone_confidence: 0.9 } }) {
  const refMain = useRef();
  const refRsi = useRef();
  const refMacd = useRef();
  const chartMain = useRef();
  const chartRsi = useRef();
  const chartMacd = useRef();
  const candleSeries = useRef();
  const volumeSeries = useRef();
  const maSeries = useRef([]);
  const bbUpper = useRef();
  const bbLower = useRef();
  const rsiSeries = useRef();
  const macdLineSeries = useRef();
  const macdSignalSeries = useRef();
  const macdHistSeries = useRef();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState([]);
  const coneUpperSeries = useRef();
  const coneLowerSeries = useRef();
  const coneMidSeries = useRef();
  const [cone, setCone] = useState([]);

  useEffect(() => {
    if (!refMain.current || chartMain.current) return;
    chartMain.current = createChart(refMain.current, { width: refMain.current.clientWidth, height: 360, layout: { background: { color: '#ffffff' } } });
    candleSeries.current = chartMain.current.addCandlestickSeries();
    volumeSeries.current = chartMain.current.addHistogramSeries({ color: '#26a69a', priceFormat: { type: 'volume' }, scaleMargins: { top: 0.7, bottom: 0 } });

    const ro = new ResizeObserver(() => {
      try { chartMain.current.applyOptions({ width: refMain.current.clientWidth }); } catch (e) {}
      try { if (chartRsi.current && refRsi.current) chartRsi.current.applyOptions({ width: refRsi.current.clientWidth }); } catch (e) {}
      try { if (chartMacd.current && refMacd.current) chartMacd.current.applyOptions({ width: refMacd.current.clientWidth }); } catch (e) {}
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
    };
  }, []);

  // Lazily create RSI/MACD charts when panels are shown
  useEffect(() => {
    if (show.rsi && refRsi.current && !chartRsi.current) {
      chartRsi.current = createChart(refRsi.current, { width: refRsi.current.clientWidth, height: 120, layout: { background: { color: '#ffffff' } } });
      rsiSeries.current = chartRsi.current.addLineSeries({ color: '#f59e0b', lineWidth: 1.5 });
    }
    if (!show.rsi && chartRsi.current) {
      try { chartRsi.current.remove(); } catch (e) {}
      chartRsi.current = null;
      rsiSeries.current = null;
    }
  }, [show.rsi]);

  useEffect(() => {
    if (show.macd && refMacd.current && !chartMacd.current) {
      chartMacd.current = createChart(refMacd.current, { width: refMacd.current.clientWidth, height: 140, layout: { background: { color: '#ffffff' } } });
      macdLineSeries.current = chartMacd.current.addLineSeries({ color: '#2563eb', lineWidth: 1 });
      macdSignalSeries.current = chartMacd.current.addLineSeries({ color: '#ef4444', lineWidth: 1 });
      macdHistSeries.current = chartMacd.current.addHistogramSeries({ color: '#7c3aed', priceFormat: { type: 'volume' } });
    }
    if (!show.macd && chartMacd.current) {
      try { chartMacd.current.remove(); } catch (e) {}
      chartMacd.current = null;
      macdLineSeries.current = null;
      macdSignalSeries.current = null;
      macdHistSeries.current = null;
    }
  }, [show.macd]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchTechnicalIndicators(symbol, { ...(options||{} ) }).then((resp) => {
      if (cancelled) return;
      setItems(resp.items || []);
      setLoading(false);
    }).catch((e) => { console.error('fetchTechnicalIndicators failed', e); setLoading(false); setItems([]); });
    return () => { cancelled = true; };
  }, [symbol, options]);

  // Fetch prediction cone when toggled
  useEffect(() => {
    let cancelled = false;
    if (!show.cone) { setCone([]); return; }
    const days = (options && options.cone_days) || 7;
    const confidence = (options && options.cone_confidence) || 0.9;
    forecastCone(symbol, { days, confidence }).then((d) => {
      if (cancelled) return;
      const path = d.path || [];
      setCone(path);
    }).catch((e) => { console.error('forecastCone failed', e); setCone([]); });
    return () => { cancelled = true; };
  }, [symbol, show.cone, options]);

  useEffect(() => {
    if (!items.length) return;
    const toTime = (d) => {
      const t = Date.parse(d);
      return Number.isNaN(t) ? Math.floor(Number(d)/1000) : Math.floor(t/1000);
    };

    const candles = items.map(r => ({ time: toTime(r.date), open: r.open, high: r.high, low: r.low, close: r.close }));
    const volumes = items.map(r => ({ time: toTime(r.date), value: r.volume || 0, color: (r.close >= r.open) ? '#22c55e' : '#ef4444' }));
    try {
      if (candleSeries.current) candleSeries.current.setData(candles);
      if (volumeSeries.current) volumeSeries.current.setData(volumes);

      // remove old ma series
      maSeries.current.forEach(s => { try { chartMain.current.removeSeries(s); } catch (e) {} });
      maSeries.current = [];
      if (show.sma) {
        const s = chartMain.current.addLineSeries({ color: '#0ea5e9', lineWidth: 1 });
        s.setData(items.filter(x=>x.sma!=null).map(r => ({ time: toTime(r.date), value: r.sma })));
        maSeries.current.push(s);
      }
      if (show.ema) {
        const e = chartMain.current.addLineSeries({ color: '#22c55e', lineWidth: 1 });
        e.setData(items.filter(x=>x.ema!=null).map(r => ({ time: toTime(r.date), value: r.ema })));
        maSeries.current.push(e);
      }
      if (show.bb) {
        if (bbUpper.current) try { chartMain.current.removeSeries(bbUpper.current); } catch {}
        if (bbLower.current) try { chartMain.current.removeSeries(bbLower.current); } catch {}
        bbUpper.current = chartMain.current.addLineSeries({ color: '#a855f7', lineWidth: 1 });
        bbLower.current = chartMain.current.addLineSeries({ color: '#a855f7', lineWidth: 1 });
        bbUpper.current.setData(items.filter(x=>x.bb_upper!=null).map(r => ({ time: toTime(r.date), value: r.bb_upper })));
        bbLower.current.setData(items.filter(x=>x.bb_lower!=null).map(r => ({ time: toTime(r.date), value: r.bb_lower })));
      } else {
        if (bbUpper.current) try { chartMain.current.removeSeries(bbUpper.current); bbUpper.current = null; } catch {}
        if (bbLower.current) try { chartMain.current.removeSeries(bbLower.current); bbLower.current = null; } catch {}
      }

      if (show.rsi && rsiSeries.current) {
        rsiSeries.current.setData(items.filter(x=>x.rsi!=null).map(r => ({ time: toTime(r.date), value: r.rsi })));
      }
      if (show.macd && macdLineSeries.current && macdSignalSeries.current && macdHistSeries.current) {
        macdLineSeries.current.setData(items.filter(x=>x.macd!=null).map(r => ({ time: toTime(r.date), value: r.macd })));
        macdSignalSeries.current.setData(items.filter(x=>x.macd_signal!=null).map(r => ({ time: toTime(r.date), value: r.macd_signal })));
        macdHistSeries.current.setData(items.filter(x=>x.macd_hist!=null).map(r => ({ time: toTime(r.date), value: r.macd_hist, color: (r.macd_hist||0) >= 0 ? '#22c55e' : '#ef4444' })));
      }

      // Prediction cone overlay
      // Create series if needed
      if (show.cone) {
        if (!coneUpperSeries.current) {
          coneUpperSeries.current = chartMain.current.addLineSeries({ color: '#7c3aed', lineWidth: 1, lineStyle: 2 /* dashed */ });
        }
        if (!coneLowerSeries.current) {
          coneLowerSeries.current = chartMain.current.addLineSeries({ color: '#7c3aed', lineWidth: 1, lineStyle: 2 /* dashed */ });
        }
        if (!coneMidSeries.current) {
          coneMidSeries.current = chartMain.current.addLineSeries({ color: '#7c3aed', lineWidth: 2 });
        }

        const toConeTime = (d) => toTime(d);
        if (Array.isArray(cone) && cone.length) {
          const upper = cone.filter(x=>x.upper!=null).map(p => ({ time: toConeTime(p.date), value: p.upper }));
          const lower = cone.filter(x=>x.lower!=null).map(p => ({ time: toConeTime(p.date), value: p.lower }));
          const mid = cone.filter(x=>pValue(x)!=null).map(p => ({ time: toConeTime(p.date), value: pValue(p) }));
          coneUpperSeries.current.setData(upper);
          coneLowerSeries.current.setData(lower);
          coneMidSeries.current.setData(mid);
        }
      } else {
        // remove cone series if exist
        if (coneUpperSeries.current) { try { chartMain.current.removeSeries(coneUpperSeries.current); } catch {} coneUpperSeries.current = null; }
        if (coneLowerSeries.current) { try { chartMain.current.removeSeries(coneLowerSeries.current); } catch {} coneLowerSeries.current = null; }
        if (coneMidSeries.current) { try { chartMain.current.removeSeries(coneMidSeries.current); } catch {} coneMidSeries.current = null; }
      }
    } catch (e) { console.error('chart setData error', e); }
  }, [items, show.sma, show.ema, show.bb, show.rsi, show.macd, show.cone, cone]);

  function pValue(p){
    if (!p) return null;
    if (p.predicted_price != null) return p.predicted_price;
    if (p.value != null) return p.value;
    return null;
  }

  useEffect(() => {
    // toggle visibility for RSI and MACD series when charts exist
    try {
      if (rsiSeries.current) rsiSeries.current.applyOptions({ visible: !!show.rsi });
      if (macdLineSeries.current) macdLineSeries.current.applyOptions({ visible: !!show.macd });
      if (macdSignalSeries.current) macdSignalSeries.current.applyOptions({ visible: !!show.macd });
      if (macdHistSeries.current) macdHistSeries.current.applyOptions({ visible: !!show.macd });
    } catch (e) {}
  }, [show.rsi, show.macd]);

  return (
    <div className="space-y-2">
      <div className="bg-white border rounded p-2">
        <div ref={refMain} />
      </div>
      {show.rsi && (
        <div className="bg-white border rounded p-2">
          <div ref={refRsi} />
        </div>
      )}
      {show.macd && (
        <div className="bg-white border rounded p-2">
          <div ref={refMacd} />
        </div>
      )}
      {loading && <div className="text-sm text-slate-500">Loading chart…</div>}
    </div>
  );
}
