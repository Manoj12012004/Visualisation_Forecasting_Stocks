import React, { useState } from 'react';
import Layout from '../components/core/layout';
import SymbolSearch from '../components/core/SymbolSearch';
import LivePriceChart from '../components/charts/LivePriceChart';

export default function RealtimePage() {
  const [symbol, setSymbol] = useState('AAPL');
  return (
    <Layout>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Realtime</h1>
          <SymbolSearch value={symbol} onSelect={setSymbol} />
        </div>
        <LivePriceChart symbol={symbol} height={320} />
      </div>
    </Layout>
  );
}
