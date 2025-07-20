import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const trendData = [
  { date: 'Mon', SP: 5100 },
  { date: 'Tue', SP: 5200 },
  { date: 'Wed', SP: 5180 },
  { date: 'Thu', SP: 5280 },
  { date: 'Fri', SP: 5245 },
];

function GlobalTrendsPanel() {
  return (
    <div style={{ width:"50vw",background: '#f5f5fa', padding: 12, borderRadius: 6, marginBottom: 20 }}>
      <h3>Market Trends</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={trendData}>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="SP" stroke="#1976d2" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
export default GlobalTrendsPanel;
