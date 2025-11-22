import React, { useState } from 'react';
import Layout from '../components/core/layout';
import SymbolSearch from '../components/core/SymbolSearch';
import MetricCard from '../components/core/MetricCard';
import EquityChart from '../components/charts/EquityChart';
import { backtestSimulateRange } from '../services/apiClient';

export default function BacktestPage() {
  const [symbol, setSymbol] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runSim() {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      // Simulate over the last year (or full available range handled by backend default)
      const data = await backtestSimulateRange(symbol, { initial: 10000 });
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch (e) {
      console.error(e);
      setError("Failed to run backtest simulation.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Strategy Backtest</h2>
          <p className="text-slate-500 mt-1">
            Simulate the model's performance on historical data to evaluate risk and return.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex flex-col md:flex-row gap-4 items-end md:items-center justify-between">
            <div className="w-full md:w-auto">
              <label className="block text-sm font-medium text-slate-700 mb-1">Select Stock</label>
              <SymbolSearch onSelect={setSymbol} />
            </div>
            <button 
              disabled={!symbol || loading} 
              onClick={runSim} 
              className={`px-6 py-2 rounded-lg font-medium text-white transition-all ${!symbol || loading ? 'bg-slate-300 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 shadow-md hover:shadow-lg'}`}
            >
              {loading ? 'Running Simulation...' : 'Run Backtest'}
            </button>
          </div>
          {symbol && <div className="mt-2 text-sm text-slate-500">Selected: <span className="font-semibold text-slate-800">{symbol}</span></div>}
        </div>

        {error && (
          <div className="p-4 bg-rose-50 text-rose-700 border border-rose-200 rounded-lg">
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-6 animate-fade-in">
            {/* Trust Indicator */}
            <div className="bg-blue-50 border border-blue-100 p-4 rounded-lg flex items-start gap-3">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              <div>
                <h4 className="font-semibold text-blue-900 text-sm">Simulation Context</h4>
                <p className="text-sm text-blue-800 mt-1">
                  This backtest simulates the strategy over the period <strong>{result.range?.start}</strong> to <strong>{result.range?.end}</strong>. 
                  It assumes a transaction cost of {(Number(result.params?.fee_bps || 0) + Number(result.params?.slippage_bps || 0))/100}% per trade. 
                  Past performance is not indicative of future results.
                </p>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Final Balance" value={`$${fmt(result.final_balance)}`} explKey="backtest_metrics" />
              <MetricCard
                label="Net Profit"
                value={<span className={(Number(result.profit)||0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}>{`${(Number(result.profit)||0) >= 0 ? '+' : ''}$${fmt(result.profit)}`}</span>}
                explKey="backtest_metrics"
              />
              <MetricCard
                label="Return %"
                value={<span className={(Number(result.return_pct)||0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}>{`${(Number(result.return_pct)||0) >= 0 ? '+' : ''}${(result.return_pct*100).toFixed(2)}%`}</span>}
                explKey="backtest_metrics"
              />
              <MetricCard label="Sharpe Ratio" value={`${Number(result.sharpe_ratio).toFixed(2)}`} />
              <MetricCard label="Win Rate" value={`${(result.win_rate*100).toFixed(1)}%`} explKey="backtest_metrics" />
              <MetricCard label="Max Drawdown" value={<span className="text-rose-600">{`${(result.drawdown_max*100).toFixed(1)}%`}</span>} explKey="risk_management" />
              <MetricCard label="Profit Factor" value={`${Number(result.profit_factor).toFixed(2)}`} />
              <MetricCard
                label="Buy & Hold"
                value={<span className="text-slate-600">{`${(result.buy_and_hold_return_pct*100).toFixed(2)}%`}</span>}
                explKey="buy_and_hold"
              />
            </div>

            {/* Equity Chart */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="font-bold text-lg text-slate-800 mb-4">Equity Curve vs Benchmark</h3>
              <EquityChart modelEquity={result.model_equity} benchmarkEquity={result.benchmark?.equity} height={400} />
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

function fmt(n){
  try { return Number(n).toLocaleString('en-US', { maximumFractionDigits: 2 }); } catch { return String(n); }
}

