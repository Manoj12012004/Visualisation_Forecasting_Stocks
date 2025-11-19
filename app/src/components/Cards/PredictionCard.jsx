import React, { useEffect, useState } from 'react';
import { listStocks, forecastNext } from '../../services/apiClient';

export default function PredictionCard() {
  const [pick, setPick] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      try {
        const symbols = await listStocks();
        // evaluate first 5 to keep it fast
        const batch = symbols.slice(0, 5);
        const preds = await Promise.all(batch.map(async s => {
          try {
            const d = await forecastNext(s, 1);
            const p = (d.path && d.path[0]) || {};
            return { symbol: s, prob: Number(p.probability || 0), price: Number(p.predicted_price || 0) };
          } catch { return { symbol: s, prob: 0, price: 0 }; }
        }));
        preds.sort((a,b)=> b.prob - a.prob);
        if (!cancelled) setPick(preds[0]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <div className="bg-white rounded border p-4">AI Pick of the Day: Loading…</div>;
  if (!pick) return <div className="bg-white rounded border p-4">AI Pick of the Day: No data</div>;

  const badge = pick.prob >= 0.7 ? { txt: 'STRONG BUY', cls: 'bg-emerald-100 text-emerald-700' }
              : pick.prob >= 0.55 ? { txt: 'BUY', cls: 'bg-emerald-50 text-emerald-700' }
              : { txt: 'SELL', cls: 'bg-rose-100 text-rose-700' };

  return (
    <div className="bg-white rounded border p-4">
      <div className="text-xs text-slate-500 mb-1">AI Pick of the Day</div>
      <div className="flex items-center justify-between">
        <div className="text-xl font-semibold">{pick.symbol}</div>
        <span className={`px-2 py-1 rounded-full text-xs ${badge.cls}`}>{badge.txt}</span>
      </div>
      <div className="text-sm text-slate-600 mt-1">Probability up: {(pick.prob*100).toFixed(1)}%</div>
    </div>
  );
}
