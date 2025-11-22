import React, { useEffect, useState, useCallback } from 'react';
import Layout from '../components/core/layout';
import CandleChart from '../components/charts/CandleChart';
// Removed PredictionHistoryChart per request
import VolatilityChart from '../components/charts/VolatilityChart';
import TechnicalIndicatorsChart from '../components/charts/TechnicalIndicatorsChart';
import { useParams } from 'react-router-dom';
import { fetchRawData, fetchTechnicalIndicators, fetchAnalysisSummary } from '../services/apiClient';
import useWebSocket from '../hooks/useWebSocket';

export default function StockDetail() {
  const params = useParams();
  const [symbol, setSymbol] = useState(params.symbol || 'AAPL');
  useEffect(() => { setSymbol(params.symbol || 'AAPL'); }, [params.symbol]);

  return (
    <Layout>
      <div className="grid xl:grid-cols-4 gap-4">
        {/* Primary price + candlesticks */}
        <div className="xl:col-span-2 flex flex-col gap-4">
          <div className="bg-white rounded border p-3">
            <div className="font-semibold mb-2">{symbol} — Live Price & Candlestick</div>
            <CandleChart symbol={symbol} live controls={false} />
          </div>
          <TechnicalIndicatorsChart symbol={symbol} />
        </div>
        {/* Analysis panel */}
        <div className="bg-white rounded border p-3 xl:col-span-1">
          <div className="font-semibold mb-2">Stock Analysis</div>
          <StockAnalysis symbol={symbol} />
        </div>
        {/* Volatility & volume */}
        <div className="xl:col-span-1">
          <VolatilityChart symbol={symbol} />
        </div>
      </div>
    </Layout>
  );
}

