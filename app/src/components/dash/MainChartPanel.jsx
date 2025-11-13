import React from 'react';
import { ResponsiveContainer, ComposedChart, XAxis, YAxis, Tooltip, Bar, Line } from 'recharts';

const chartData = [
  { date: 'Mon', open: 174, close: 176, low: 173, high: 177, volume: 12000 },
  { date: 'Tue', open: 176, close: 175, low: 174, high: 177, volume: 15000 },
  // ...add real price data
];

function MainChartPanel() {
  return (
    <div style={{ background: '#fff', padding: 12, borderRadius: 6, marginTop: 8 }}>
      <h3>Candlestick Chart</h3>
      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={chartData}>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="volume" fill="#bdbdbd" yAxisId={1} />
          <Line type="monotone" dataKey="close" stroke="#1e88e5" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
export default MainChartPanel;
