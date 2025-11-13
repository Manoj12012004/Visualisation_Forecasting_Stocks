import { use, useEffect, useState } from "react";
import api from "../../services/api";

function TopStocks() {
  const [stocks, setStocks] = useState(null);
  const fetchMetrics = async () => {
      api.get('/stocks/').then(res=>{
        console.log("Stocks fetched:", res);
        setStocks(res)}).catch(err => {
        console.error("Error fetching stocks:", err);
    })
  }
  useEffect(()=>{
    fetchMetrics();
  })
  const metrics = [
    // { label: 'Portfolio Value', value: '$52,100' },
    // { label: '1D Gain/Loss', value: '+$310' },
    { label: 'Top Gainer', value: 'TSLA (+3.5%)' },
    { label: 'Top Loser', value: 'AAPL (-1.1%)' },
  ];
  return (
    <div style={{ display: 'flex', gap: 20, margin: '1rem 0' }}>
      {/* {metrics.map(m => (
        <div key={m.label} style={{
          background: '#e0e7ef', padding: 12, borderRadius: 6, minWidth: 120,
        }}>
          <div style={{ fontWeight: 700 }}>{m.value}</div>
          <div style={{ fontSize: 14 }}>{m.label}</div>
        </div>
      ))} */}
      {stocks}
    </div>
  );
}
export default TopStocks;
