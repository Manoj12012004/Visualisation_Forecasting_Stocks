import React, { useMemo, useState } from 'react';
import Layout from '../components/core/layout';
import DonutChart from '../components/charts/DonutChart';
import MetricCard from '../components/core/MetricCard';

export default function Portfolio() {
  const [holdings] = useState(() => {
    // simple local stub
    const saved = localStorage.getItem('paper_holdings');
    return saved ? JSON.parse(saved) : [
      { symbol: 'AAPL', qty: 10, avg: 150, price: 175 },
      { symbol: 'GOOGL', qty: 2, avg: 120, price: 130 },
    ];
  });

  const cash = 20000; // stub
  const totals = useMemo(() => {
    const value = holdings.reduce((s,h)=> s + h.qty * (h.price||h.avg||0), 0) + cash;
    const invested = holdings.reduce((s,h)=> s + h.qty * (h.avg||0), 0);
    const pnl = value - (invested + cash);
    return { value, cash, pnl };
  }, [holdings]);

  const alloc = useMemo(() => {
    const total = holdings.reduce((s,h)=> s + h.qty * (h.price||h.avg||0), 0) + cash;
    const rows = holdings.map(h => ({ name: h.symbol, value: h.qty * (h.price||h.avg||0) }));
    rows.push({ name: 'Cash', value: cash });
    return rows.map(r => ({ ...r, pct: total? (r.value/total)*100: 0 }));
  }, [holdings]);

  return (
    <Layout>
      <div className="space-y-4">
        <div className="grid md:grid-cols-3 gap-4">
          <MetricCard label="Total Account Value" value={fmt(totals.value)} />
          <MetricCard label="Available Cash" value={fmt(totals.cash)} />
          <MetricCard label="Total P/L" value={<span className={totals.pnl>=0?'text-emerald-700':'text-rose-700'}>{`${totals.pnl>=0?'+':''}${fmt(totals.pnl)}`}</span>} />
        </div>

        <div className="grid lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 bg-white rounded border p-4">
            <div className="font-semibold mb-2">Holdings</div>
            <table className="min-w-full text-sm">
              <thead><tr>
                <th className="text-left p-1">Symbol</th>
                <th className="text-right p-1">Qty</th>
                <th className="text-right p-1">Avg Buy</th>
                <th className="text-right p-1">Current</th>
                <th className="text-right p-1">Net P/L</th>
                <th className="text-right p-1">Actions</th>
              </tr></thead>
              <tbody>
              {holdings.map((h,i)=>{
                const cur = h.price||h.avg||0;
                const pl = (cur - (h.avg||0)) * h.qty;
                return (
                  <tr key={i} className="odd:bg-slate-50">
                    <td className="p-1">{h.symbol}</td>
                    <td className="p-1 text-right">{h.qty}</td>
                    <td className="p-1 text-right">{fmt(h.avg)}</td>
                    <td className="p-1 text-right">{fmt(cur)}</td>
                    <td className={`p-1 text-right ${pl>=0?'text-emerald-600':'text-rose-600'}`}>{pl>=0?'+':''}{fmt(pl)}</td>
                    <td className="p-1 text-right">
                      <button className="px-2 py-0.5 border rounded text-xs mr-1">Buy More</button>
                      <button className="px-2 py-0.5 border rounded text-xs">Sell</button>
                    </td>
                  </tr>
                );
              })}
              </tbody>
            </table>
          </div>
          <div className="bg-white rounded border p-4">
            <div className="font-semibold mb-2">Allocation</div>
            <DonutChart data={alloc} />
          </div>
        </div>
      </div>
    </Layout>
  );
}

function fmt(x){
  if (x == null || Number.isNaN(Number(x))) return '-';
  try { return '$'+Number(x).toLocaleString(undefined, { maximumFractionDigits: 2 }); } catch { return String(x); }
}
