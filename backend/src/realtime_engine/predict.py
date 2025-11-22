# src/api/realtime.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path

from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.database.connection import SessionLocal
from src.database.models import Predictions
from src.utils import load_obj

router = APIRouter()

_MODEL_CACHE = {}


# ---------- MODEL LOADING WITH CACHE ----------
def load_for_inference(symbol: str):
    symbol = symbol.upper()

    if symbol in _MODEL_CACHE:
        return _MODEL_CACHE[symbol]

    base = Path("artifacts/models") / symbol
    if not base.exists():
        raise FileNotFoundError("Model not trained for this symbol.")

    direction = tf.keras.models.load_model(base / f"{symbol}_direction.keras")
    ret = tf.keras.models.load_model(base / f"{symbol}_return.keras")
    ind_scaler = load_obj(base / f"{symbol}_ind_scaler.pkl")
    target_scaler = load_obj(base / f"{symbol}_target_scaler.pkl")

    obj = {
        "direction": direction,
        "return": ret,
        "ind_scaler": ind_scaler,
        "target_scaler": target_scaler,
        "transformer": DataTransformation()
    }

    _MODEL_CACHE[symbol] = obj
    return obj


# ---------- HELPER: USE ONLY CLOSED CANDLE ----------
def get_closed_candles(df: pd.DataFrame):
    """
    Removes the last row (usually incomplete intraday candle).
    Ensures predictions are always made on stable data.
    """
    if len(df) <= 2:
        raise ValueError("Not enough candles for safe prediction.")

    return df.iloc[:-1].reset_index(drop=True)  # last candle = in-progress, drop it


# ---------- MAIN: SINGLE, SAFE PREDICTION ----------
@router.post("/predict")
def make_one_prediction(symbol: str):
    try:
        artifacts = load_for_inference(symbol)

        # 1) ingestion
        ingestor = DataIngestion(symbol)
        df_raw = ingestor.fin_data_ingestion()

        # 2) enforce CLOSED candles only → prevents confusion
        df = get_closed_candles(df_raw)

        # 3) transform
        X_seq, X_ind, y_ret, y_dir, feat, vol_array = artifacts["transformer"].fin_data_transform(df)

        X_seq_last = X_seq[-1:].astype("float32")
        X_ind_last = X_ind[-1:].astype("float32")
        vol20_last = float(vol_array[-1])

        # 4) scale
        X_ind_last = artifacts["ind_scaler"].transform(X_ind_last)

        # 5) direction prediction
        p = float(
            artifacts["direction"].predict([X_seq_last, X_ind_last], verbose=0)[0][0]
        )
        direction = 1 if p >= 0.55 else 0   # stable: no +/-1, only 0/1

        # 6) return prediction
        ret_scaled = float(
            artifacts["return"].predict([X_seq_last, X_ind_last], verbose=0)[0][0]
        )

        ret_norm = artifacts["target_scaler"].inverse_transform([[ret_scaled]])[0][0]
        predicted_return = float(ret_norm * (vol20_last + 1e-9))

        # 7) price estimation
        last_price = float(df.iloc[-1]["close"])
        next_price = last_price * (1 + predicted_return)

        # 8) persist prediction
        db = SessionLocal()
        try:
            pred_row = Predictions(
                stock_symbol=symbol.upper(),
                prediction_time=datetime.utcnow(),
                predicted_return=predicted_return,
                predicted_direction=direction,
                signal="UP" if direction == 1 else "DOWN",
                confidence=p,
                explanation={
                    "note": "Prediction uses last *closed* candle. No live or incomplete data used."
                }
            )
            db.add(pred_row)
            db.commit()
            db.refresh(pred_row)

        finally:
            db.close()

        # 9) RETURN
        return JSONResponse({
            "prediction_id": pred_row.id,
            "symbol": symbol.upper(),
            "timestamp": pred_row.prediction_time.isoformat(),
            "direction": direction,
            "probability": p,
            "predicted_return": predicted_return,
            "predicted_next_price": next_price,
            "current_price": last_price
        })

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
