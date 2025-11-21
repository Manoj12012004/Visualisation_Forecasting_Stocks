import axios from 'axios';

// Base URL (supports CRA + NEXT style vars)
const baseURL = process.env.REACT_APP_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
export const api = axios.create({ baseURL });

// ---------------- Stocks ----------------
export async function listStocks() {
  const { data } = await api.get('/stocks/list');
  return data;
}

export async function trainStock(symbol) {
  const { data } = await api.get(`/stocks/${symbol}/train`);
  return data;
}

// (Removed) Indicators Education endpoints were tied to deprecated Learn page

// (Removed) Legacy prediction helpers; RealtimeSmall handles requests directly

// ---------------- Backtest ----------------
export async function backtestSimple(symbol, { threshold = 0.6, feeBps = 1, slippageBps = 1, initial = 10000 } = {}) {
  const params = new URLSearchParams({
    symbol,
    threshold: String(threshold),
    fee_bps: String(feeBps),
    slippage_bps: String(slippageBps),
    initial: String(initial)
  });
  const { data } = await api.get(`/backtest/simple?${params.toString()}`);
  return data;
}

// (Removed) backtestSimulate unused by current UI

// ---------------- Evaluation Metrics ----------------
export async function evaluatePredictions(symbol) {
  const { data } = await api.post('/evaluation/evaluate', null, { params: { symbol } });
  return data;
}

export async function fetchMetrics(symbol) {
  const { data } = await api.get('/evaluation/metrics', { params: { symbol } });
  return data;
}

// ---------------- Market ----------------
export async function fetchHeatmap(symbols) {
  const params = symbols && symbols.length ? { symbols: symbols.join(',') } : undefined;
  const { data } = await api.get('/market/heatmap', { params });
  const items = Array.isArray(data) ? data : (data.items || []);
  // Normalize shape and scale to percent points
  return items.map(it => ({
    symbol: it.symbol || it.ticker || it.sym,
    pct_change: (it.pct_change != null ? it.pct_change : it.change_pct) * 100,
  }));
}

// ---------------- Forecast ----------------
export async function forecastNext(symbol, days = 1) {
  const { data } = await api.get('/forecast/next', { params: { symbol, days } });
  return data;
}

// ---------------- Data ----------------
export async function fetchRawData(symbol, limit = 200) {
  const { data } = await api.get('/data/raw', { params: { symbol, limit } });
  return data;
}

// (Removed) Explainability endpoints not used in the streamlined UI

// ---------------- Technical Indicators ----------------
export async function fetchTechnicalIndicators(symbol, options = {}) {
  // Only pass supported params to avoid backend errors
  const allow = new Set(['symbol','limit','sma_window','ema_window','bb_window','rsi_window','macd_fast','macd_slow','macd_signal','bb_k']);
  const params = { symbol };
  for (const [k,v] of Object.entries(options || {})) {
    if (allow.has(k)) params[k] = v;
  }
  const { data } = await api.get('/data/technical', { params });
  return data; // expected { symbol, items: [...] }
}

export async function forecastCone(symbol, opts = {}) {
  const params = { symbol, ...(opts || {}) };
  const { data } = await api.get('/data/forecast_cone', { params });
  return data; // expected { path: [...] } or similar
}
