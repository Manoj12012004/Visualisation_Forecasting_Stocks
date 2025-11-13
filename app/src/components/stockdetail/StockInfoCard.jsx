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
    { label: "Market Cap", value: formatNumber(stats['market_cap']) },
    { label: "P/E Ratio", value: stats['pe_ratio'] ? stats['pe_ratio'].toFixed(2) : 'N/A' },
    { label: "Volume", value: formatNumber(stats['volume']) },
    { label: "Dividend", value: stats['dividend'] || 'N/A' },
  ];

  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: 16,
      marginBottom: 16,
    }}>
      {cards.map((card) => (
        <div
          key={card.label}
          style={{
            background: '#f0f4f8',
            padding: '12px 16px',
            borderRadius: 10,
            minWidth: 140,
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            flex: '1 1 140px'
          }}
        >
          <div style={{ fontSize: 12, color: '#78909c' }}>{card.label}</div>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>{card.value}</div>
        </div>
      ))}
    </div>
  );
}

function formatNumber(number) {
  if (!number) return 'N/A';
  const num = typeof number === 'string' ? parseFloat(number) : number;
  return isNaN(num) ? 'N/A' : num.toLocaleString('en-US');
}

export default StockInfoCards;
