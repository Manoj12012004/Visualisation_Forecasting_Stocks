import React, { useState } from 'react';

const STOCKS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA'];

function StockSelector({ onSelect }) {
  const [selected, setSelected] = useState(STOCKS[0]);
  return (
    <select
      value={selected}
      onChange={e => {
        setSelected(e.target.value);
        if (onSelect) onSelect(e.target.value);
      }}
    >
      {STOCKS.map(s => (
        <option key={s} value={s}>{s}</option>
      ))}
    </select>
  );
}

export default StockSelector;
