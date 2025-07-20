import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../../services/api';

function IndicatorsPanel({ symbol }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    api.get(`/stocks/${symbol}/technical`)
      .then(res => {
        console.log(res.data);
        setData(res.data)})
      .catch(() => setData([]));
  }, [symbol]);

  return (
    <div style={{ background: "#fafbfc", borderRadius: 8, padding: 14, marginBottom: 20 }}>
      <h4>Technical Indicators</h4>
      <ResponsiveContainer width="100%" height={230}>
        <LineChart data={data}>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line name="Close" dataKey="close" stroke="#1976d2" dot={false} />
          <Line name="SMA 20" dataKey="sma20" stroke="#43a047" dot={false}/>
          <Line name="RSI" dataKey="rsi" stroke="#e53935" dot={false}/>
          {/* Add more overlays as needed */}
        </LineChart>
      </ResponsiveContainer>
      {JSON.stringify(data)}
    </div>
  );
}

export default IndicatorsPanel;
