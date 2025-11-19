import React, { useEffect, useState } from 'react';
import { listStocks, fetchRawData } from '../../services/apiClient';

export default function WatchlistTable() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      try {
        const symbols = await listStocks();
        const data = await Promise.all(symbols.map(async s => {
          try {
            const d = await fetchRawData(s, 2);
            const last = (d.rows||[]).slice(-1)[0] || {};
            const prev = (d.rows||[]).slice(-2)[0] || {};
            const cp = Number(last.close || 0);
            const pc = Number(prev.close || 0);
            const ch = pc ? ((cp-pc)/pc)*100 : 0;
            return { symbol: s, price: cp, change: ch };
          } catch { return { symbol: s, price: null, change: null }; }
        }));
        if (!cancelled) setRows(data);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="bg-white rounded border p-4">
      <div className="font-semibold mb-2">Your Watchlist</div>
      {loading ? <div className="text-sm text-slate-500">Loading…</div> : (
        <table className="min-w-full text-sm">
          <thead><tr>
            <th className="text-left p-1">Ticker</th>
            <th className="text-right p-1">Current Price</th>
            <th className="text-right p-1">Day Change %</th>
          </tr></thead>
          <tbody>
          {rows.map(r => (
            <tr key={r.symbol} className="odd:bg-slate-50">
              <td className="p-1">{r.symbol}</td>
              <td className="p-1 text-right">{fmt(r.price)}</td>
              <td className={`p-1 text-right ${r.change>=0?'text-emerald-600':'text-rose-600'}`}>{r.change!=null? r.change.toFixed(2)+'%': '-'}</td>
            </tr>
          ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function fmt(x){
  if (x == null || Number.isNaN(Number(x))) return '-';
  try { return Number(x).toLocaleString(); } catch { return String(x); }
}
