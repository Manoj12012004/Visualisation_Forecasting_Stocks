import React, { useState } from 'react';
import Layout from '../components/core/layout';
import SymbolSearch from '../components/core/SymbolSearch';
import MetricCard from '../components/core/MetricCard';
import AIExplainBlock from '../components/learning/AIExplainBlock';
import { backtestSimple } from '../services/apiClient';

export default function BacktestPage() {
  const [symbol, setSymbol] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function runSim() {
    if (!symbol) return;
    setLoading(true);
    try {
      const data = await backtestSimple(symbol, { initial: 10000 });
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <h2 style={{ marginBottom: 8 }}>Backtest</h2>
      <p style={{ marginTop: 0, color: '#475569' }}>Choose a symbol and run a simple strategy simulation to understand performance and risk.</p>
      <SymbolSearch onSelect={setSymbol} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <div>Selected: <strong>{symbol || 'None'}</strong></div>
        <button disabled={!symbol || loading} onClick={runSim} style={btn}>{loading ? 'Running...' : 'Run Backtest'}</button>
      </div>

      {result && (
        <>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <MetricCard label="Final Balance" value={`$${fmt(result.final_balance)}`} explKey="backtest_metrics" />
            <MetricCard
              label="Net Profit"
              value={<span className={(Number(result.profit)||0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}>{`${(Number(result.profit)||0) >= 0 ? '+' : ''}$${fmt(result.profit)}`}</span>}
              explKey="backtest_metrics"
            />
            <MetricCard
              label="Return %"
              value={<span className={(Number(result.return_pct)||0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}>{`${(Number(result.return_pct)||0) >= 0 ? '+' : ''}${(result.return_pct*100).toFixed(2)}%`}</span>}
              explKey="backtest_metrics"
            />
            {typeof result.cagr === 'number' && (
              <MetricCard label="CAGR" value={`${(result.cagr*100).toFixed(2)}%`} />
            )}
            {typeof result.sharpe_ratio === 'number' && (
              <MetricCard label="Sharpe Ratio" value={`${Number(result.sharpe_ratio).toFixed(2)}`} />
            )}
            <MetricCard label="Win Rate" value={`${(result.win_rate*100).toFixed(1)}%`} explKey="backtest_metrics" />
            {typeof result.profit_factor === 'number' && (
              <MetricCard label="Profit Factor" value={`${Number(result.profit_factor).toFixed(2)}`} />
            )}
            {typeof result.buy_and_hold_return_pct === 'number' && (
              <MetricCard
                label="Buy&Hold %"
                value={<span className={(Number(result.buy_and_hold_return_pct)||0) >= 0 ? 'text-slate-700' : 'text-slate-700'}>{`${(result.buy_and_hold_return_pct*100).toFixed(2)}%`}</span>}
                explKey="buy_and_hold"
              />
            )}
            {typeof result.drawdown_max === 'number' && (
              <MetricCard label="Max Drawdown" value={<span className="text-rose-700">{`${(result.drawdown_max*100).toFixed(1)}%`}</span>} explKey="risk_management" />
            )}
          </div>

          <AIExplainBlock topic="backtesting" />
          <AIExplainBlock topic="risk_management" />
        </>
      )}
    </Layout>
  );
}

function fmt(n){
  try { return Number(n).toLocaleString('en-US', { maximumFractionDigits: 2 }); } catch { return String(n); }
}

const btn = { background: '#0f172a', color: '#f8fafc', border: 'none', padding: '6px 12px', borderRadius: 4, cursor: 'pointer' };