function StockAnalysis({ symbol }) {
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [prevClose, setPrevClose] = useState(null);
  
  // WebSocket for live updates
  const wsBase = (process.env.REACT_APP_API_BASE || 'http://localhost:8000').replace(/^http/, 'ws');
  const wsUrl = `${wsBase}/ws/price/${symbol}`;

  const handleMessage = useCallback((msg) => {
    if (msg?.last_candle) {
      setData(prev => {
        if (!prev || !prevClose) return prev;

        const c = msg.last_candle;
        const i = msg.indicators || {};
        
        const currentClose = Number(c.close);
        const change = currentClose - prevClose;
        const changePct = (change / prevClose) * 100;

        return {
          ...prev,
          price: {
            ...prev.price,
            open: fmt(c.open),
            high: fmt(c.high),
            low: fmt(c.low),
            close: fmt(c.close),
            volume: Number(c.volume).toLocaleString(),
            change: change.toFixed(2),
            changePct: changePct.toFixed(2),
            isUp: change >= 0
          },
          tech: {
            ...prev.tech,
            rsi: i.rsi ? Number(i.rsi).toFixed(1) : prev.tech.rsi,
            macd: i.macd ? Number(i.macd).toFixed(2) : prev.tech.macd,
            sma: i.sma ? fmt(i.sma) : prev.tech.sma,
            ema: i.ema ? fmt(i.ema) : prev.tech.ema
          }
        };
      });
    }
  }, [prevClose]);

  useWebSocket(wsUrl, {
    onMessage: handleMessage
  });
  
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [raw, tech, analysis] = await Promise.all([
          fetchRawData(symbol, 2),
          fetchTechnicalIndicators(symbol, { limit: 1 }),
          fetchAnalysisSummary(symbol)
        ]);
        
        if (cancelled) return;

        const rows = raw?.rows || raw?.items || [];
        const latest = rows[rows.length - 1] || {};
        const prev = rows[rows.length - 2] || {};
        
        const techItems = tech?.items || tech?.rows || [];
        const indicators = techItems[techItems.length - 1] || {};

        // Calculate change
        const close = Number(latest.close);
        const pClose = Number(prev.close);
        setPrevClose(pClose);

        const change = close - pClose;
        const changePct = pClose ? (change / pClose) * 100 : 0;

        setData({
          price: {
            open: fmt(latest.open),
            high: fmt(latest.high),
            low: fmt(latest.low),
            close: fmt(latest.close),
            volume: Number(latest.volume).toLocaleString(),
            change: change.toFixed(2),
            changePct: changePct.toFixed(2),
            isUp: change >= 0
          },
          tech: {
            rsi: Number(indicators.rsi || 0).toFixed(1),
            macd: Number(indicators.macd || 0).toFixed(2),
            sma: fmt(indicators.sma),
            ema: fmt(indicators.ema)
          }
        });
        setSummary(analysis);
      } catch (e) {
        console.error(e);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [symbol]);

  if (!data) return <div className="text-sm text-gray-500">Loading analysis...</div>;

  const { price, tech } = data;

  return (
    <div className="space-y-4">
      {/* Price Summary */}
      <div className="p-3 bg-slate-50 rounded border border-slate-100">
        <div className="flex justify-between items-end mb-2">
          <span className="text-2xl font-bold text-slate-800">{price.close}</span>
          <span className={`text-sm font-medium ${price.isUp ? 'text-emerald-600' : 'text-rose-600'}`}>
            {price.isUp ? '▲' : '▼'} {price.change} ({price.changePct}%)
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
          <div className="flex justify-between"><span>Open</span> <span className="font-mono">{price.open}</span></div>
          <div className="flex justify-between"><span>High</span> <span className="font-mono">{price.high}</span></div>
          <div className="flex justify-between"><span>Low</span> <span className="font-mono">{price.low}</span></div>
          <div className="flex justify-between"><span>Vol</span> <span className="font-mono">{price.volume}</span></div>
        </div>
      </div>

      {/* Trading Signal */}
      {summary && (
        <div className="p-3 bg-blue-50 rounded border border-blue-100">
          <div className="text-xs font-semibold text-blue-800 uppercase mb-1">Trading Signal</div>
          <div className="flex items-center justify-between">
            <span className={`text-lg font-bold ${
              summary.recommendation.includes('Buy') ? 'text-emerald-600' : 
              summary.recommendation.includes('Sell') ? 'text-rose-600' : 'text-slate-600'
            }`}>
              {summary.recommendation}
            </span>
            <div className="text-right text-[10px] text-slate-500">
              <div>Sup: {fmt(summary.levels.support)}</div>
              <div>Res: {fmt(summary.levels.resistance)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Technical Indicators */}
      <div>
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Technical Indicators</h4>
        <div className="grid grid-cols-2 gap-3">
          <IndicatorCard label="RSI (14)" value={tech.rsi} 
            status={Number(tech.rsi) > 70 ? 'Overbought' : Number(tech.rsi) < 30 ? 'Oversold' : 'Neutral'} 
            color={Number(tech.rsi) > 70 ? 'text-rose-600' : Number(tech.rsi) < 30 ? 'text-emerald-600' : 'text-slate-600'}
          />
          <IndicatorCard label="MACD" value={tech.macd} 
            status={Number(tech.macd) > 0 ? 'Bullish' : 'Bearish'}
            color={Number(tech.macd) > 0 ? 'text-emerald-600' : 'text-rose-600'}
          />
          <IndicatorCard label="SMA (20)" value={tech.sma} status="Trend" />
          <IndicatorCard label="EMA (20)" value={tech.ema} status="Weighted" />
        </div>
      </div>
    </div>
  );
}

function IndicatorCard({ label, value, status, color = 'text-slate-700' }) {
  return (
    <div className="bg-slate-50 p-2 rounded border border-slate-100">
      <div className="text-[10px] text-slate-400 uppercase">{label}</div>
      <div className={`font-mono font-medium ${color}`}>{value}</div>
      <div className="text-[10px] text-slate-500 mt-1">{status}</div>
    </div>
  );
}

function fmt(x){
  if (x == null || Number.isNaN(Number(x))) return '-';
  try { return '$'+Number(x).toFixed(2); } catch { return String(x); }
}
