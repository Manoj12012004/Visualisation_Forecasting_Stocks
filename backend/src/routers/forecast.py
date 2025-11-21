from fastapi import APIRouter, HTTPException
from datetime import timedelta
import numpy as np
import math

from src.realtime_engine.predict import load_for_inference, get_closed_candles
from src.components.data_ingestion import DataIngestion

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/next")
def forecast_next(symbol: str, days: int = 1):
    """
    Naive multi-step forecast using existing single-step models in an autoregressive manner.
    Inputs are held constant (last available sequence/indicators); output returns are compounded.
    """
    try:
        days = int(max(1, min(days, 14)))
        artifacts = load_for_inference(symbol)
        df_raw = DataIngestion(symbol).fin_data_ingestion()
        df = get_closed_candles(df_raw)

        X_seq, X_ind, y_ret, y_dir, feat, vol_array = artifacts["transformer"].fin_data_transform(df)
        Xs = X_seq[-1:].astype("float32")
        Xi = X_ind[-1:].astype("float32")
        Xi = artifacts["ind_scaler"].transform(Xi)
        vol20 = float(vol_array[-1])

        last_price = float(df.iloc[-1]["close"])
        start_date = df.iloc[-1]["date"] if "date" in df.columns else None

        path = []
        cur_price = last_price
        cur_date = None
        for i in range(days):
            p = float(artifacts["direction"].predict([Xs, Xi], verbose=0)[0][0])
            ret_scaled = float(artifacts["return"].predict([Xs, Xi], verbose=0)[0][0])
            ret = artifacts["target_scaler"].inverse_transform([[ret_scaled]])[0][0]
            pred_return = float(ret * (vol20 + 1e-9))
            cur_price = cur_price * (1 + pred_return)
            cur_date = (start_date + timedelta(days=i+1)) if start_date is not None else None
            path.append({
                "step": i + 1,
                "date": cur_date.isoformat() if cur_date is not None else None,
                "probability": p,
                "predicted_return": pred_return,
                "predicted_price": cur_price,
            })

        return {
            "symbol": symbol.upper(),
            "last_price": last_price,
            "start_date": start_date.isoformat() if start_date is not None else None,
            "days": days,
            "path": path
        }
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

        X_seq, X_ind, y_ret, y_dir, feat, vol_array = artifacts["transformer"].fin_data_transform(df)
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
