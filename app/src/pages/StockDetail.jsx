import React, { useEffect, useState } from 'react';
import Layout from '../components/core/layout';
import CandleChart from '../components/charts/CandleChart';
import PredictionHistoryChart from '../components/charts/PredictionHistoryChart';
import { useParams } from 'react-router-dom';
import { forecastNext, forecastCone } from '../services/apiClient';

export default function StockDetail() {
  const params = useParams();
  const [symbol, setSymbol] = useState(params.symbol || 'AAPL');
  useEffect(() => { setSymbol(params.symbol || 'AAPL'); }, [params.symbol]);

  return (
    <Layout>
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white rounded border p-3">
          <div className="font-semibold mb-2">{symbol} — Candlestick</div>
          <CandleChart symbol={symbol} />
          <div className="mt-4">
            <div className="font-semibold mb-2">Historical Accuracy (last 30)</div>
            <PredictionHistoryChart symbol={symbol} />
          </div>
        </div>
        <div className="bg-white rounded border p-3">
          <CrystalBall symbol={symbol} />
        </div>
      </div>
    </Layout>
  );
}

function CrystalBall({ symbol }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const next = await forecastNext(symbol, 1);
        const cone = await forecastCone(symbol, { days: 1, confidence: 0.85 });
        if (cancelled) return;
        const p = (next.path && next.path[0]) || {};
        const c = (cone.path && cone.path[0]) || {};
        const badge = p.probability >= 0.7 ? { txt: 'STRONG BUY', cls: 'bg-emerald-100 text-emerald-700' }
                    : p.probability >= 0.55 ? { txt: 'BUY', cls: 'bg-emerald-50 text-emerald-700' }
                    : { txt: 'SELL', cls: 'bg-rose-100 text-rose-700' };
        setData({
          predicted: p.predicted_price,
          confidenceText: `We are 85% confident the price will be between ${fmt(c.lower)} and ${fmt(c.upper)}.`,
          badge,
          probability: p.probability,
        });
      } catch { setData(null); }
    })();
    return () => { cancelled = true; };
  }, [symbol]);

  if (!data) return <div>Loading prediction…</div>;
  return (
    <div>
      <div className="font-semibold mb-2">Crystal Ball</div>
      <div className="text-3xl font-bold">{fmt(data.predicted)}</div>
      <div className="text-sm text-slate-600 mt-2">{data.confidenceText}</div>
      <div className="mt-3">
        <span className={`px-2 py-1 rounded-full text-xs ${data.badge.cls}`}>{data.badge.txt}</span>
      </div>
      <div className="text-xs text-slate-500 mt-1">Probability up: {(data.probability*100).toFixed(1)}%</div>
      <div className="mt-4 text-sm text-slate-500">Sentiment: disabled in this build.</div>
    </div>
  );
}

function fmt(x){
  if (x == null || Number.isNaN(Number(x))) return '-';
  try { return '$'+Number(x).toFixed(2); } catch { return String(x); }
}
