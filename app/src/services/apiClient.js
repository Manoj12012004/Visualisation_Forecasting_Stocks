import axios from 'axios';

// Base URL (supports CRA + NEXT style vars)
const baseURL = process.env.REACT_APP_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
export const api = axios.create({ baseURL });

// ---------------- Lightweight In-Memory Cache ----------------
// Keyed by endpoint + sorted params, with per-entry TTL
const _cache = new Map();

function cacheKey(path, params) {
  const normalized = params && typeof params === 'object' ? Object.keys(params).sort().reduce((acc, k) => { acc[k] = params[k]; return acc; }, {}) : undefined;
  return `${path}::${JSON.stringify(normalized || {})}`;
}

function cacheGet(path, params) {
  const key = cacheKey(path, params);
  const hit = _cache.get(key);
  if (!hit) return undefined;
  if (hit.expiresAt && hit.expiresAt < Date.now()) {
    _cache.delete(key);
    return undefined;
  }
  return hit.value;
}

function cacheSet(path, params, value, ttlMs) {
  const key = cacheKey(path, params);
  const expiresAt = ttlMs ? Date.now() + Number(ttlMs) : undefined;
  _cache.set(key, { value, expiresAt });
  return value;
}

export function invalidateCache(pathPrefix) {
  if (!pathPrefix) {
    _cache.clear();
    return;
  }
  for (const key of _cache.keys()) {
    if (key.startsWith(pathPrefix)) _cache.delete(key);
  }
}

// Default TTLs (ms)
const TTL = {
  veryShort: Number(process.env.REACT_APP_CACHE_TTL_VERY_SHORT_MS || 5_000),
  short: Number(process.env.REACT_APP_CACHE_TTL_SHORT_MS || 30_000),
  medium: Number(process.env.REACT_APP_CACHE_TTL_MEDIUM_MS || 120_000),
  long: Number(process.env.REACT_APP_CACHE_TTL_LONG_MS || 600_000),
};

async function getWithCache(path, { params, ttlMs } = {}) {
  const cached = cacheGet(path, params);
  if (cached !== undefined) return cached;
  const { data } = await api.get(path, params ? { params } : undefined);
  return cacheSet(path, params, data, ttlMs);
}

// ---------------- Stocks ----------------
export async function listStocks() {
  // Names list changes rarely; cache longer
  return getWithCache('/stocks/list', { ttlMs: TTL.long });
}

export async function trainStock(symbol, force = false) {
  const { data } = await api.get(`/stocks/${symbol}/train`, { params: { force } });
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

export async function backtestSimulateRange(symbol, options = {}) {
  const params = { symbol, ...options };
  const { data } = await api.get('/backtest/simulate_range', { params });
  return data;
}

// ---------------- Evaluation Metrics ----------------
export async function evaluatePredictions(symbol) {
  const { data } = await api.post('/evaluation/evaluate', null, { params: { symbol } });
  return data;
}

export async function fetchMetrics(symbol) {
  // Cache briefly to avoid repeated panels hitting at once
  return getWithCache('/evaluation/metrics', { params: { symbol }, ttlMs: TTL.short });
}

// ---------------- Market ----------------
export async function fetchHeatmap(symbols) {
  const params = symbols && symbols.length ? { symbols: symbols.join(',') } : undefined;
  const data = await getWithCache('/market/heatmap', { params, ttlMs: TTL.veryShort });
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
export async function fetchRawData(symbol, limitOrOptions = 200) {
  let params = { symbol };
  if (typeof limitOrOptions === 'number') {
    params.limit = limitOrOptions;
  } else {
    params = { symbol, ...limitOrOptions };
  }
  return getWithCache('/data/raw', { params, ttlMs: TTL.short });
}

// ---------------- Explainability ----------------
export async function fetchFeatureImportance(symbol) {
  const { data } = await api.get('/explain/feature-importance', { params: { symbol } });
  return data;
}

export async function fetchSequenceAttribution(symbol) {
  const { data } = await api.get('/explain/sequence-attribution', { params: { symbol } });
  return data;
}

// ---------------- Technical Indicators ----------------
export async function fetchTechnicalIndicators(symbol, options = {}) {
  // Only pass supported params to avoid backend errors
  const allow = new Set(['symbol','limit','period','interval','sma_window','ema_window','bb_window','rsi_window','macd_fast','macd_slow','macd_signal','bb_k']);
  const params = { symbol };
  for (const [k,v] of Object.entries(options || {})) {
    if (allow.has(k)) params[k] = v;
  }
  return getWithCache('/data/technical', { params, ttlMs: TTL.medium }); // expected { symbol, items: [...] }
}

export async function fetchAnalysisSummary(symbol) {
  return getWithCache('/data/analysis/summary', { params: { symbol }, ttlMs: TTL.short });
}

export async function forecastCone(symbol, opts = {}) {
  const params = { symbol, ...(opts || {}) };
  return getWithCache('/data/forecast_cone', { params, ttlMs: TTL.medium }); // expected { path: [...] } or similar
}

