import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

function LivePriceChart({symbol}) {
  const [data, setData] = useState([]);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/price_feed");

    ws.onopen=()=>{
      ws.send(JSON.stringify({'symbol':symbol}))
    }
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      console.log("Live price received:", msg);

      if (msg.symbol && msg.price) {
        setData(prev => [
          ...prev.slice(-19),
          {
            name: new Date().toLocaleTimeString(),
            price: parseFloat(msg.price),
          },
        ]);
      }
    };

    ws.onclose = () => console.log("WebSocket closed");
    ws.onerror = (e) => console.error("WebSocket error", e);

    return () => ws.close();
  }, []);

  return (
    <div className="p-6">
      <h2>Live AAPL Price</h2>
      <LineChart width={600} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis domain={['auto', 'auto']} />
        <Tooltip />
        <Line type="monotone" dataKey="price" stroke="#82ca9d" dot={false} />
      </LineChart>
    </div>
  );
}

export default LivePriceChart;
