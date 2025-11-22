// src/components/CandleChart.jsx
import React, { useState } from 'react';
import CandlestickChart from '../charts/CandlestickChart';

export default function CandleChart({ symbol, live = false, controls = true }) {
  const [show, setShow] = useState({ sma: controls, ema: controls, bb: false });
  const [period, setPeriod] = useState('1Y');
  
  const toggle = key => setShow(s => ({ ...s, [key]: !s[key] }));

  const periods = {
    '1M': '1mo',
    '3M': '3mo',
    '6M': '6mo',
    '1Y': '1y'
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        {controls ? (
          <div className="flex flex-wrap gap-3 text-xs">
            {['sma','ema','bb'].map(k => (
              <label key={k} className="flex items-center gap-1 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={!!show[k]}
                  onChange={() => toggle(k)}
                  className="accent-blue-600"
                />
                <span className="uppercase font-medium">{k}</span>
              </label>
            ))}
          </div>
        ) : <div />}
        
        <div className="flex bg-slate-100 rounded p-0.5">
          {Object.keys(periods).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-2 py-0.5 text-xs font-medium rounded ${
                period === p 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <CandlestickChart
        symbol={symbol}
        show={controls ? show : {}}
        live={live}
        period={periods[period]}
        options={{ sma_window: 20, ema_window: 20, bb_window: 20, bb_k: 2.0 }}
      />
    </div>
  );
}
