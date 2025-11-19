import React, { useEffect, useMemo, useState } from 'react';
import { fetchHeatmap, fetchRawData } from '../../services/apiClient';

export default function MarketSnapshot() {
  const [heat, setHeat] = useState([]);
  const [series, setSeries] = useState([]);

  useEffect(() => {
    fetchHeatmap().then(setHeat).catch(() => setHeat([]));
    // Use AAPL as a proxy "index" for now
    fetchRawData('AAPL', 60).then((d) => {
      const rows = d.rows || [];
      setSeries(rows.map(r => ({ t: r.timestamp || r.date || r.time, c: Number(r.close || r.Close || r.CLOSE) })));
    }).catch(() => setSeries([]));
  }, []);

  const advancers = useMemo(() => {
    const pos = heat.filter(x => (x.change || x.pct_change || 0) > 0).length;
    return heat.length ? Math.round((pos / heat.length) * 100) : 50;
  }, [heat]);

  const topGainers = useMemo(() => [...heat].sort((a,b)=> (b.change||b.pct_change||0) - (a.change||a.pct_change||0)).slice(0,5), [heat]);
  const topLosers = useMemo(() => [...heat].sort((a,b)=> (a.change||a.pct_change||0) - (b.change||b.pct_change||0)).slice(0,5), [heat]);

  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <div className="bg-white rounded border p-4">
        <div className="font-semibold mb-2">Market Index (proxy)</div>
        <MiniLine data={series} />
      </div>
      <div className="bg-white rounded border p-4">
        <div className="font-semibold mb-2">Market Breadth</div>
        <div className="text-sm text-slate-600 mb-2">% of advancing symbols</div>
        <BreadthGauge value={advancers} />
      </div>
      <div className="bg-white rounded border p-4">
        <div className="font-semibold mb-2">Top Movers</div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-slate-500 mb-1">Gainers</div>
            {topGainers.map((x) => (
              <div key={x.symbol} className="flex justify-between text-sm py-1 border-b">
                <span>{x.symbol}</span><span className="text-emerald-600">{(x.change||x.pct_change||0).toFixed(2)}%</span>
              </div>
            ))}
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Losers</div>
            {topLosers.map((x) => (
              <div key={x.symbol} className="flex justify-between text-sm py-1 border-b">
                <span>{x.symbol}</span><span className="text-rose-600">{(x.change||x.pct_change||0).toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniLine({ data }) {
  return (
    <div className="h-28 w-full bg-slate-50 rounded grid place-items-center text-slate-400 text-sm">
      {/* Minimal sparkline placeholder without extra deps */}
      {data && data.length ? <span>{data.length} points</span> : <span>No data</span>}
    </div>
  );
}

function BreadthGauge({ value=50 }) {
  return (
    <div className="w-full">
      <div className="h-3 bg-slate-200 rounded">
        <div className="h-3 bg-emerald-600 rounded" style={{ width: `${value}%` }}></div>
      </div>
      <div className="text-sm mt-1 font-medium">{value}% Advancers</div>
    </div>
  );
}
