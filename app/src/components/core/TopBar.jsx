import React from 'react';
import SymbolSearch from './SymbolSearch';
import { FaBell } from 'react-icons/fa';

export default function TopBar({ symbol, onSelectSymbol }) {
  return (
    <div className="sticky top-0 z-20 bg-white border-b px-4 py-2 flex items-center justify-between">
      <div className="text-lg font-semibold">Dashboard</div>
      <div className="flex items-center gap-3">
        <SymbolSearch value={symbol} onSelect={onSelectSymbol} placeholder="Search stocks" />
        <button className="relative p-2 rounded hover:bg-gray-100" title="Notifications">
          <FaBell />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        <div className="w-8 h-8 rounded-full bg-slate-800 text-white grid place-items-center text-sm">U</div>
      </div>
    </div>
  );
}
