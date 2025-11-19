import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#10b981'];

export default function DonutChart({ data = [] }) {
  const total = data.reduce((s, x) => s + (x.value || 0), 0) || 1;
  const rows = data.map(d => ({ name: d.name, value: d.value }));
  return (
    <div className="h-56">
      <ResponsiveContainer>
        <PieChart>
          <Pie data={rows} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
            {rows.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v, n) => [`${((v/total)*100).toFixed(1)}%`, n]} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
