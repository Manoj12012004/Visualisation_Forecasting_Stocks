from fastapi import APIRouter, HTTPException

from src.components.data_ingestion import DataIngestion
from src.realtime_engine.predict import load_for_inference
from src.components.data_transformation import DataTransformation
from src.exception import CustomException
import sys
from datetime import timedelta
import math
import numpy as np
import pandas as pd

router = APIRouter()


@router.get("/raw")
def raw_data(symbol: str, period: str = "5y", interval: str = "1d", limit: int = 5000):
    try:
        df = DataIngestion(symbol).fin_data_ingestion(period=period, interval=interval)
        use_limit = int(max(1, min(limit, 10000)))
        out = df.tail(use_limit).reset_index(drop=True)
        # Build rows explicitly to avoid pandas/numpy types or multi-index artifacts creating non-string keys
        rows = []
        for tup in out.itertuples():
            try:
                date_val = getattr(tup, 'date', None)
                if hasattr(date_val, 'isoformat'):
                    date_val = date_val.isoformat()
                elif date_val is not None:
                    date_val = str(date_val)
                row = {
                    'date': date_val,
                    'open': float(getattr(tup, 'open')) if hasattr(tup, 'open') else None,
                    'high': float(getattr(tup, 'high')) if hasattr(tup, 'high') else None,
                    'low': float(getattr(tup, 'low')) if hasattr(tup, 'low') else None,
                    'close': float(getattr(tup, 'close')) if hasattr(tup, 'close') else None,
                    'volume': float(getattr(tup, 'volume')) if hasattr(tup, 'volume') else None,
                }
                rows.append(row)
            except Exception:
                # Skip malformed row
                continue
        return {"symbol": symbol.upper(), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast_cone")
def forecast_cone(symbol: str, days: int = 7, confidence: float = 0.9):
    """
    Simple volatility-based forecast cone using log-returns.
    Returns mid, lower, upper bands for the next N calendar days.
    """
    try:
        days = int(max(1, min(int(days), 60)))
        df = DataIngestion(symbol).fin_data_ingestion()
        if df is None or df.empty or "close" not in df.columns:
            raise HTTPException(status_code=404, detail="No data")
        close = df["close"].dropna()
        if len(close) < 30:
            raise HTTPException(status_code=400, detail="Not enough history for cone")

        # compute log returns
        rets = np.log(close / close.shift(1)).dropna()
        mu = float(np.mean(rets))
        sigma = float(np.std(rets))
        last_close = float(close.iloc[-1])
        # Handle date which may arrive as string instead of datetime-like
        last_date_raw = df["date"].iloc[-1]
        if isinstance(last_date_raw, str):
            try:
                last_date = pd.to_datetime(last_date_raw)
            except Exception:
                raise HTTPException(status_code=500, detail=f"Unable to parse last date: {last_date_raw}")
        else:
            last_date = last_date_raw

        # z-score lookup for common two-sided confidences
        z_map = {0.80: 1.2816, 0.85: 1.4395, 0.90: 1.6449, 0.95: 1.96, 0.975: 2.2414, 0.99: 2.5758}
        # pick nearest key
        z = z_map[min(z_map.keys(), key=lambda k: abs(k - confidence))] if confidence is not None else 1.6449

        path = []
        for t in range(1, days + 1):
            vol = sigma * math.sqrt(t)
            mid = last_close * math.exp(mu * t)
            upper = mid * math.exp(z * vol)
            lower = mid * math.exp(-z * vol)
            dt = last_date + timedelta(days=t)
            # normalize date to isoformat if pandas Timestamp
            if hasattr(dt, "isoformat"):
                dt = dt.isoformat()
            path.append({
                "date": dt,
                "mid": float(mid),
                "upper": float(upper),
                "lower": float(lower),
            })
        return {"symbol": symbol.upper(), "path": path}
    except Exception as e:
        raise CustomException(e, sys)


@router.get("/features/summary")
def feature_summary(symbol: str):
    try:
        artifacts = load_for_inference(symbol)
        df = DataIngestion(symbol).fin_data_ingestion()
        tfm = artifacts["transformer"]
        feat_df = tfm._build_features(df).dropna().reset_index(drop=True)
        desc = feat_df.describe().transpose().reset_index().rename(columns={"index": "feature"})
        cols = [c for c in ["feature", "count", "mean", "std", "min", "25%", "50%", "75%", "max"] if c in desc.columns]
        rows = desc[cols].to_dict(orient="records")
        return {"symbol": symbol.upper(), "summary": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/summary")
def analysis_summary(symbol: str):
    """
    Returns a trading signal summary (Buy/Sell/Neutral) based on technical indicators.
    """
    try:
        df = DataIngestion(symbol).fin_data_ingestion(period="6mo", interval="1d")
        if df is None or df.empty:
            raise ValueError("No data available")
        
        tfm = DataTransformation()
        # Use standard settings for analysis
        tech = tfm.technical_view(df)
        last = tech.iloc[-1]
        
        # 1. RSI Signal
        rsi = last.get("rsi", 50)
        if rsi > 70: rsi_sig = "Sell"
        elif rsi < 30: rsi_sig = "Buy"
        else: rsi_sig = "Neutral"
        
        # 2. MACD Signal
        macd = last.get("macd", 0)
        signal = last.get("macd_signal", 0)
        macd_sig = "Buy" if macd > signal else "Sell"
        
        # 3. Trend (SMA 50 vs Price)
        # We need to ensure SMA50 is calculated. technical_view calculates SMA based on window param (default 20).
        # Let's calculate SMA50 manually here or ensure technical_view provides it.
        # For simplicity, let's use the SMA20 provided as "sma" and compare to price for short-term trend.
        price = last["close"]
        sma20 = last.get("sma", price)
        trend_sig = "Bullish" if price > sma20 else "Bearish"
        
        # 4. Support/Resistance (Simple Pivot Points from last 20 days)
        recent = tech.tail(20)
        support = float(recent["low"].min())
        resistance = float(recent["high"].max())
        
        # Composite Score (Simple)
        score = 0
        if rsi_sig == "Buy": score += 1
        elif rsi_sig == "Sell": score -= 1
        
        if macd_sig == "Buy": score += 1
        else: score -= 1
        
        if trend_sig == "Bullish": score += 1
        else: score -= 1
        
        if score >= 2: recommendation = "Strong Buy"
        elif score == 1: recommendation = "Buy"
        elif score == 0: recommendation = "Neutral"
        elif score == -1: recommendation = "Sell"
        else: recommendation = "Strong Sell"
        
        return {
            "symbol": symbol.upper(),
            "recommendation": recommendation,
            "signals": {
                "rsi": {"value": float(rsi), "signal": rsi_sig},
                "macd": {"value": float(macd), "signal": macd_sig},
                "trend": {"signal": trend_sig},
            },
            "levels": {
                "support": support,
                "resistance": resistance,
                "pivot": float((last["high"] + last["low"] + last["close"]) / 3)
            },
            "price": float(price)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical")
def technical_indicators(
    symbol: str,
    period: str = "5y",
    interval: str = "1d",
    limit: int = 5000,
    sma_window: int = 20,
    ema_window: int = 20,
    bb_window: int = 20,
    rsi_window: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    bb_k: float = 2.0,
):
    """
    Returns OHLCV plus common technical indicators for charting.
    """
    try:
        df = DataIngestion(symbol).fin_data_ingestion(period=period, interval=interval)
        if df is None or df.empty:
            raise ValueError("Ingestion returned empty dataframe")
        missing_cols = {c for c in ['date','open','high','low','close','volume'] if c not in df.columns}
        if missing_cols:
            raise ValueError(f"Missing required columns after ingestion: {missing_cols}")
        tfm = DataTransformation()
        tech = tfm.technical_view(
            df,
            sma_window=sma_window,
            ema_window=ema_window,
            bb_window=bb_window,
            rsi_window=rsi_window,
            macd_fast=macd_fast,
            macd_slow=macd_slow,
            macd_signal=macd_signal,
            bb_k=bb_k,
        )
        out = tech.tail(int(max(1, min(limit, 10000)))).reset_index(drop=True)
        rows = out.to_dict(orient="records")
        for r in rows:
            if "date" in r and hasattr(r["date"], "isoformat"):
                r["date"] = r["date"].isoformat()
        return {"symbol": symbol.upper(), "items": rows}
    except Exception as e:
        # Provide richer error context during debugging; remove or tone down later.
        raise HTTPException(status_code=500, detail=f"technical_indicators failed: {type(e).__name__}: {e}")
