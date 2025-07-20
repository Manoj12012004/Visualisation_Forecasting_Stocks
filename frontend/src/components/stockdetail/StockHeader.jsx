import React, { useEffect, useState } from 'react';
import axios from 'axios';
import api from '../../services/api';

function StockHeader({ symbol }) {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    api.get(`/stocks/${symbol}`)
      .then(res => console.log(res.data))
      .catch(() => setInfo(null));
  }, [symbol]);

  if (!info) return <div>Loading...</div>;

  return (
    <div style={{display: "flex", alignItems: "center", gap: 20, margin: "1rem 0"}}>
      {/* <h2>{info.name} ({symbol.toUpperCase()})</h2>
      <span>Last Price: <strong>${info.price}</strong></span>
      <span>Change: <strong style={{color: info.change > 0 ? "green" : "red"}}>{info.change}%</strong></span> */}
    </div>
  );
}

export default StockHeader;
