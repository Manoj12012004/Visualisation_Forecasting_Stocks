import { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, Tooltip, XAxis, YAxis, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

// Fetch recent predictions and actual prices (assuming endpoint returns array with timestamp, predicted_next_price, actual_price)
export default function PredictionHistoryChart({ symbol }) {
  const [rows, setRows] = useState([]);
  const base = process.env.NEXT_PUBLIC_API_BASE || process.env.REACT_APP_API_BASE || '';

  useEffect(() => {
    let active = true;
    async function load() {
      if (!symbol) return;
      try {
        // Try cleaner path first then duplicated fallback
        const paths = [ `${base}/predictions/history`, `${base}/predictions/predictions/history` ];
        let data;
        for (const p of paths) {
          try {
            const res = await axios.get(p, { params: { symbol, limit: 50 } });
            data = res.data;
            break;
          } catch(e){ /* next */ }
        }
        if (!data) return; // all failed
        if (!active) return;
        const list = Array.isArray(data.items) ? data.items : data; // support both shapes
        const mapped = list.map(r => ({
          time: new Date(r.prediction_time).toLocaleTimeString(),
          predicted: r.predicted_return != null && r.current_price ? (r.current_price * (1 + r.predicted_return)) : null,
          actual: null // actual price not provided in current API; placeholder
        })).filter(row => row.predicted != null).slice(-50);
        setRows(mapped);
      } catch (e) {
        console.error(e);
      }
    }
    load();
    const id = setInterval(load, 15000);
    return () => { active = false; clearInterval(id); };
  }, [symbol, base]);

  if (!symbol) return null;

  return (
    <div className="bg-white rounded shadow p-3 mt-4">
      <h3 className="text-sm font-semibold mb-2">Prediction vs Actual (Recent)</h3>
      <div style={{ width: '100%', height: 240 }}>
        <ResponsiveContainer>
          <LineChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#f1f5f9" />
            <XAxis dataKey="time" interval={rows.length > 12 ? Math.floor(rows.length/8) : 0} />
            <YAxis domain={['auto', 'auto']} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="predicted" stroke="#2563eb" dot={false} name="Predicted" />
            {rows.some(r => r.actual) && <Line type="monotone" dataKey="actual" stroke="#dc2626" dot={false} name="Actual" />}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
