import React, { useEffect, useState } from 'react';
import { fetchHeatmap, listStocks } from '../../services/apiClient';

function tileColor(v) {
  if (v == null) return 'bg-gray-200 text-gray-700';
  if (v > 0.03) return 'bg-green-600 text-white';
  if (v > 0.0) return 'bg-green-200 text-green-800';
  if (v < -0.03) return 'bg-red-600 text-white';
  return 'bg-red-200 text-red-800';
}

export default function MarketHeatmap() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const syms = await listStocks();
        const { items } = await fetchHeatmap(syms);
        if (mounted) setItems(items || []);
      } finally { if (mounted) setLoading(false); }
    }
    load();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="bg-white border rounded p-4">
      <div className="font-semibold mb-2">Market Heatmap (1D)</div>
      {loading ? <div className="text-sm text-gray-500">Loading…</div> : null}
      <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
        {items.map(({ symbol, change_pct }) => (
          <div key={symbol} className={`rounded p-2 text-center text-xs ${tileColor(change_pct)}`}>
            <div className="font-semibold">{symbol}</div>
            <div>{change_pct == null ? '—' : `${(change_pct * 100).toFixed(1)}%`}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
