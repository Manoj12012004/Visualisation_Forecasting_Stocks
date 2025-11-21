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
def raw_data(symbol: str, limit: int = 200):
    try:
        df = DataIngestion(symbol).fin_data_ingestion()
        cols = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]
        out = df.tail(int(max(1, min(limit, 2000)))).reset_index(drop=True)
        rows = out[cols].to_dict(orient="records")
        for r in rows:
            if "date" in r and hasattr(r["date"], "isoformat"):
                r["date"] = r["date"].isoformat()
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


@router.get("/technical")
def technical_indicators(
    symbol: str,
    limit: int = 400,
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
        df = DataIngestion(symbol).fin_data_ingestion()
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
        out = tech.tail(int(max(1, min(limit, 2000)))).reset_index(drop=True)
        rows = out.to_dict(orient="records")
        for r in rows:
            if "date" in r and hasattr(r["date"], "isoformat"):
                r["date"] = r["date"].isoformat()
        return {"symbol": symbol.upper(), "items": rows}
    except Exception as e:
        # Provide richer error context during debugging; remove or tone down later.
        raise HTTPException(status_code=500, detail=f"technical_indicators failed: {type(e).__name__}: {e}")
