from fastapi import APIRouter, HTTPException
from datetime import timedelta
import numpy as np
import math
import pandas as pd

from src.realtime_engine.predict import load_for_inference, get_closed_candles
from src.components.data_ingestion import DataIngestion

router = APIRouter(prefix="/forecast", tags=["forecast"])


import traceback

@router.get("/next")
def forecast_next(symbol: str, days: int = 1):
    """
    Naive multi-step forecast using existing single-step models in an autoregressive manner.
    Inputs are updated each step by appending the predicted price to the history and re-calculating features.
    """
    try:
        days = int(max(1, min(days, 14)))
        artifacts = load_for_inference(symbol)
        df_raw = DataIngestion(symbol).fin_data_ingestion()
        df = get_closed_candles(df_raw)

        # Initial Transform
        X_seq, X_ind, y_ret, y_dir, feat, vol_array, dates, prices = artifacts["transformer"].fin_data_transform(df, inference=True)
        Xs = X_seq[-1:].astype("float32")
        Xi = X_ind[-1:].astype("float32")
        Xi = artifacts["ind_scaler"].transform(Xi)
        vol20 = float(vol_array[-1])

        last_price = float(df.iloc[-1]["close"])
        # Ensure start_date is a Timestamp
        if "date" in df.columns:
            start_date = pd.to_datetime(df.iloc[-1]["date"])
        else:
            # Fallback if date column is missing (unlikely with DataIngestion)
            start_date = pd.Timestamp.now()

        path = []
        cur_price = last_price
        cur_date = start_date
        
        # Working copy for autoregression
        df_curr = df.copy()

        for i in range(days):
            # 1. Predict
            # Use .item() to avoid DeprecationWarning for single-element arrays
            p = artifacts["direction"].predict([Xs, Xi], verbose=0)[0][0].item()
            ret_scaled = artifacts["return"].predict([Xs, Xi], verbose=0)[0][0].item()
            ret = artifacts["target_scaler"].inverse_transform([[ret_scaled]])[0][0].item()
            pred_return = float(ret * (vol20 + 1e-9))
            
            # Update price
            cur_price = cur_price * (1 + pred_return)
            
            # Update date (skip weekends)
            if cur_date is not None:
                cur_date = cur_date + timedelta(days=1)
                while cur_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    cur_date = cur_date + timedelta(days=1)
            
            path.append({
                "step": i + 1,
                "date": cur_date.isoformat() if cur_date is not None else None,
                "probability": p,
                "predicted_return": pred_return,
                "predicted_price": cur_price,
            })
            
            # 2. Update State (Autoregression)
            # Append predicted candle to history to recalculate indicators for next step
            last_vol = df_curr.iloc[-1]["volume"]
            new_row = pd.DataFrame([{
                "date": cur_date,
                "open": cur_price,
                "high": cur_price,
                "low": cur_price,
                "close": cur_price,
                "volume": last_vol
            }])
            df_curr = pd.concat([df_curr, new_row], ignore_index=True)
            
            # Re-transform
            X_seq_next, X_ind_next, _, _, _, vol_array_next, _, _ = artifacts["transformer"].fin_data_transform(df_curr, inference=True)
            
            Xs = X_seq_next[-1:].astype("float32")
            Xi = X_ind_next[-1:].astype("float32")
            Xi = artifacts["ind_scaler"].transform(Xi)
            vol20 = float(vol_array_next[-1])

        return {"symbol": symbol, "forecast": path}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cone")
def forecast_cone(symbol: str, days: int = 7, confidence: float = 0.9):
    """
    Returns a simple forecast cone for the next N days with mid, lower, upper paths.
    Bands are derived from recent realized volatility and widen each step.
    """
    try:
        days = int(max(1, min(days, 30)))
        confidence = float(max(0.5, min(confidence, 0.999)))

        # crude z-score lookup (two-tailed) for common confidence levels
        z_table = {
            0.8: 1.2816,
            0.85: 1.4395,
            0.9: 1.6449,
            0.95: 1.96,
            0.975: 2.2414,
            0.99: 2.5758,
        }
        # pick closest key
        z = z_table[min(z_table.keys(), key=lambda k: abs(k - confidence))]

        artifacts = load_for_inference(symbol)
        df_raw = DataIngestion(symbol).fin_data_ingestion()
        df = get_closed_candles(df_raw)

        X_seq, X_ind, y_ret, y_dir, feat, vol_array, dates, prices = artifacts["transformer"].fin_data_transform(df)
        if X_seq is None or len(X_seq) == 0:
            raise HTTPException(status_code=400, detail="Not enough data for forecasting")

        # scale indicators and infer last state
        Xs = X_seq[-1:].astype("float32")
        Xi = X_ind[-1:].astype("float32")
        Xi = artifacts["ind_scaler"].transform(Xi)

        # realized daily volatility from last 20 bars
        try:
            close = df["close"].astype(float).values
            rets = np.diff(close) / close[:-1]
            sigma_r = float(np.std(rets[-20:], ddof=1)) if rets.size >= 5 else 0.02
        except Exception:
            sigma_r = 0.02

        last_price = float(df.iloc[-1]["close"])
        start_date = df.iloc[-1]["date"] if "date" in df.columns else None

        path = []
        cur_mid = last_price
        cur_upper = last_price
        cur_lower = last_price
        for i in range(days):
            # model one-step prediction
            p_up = float(artifacts["direction"].predict([Xs, Xi], verbose=0)[0][0])
            ret_scaled = float(artifacts["return"].predict([Xs, Xi], verbose=0)[0][0])
            ret = artifacts["target_scaler"].inverse_transform([[ret_scaled]])[0][0]

            # use model-implied return scaled by volatility as point forecast
            mid_ret = float(ret * (float(vol_array[-1]) + 1e-9))

            # widen bands with sqrt time
            widen = z * sigma_r * math.sqrt(i + 1)

            cur_mid = cur_mid * (1.0 + mid_ret)
            cur_upper = cur_upper * (1.0 + mid_ret + widen)
            cur_lower = cur_lower * (1.0 + mid_ret - widen)

            cur_date = (start_date + timedelta(days=i + 1)) if start_date is not None else None
            path.append({
                "step": i + 1,
                "date": cur_date.isoformat() if cur_date is not None else None,
                "probability": p_up,
                "predicted_price": float(cur_mid),
                "upper": float(cur_upper),
                "lower": float(cur_lower),
            })

        return {
            "symbol": symbol.upper(),
            "last_price": last_price,
            "start_date": start_date.isoformat() if start_date is not None else None,
            "days": days,
            "confidence": confidence,
            "path": path,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
