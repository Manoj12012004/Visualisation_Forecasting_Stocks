from fastapi import APIRouter, HTTPException

from src.components.data_ingestion import DataIngestion
from src.realtime_engine.predict import load_for_inference
from src.components.data_transformation import DataTransformation

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
        raise HTTPException(status_code=500, detail=str(e))
