import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function EquityChart({ modelEquity, benchmarkEquity, height = 300 }) {
  // Merge data
  const data = React.useMemo(() => {
    if (!modelEquity || !modelEquity.length) return [];
    const map = new Map();
    modelEquity.forEach(d => map.set(d.date, { date: d.date, model: d.value }));
    if (benchmarkEquity) {
      benchmarkEquity.forEach(d => {
        if (map.has(d.date)) {
          map.get(d.date).benchmark = d.value;
        }
      });
    }
    return Array.from(map.values()).sort((a, b) => new Date(a.date) - new Date(b.date));
  }, [modelEquity, benchmarkEquity]);

  if (!data.length) return <div className="h-full flex items-center justify-center text-slate-400">No data available</div>;

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis 
            dataKey="date" 
            tickFormatter={(str) => new Date(str).toLocaleDateString(undefined, {month:'short', year:'2-digit'})}
            stroke="#94a3b8"
            fontSize={12}
            minTickGap={30}
          />
          <YAxis 
            stroke="#94a3b8"
            fontSize={12}
            tickFormatter={(val) => `$${val.toLocaleString()}`}
            domain={['auto', 'auto']}
          />
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            formatter={(val, name) => [`$${Number(val).toLocaleString(undefined, {maximumFractionDigits: 2})}`, name]}
            labelFormatter={(label) => new Date(label).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          />
          <Legend wrapperStyle={{ paddingTop: '10px' }} />
          <Line type="monotone" dataKey="model" stroke="#4f46e5" strokeWidth={2} name="Strategy Equity" dot={false} activeDot={{ r: 6 }} />
          <Line type="monotone" dataKey="benchmark" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" name="S&P 500 (Benchmark)" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
