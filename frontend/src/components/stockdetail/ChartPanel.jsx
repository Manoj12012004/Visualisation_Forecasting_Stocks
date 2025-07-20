import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../../services/api';

export function ChartPanel({ symbol,interval = '1day' }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.get(`/stocks/${symbol}/historical/${interval}`).then(res => {
      if (!res.data.error) {
        const formatted = res.data.map(p => ({
          date: p['date'],
          open: p['open'],
          close: p['close'],
          high: p['high'],
          low: p['low'],
          volume: p['volume']
        }));
        setData(formatted);
      }
    });
  }, [symbol]);
  if (!data) return <div>Loading chart...</div>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="close" stroke="#8884d8" />
      </LineChart>
    </ResponsiveContainer>
  );
}
