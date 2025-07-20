import React, { useEffect, useState } from 'react';
import api from '../../services/api';

function StockInfoCards({ symbol }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get(`/stocks/${symbol}`)
      .then(res => setStats(res.data))
      .catch(() => setStats(null));
  }, [symbol]);

  if (!stats) return null;

  const cards = [
    { label: "Market Cap", value: stats['market_cap'] },
    { label: "P/E Ratio", value: stats['pe_ratio'] },
    { label: "Volume", value: stats['volume'] },
    { label: "Dividend", value: stats['dividend']},
  ];

  return (
    <div style={{display: "flex", gap: 16, marginBottom: 12}}>
      {cards.map(card => (
        <div key={card.label} style={{
          background: "#eef1f5", padding: 12, borderRadius: 8, minWidth: 110
        }}>
          <small>{card.label}</small><br />
          <strong>{card.value}</strong>
        </div>
      ))}
    </div>
  );
}

export default StockInfoCards;
