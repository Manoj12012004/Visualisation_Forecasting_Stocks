import React, { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { Paper, Typography, Box } from "@mui/material";
import api from "../services/api";

// Modern dark-themed chart styles
const chartStyles = {
  background: "#151c22",
  borderRadius: 12,
  boxShadow: "0 2px 12px rgba(0,0,0,0.42)"
};

const labelStyle = {
  fill: "#b8c7ce",
  fontSize: 12,
};

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <Box sx={{ bgcolor: "#232c34", p: 1, borderRadius: 1 }}>
        <Typography variant="body2" sx={{ color: "#66D9EF" }}>
          {label}
        </Typography>
        <Typography variant="body2" sx={{ color: "#fff" }}>
          ${payload[0].value?.toFixed(2)}
        </Typography>
      </Box>
    );
  }
  return null;
}

export default function LiveChart({ symbol }) {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    api.get(`/stream/start/${symbol}`).catch(() => {});
    const interval = setInterval(async () => {
    const res = await api.get(`/stream/current/${symbol}`);
    setChartData(prev => {
      const updated = [...prev, { time: res.data?.time, price: res.data?.price }];
      return updated.slice(-60); // keep last 60 points
    });
  }, 5000); // every 5 seconds
  return () => clearInterval(interval);
  }, [symbol]);

  return (
    <Paper sx={{ ...chartStyles, p: 3, mt: 2 }}>
      <Typography variant="h6" sx={{ color: "#ffffff" }}>
        {symbol} - Real-Time Stock Chart
      </Typography>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData}>
          <CartesianGrid stroke="#263648" strokeDasharray="4 2" />
          <XAxis dataKey="time" axisLine={false} tickLine={false} style={labelStyle} />
          <YAxis domain={['auto', 'auto']} axisLine={false} tickLine={false} style={labelStyle} />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#465970", strokeWidth: 2 }} />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#5DD991"
            strokeWidth={3}
            dot={false}
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </Paper>
  );
}



// import React, { useEffect, useRef } from 'react';
// import { createChart } from 'lightweight-charts';
// import api from '../services/api';

// export default function LiveCandlestickChart({ symbol }) {
//   const chartContainerRef = useRef();
//   const chartRef = useRef();
//   const candleSeriesRef = useRef();

//   useEffect(() => {
//     chartRef.current = createChart(chartContainerRef.current, {
//       width: chartContainerRef.current.clientWidth,
//       height: 400,
//       layout: {
//         background: { color: '#fff' },
//         textColor: '#000',
//       },
//       grid: {
//         vertLines: { color: '#eee' },
//         horzLines: { color: '#eee' },
//       },
//       timeScale: {
//         timeVisible: true,
//         secondsVisible: true,
//       },
//     });

//     candleSeriesRef.current = chartRef.current.addCandlestickSeries();

//     const ws = new WebSocket(`ws://localhost:8000/ws/candles/${symbol} `);
//     ws.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       console.log("📈 Live OHLC:", data);

//       candleSeriesRef.current.update(data); // data must be { time, open, high, low, close }
//     };

//     return () => {
//       ws.close();
//       chartRef.current.remove();
//     };
//   }, [symbol]);

//   return <div ref={chartContainerRef} style={{ width: '100%', height: 400 }} />;
// }
