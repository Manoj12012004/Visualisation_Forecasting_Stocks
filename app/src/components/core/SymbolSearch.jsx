import React, { useState, useEffect, useMemo } from 'react';
import { listStocks } from '../../services/apiClient';

export default function SymbolSearch({ onSelect, value: externalValue, placeholder = 'Enter symbol (e.g. AAPL)' }) {
  const [value, setValue] = useState(externalValue || '');
  const [all, setAll] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => { listStocks().then(setAll).catch(() => {}); }, []);
  useEffect(() => { if (externalValue) setValue(externalValue); }, [externalValue]);

  const suggestions = useMemo(() => {
    if (!value) return all.slice(0, 5);
    return all.filter(s => s.toUpperCase().startsWith(value.toUpperCase())).slice(0, 8);
  }, [value, all]);

  function choose(sym) {
    setValue(sym);
    setOpen(false);
    if (onSelect) onSelect(sym);
  }

  return (
    <div className="relative inline-block" style={{ minWidth: 220 }}>
      <input
        value={value}
        onChange={(e) => { setValue(e.target.value.toUpperCase()); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 120)}
        placeholder={placeholder}
        className="border px-2 py-1 rounded w-full text-sm"
        autoComplete="off"
      />
      <button
        onClick={() => value && choose(value)}
        disabled={!value}
        className="ml-2 bg-slate-700 hover:bg-slate-800 disabled:opacity-40 text-white px-3 py-1 rounded text-sm"
      >Select</button>
      {open && suggestions.length > 0 && (
        <div className="absolute z-10 mt-1 w-full bg-white border rounded shadow text-sm max-h-56 overflow-auto">
          {suggestions.map(s => (
            <div
              key={s}
              onMouseDown={(e) => { e.preventDefault(); choose(s); }}
              className="px-2 py-1 cursor-pointer hover:bg-slate-100 flex justify-between"
            >
              <span>{s}</span>
              {value === s && <span className="text-xs text-slate-500">match</span>}
            </div>
          ))}
          {value && suggestions.length === 0 && <div className="px-2 py-1 text-slate-500">No matches</div>}
        </div>
      )}
    </div>
  );
}