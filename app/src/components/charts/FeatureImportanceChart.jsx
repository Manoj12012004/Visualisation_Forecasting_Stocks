import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

const FeatureImportanceChart = ({ data, height = 300 }) => {
  if (!data || data.length === 0) {
    return <div className="text-center text-slate-400 py-10">No feature importance data available</div>;
  }

  // Sort data by importance descending for better visualization
  const sortedData = [...data].sort((a, b) => b.importance - a.importance).slice(0, 10); // Top 10

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <BarChart
          data={sortedData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" domain={[0, 'auto']} hide />
          <YAxis 
            dataKey="feature" 
            type="category" 
            width={100} 
            tick={{ fontSize: 12, fill: '#64748b' }}
          />
          <Tooltip 
            formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Importance']}
            contentStyle={{ borderRadius: '4px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={index < 3 ? '#4f46e5' : '#94a3b8'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FeatureImportanceChart;
