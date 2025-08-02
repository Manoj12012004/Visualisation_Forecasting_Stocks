import React, { useEffect, useState } from 'react';
import api from '../../services/api';

function StockHeader({ symbol }) {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    api.get(`/stocks/${symbol}`)
      .then(res => setInfo(res.data))
      .catch(() => setInfo(null));
  }, [symbol]);

  if (!info) return <div>Loading...</div>;

  const priceChange = parseFloat(info.change);
  const priceChangePct = parseFloat(info.percent_change);
  const isUp = priceChange > 0;

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      gap: 8,
      margin: "1.3rem 0",
      border: "1px solid #e0e0e0",
      borderRadius: 10,
      padding: "18px 22px",
      background: "#f7faff"
    }}>
      <div style={{display: "flex", alignItems: "center", gap: 14}}>
        <h2 style={{margin: 0}}>{info.name} <span style={{color: "#546e7a"}}>({info.symbol})</span></h2>
        <span style={{
          padding: "3px 10px",
          borderRadius: 5,
          background: info.is_market_open ? "#c8e6c9" : "#ffcdd2",
          color: info.is_market_open ? "#2e7d32" : "#d32f2f",
          fontWeight: 600
        }}>
          {info.is_market_open ? "Market Open" : "Market Closed"}
        </span>
        <span style={{color: "#789"}}>{info.exchange} / {info.mic_code}</span>
      </div>
      <div style={{display: "flex", alignItems: "center", gap: 22, flexWrap: "wrap"}}>
        <span>
          <strong style={{fontSize: 26}}>${Number(info.close).toFixed(2)}</strong>
          <span style={{
            color: isUp ? "#388e3c" : "#d32f2f",
            marginLeft: 8,
            fontWeight: 600
          }}>
            {isUp ? '▲' : '▼'} {priceChange.toFixed(2)} ({priceChangePct.toFixed(2)}%)
          </span>
        </span>
        <span>Prev Close: <strong>${Number(info.previous_close).toFixed(2)}</strong></span>
        <span>Open: <strong>${Number(info.open).toFixed(2)}</strong></span>
        <span>High: <strong>${Number(info.high).toFixed(2)}</strong></span>
        <span>Low: <strong>${Number(info.low).toFixed(2)}</strong></span>
        <span>Date: <strong>{info.datetime}</strong></span>
      </div>
      <div style={{display: "flex", alignItems: "center", gap: 22, flexWrap: "wrap"}}>
        <span>Volume: <strong>{Number(info.volume).toLocaleString()}</strong></span>
        <span>Avg Volume: <strong>{Number(info.average_volume).toLocaleString()}</strong></span>
        <span>
          52W Range: <span style={{fontWeight: 500}}>${info.fifty_two_week.low} - ${info.fifty_two_week.high}</span>
        </span>
      </div>
    </div>
  );
}

export default StockHeader;
