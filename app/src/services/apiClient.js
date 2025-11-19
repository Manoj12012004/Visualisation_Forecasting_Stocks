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

export async function forecastCone(symbol, { days = 7, confidence = 0.9 } = {}) {
  const { data } = await api.get('/forecast/cone', { params: { symbol, days, confidence } });
  return data; // { symbol, days, confidence, path: [{ date, predicted_price, lower, upper }] }
}

// ---------------- Data ----------------
export async function fetchRawData(symbol, limit = 200) {
  const { data } = await api.get('/data/raw', { params: { symbol, limit } });
  return data;
}

// (Removed) Explainability endpoints not used in the streamlined UI

// ---------------- Technical Indicators ----------------
export async function fetchTechnicalIndicators(symbol, options = {}) {
  const params = { symbol, ...(options || {}) };
  const { data } = await api.get('/data/technical', { params });
  return data; // { symbol, items: [{ date, open, high, low, close, volume, sma, ema, rsi, macd, macd_signal, macd_hist, bb_mid, bb_upper, bb_lower }] }
}
