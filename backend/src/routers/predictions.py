# api/realtime.py (add)

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from src.database.connection import SessionLocal
from src.services.model_loader import get_model, ModelBundle
from src.components.data_ingestion import DataIngestion
import json

router = APIRouter()

def _ensure_last_candle_closed(df):
    # df should be sorted by date and contain a reliable 'date' column with timezone-aware times or ISO strings.
    # If using intraday ticks, implement logic to ensure latest row corresponds to closed candle.
    # Simple heuristic: if last timestamp is within very recent few seconds and timeframe is 1m, treat previous row as last closed.
    # For now: return df.iloc[:-1] as closed history and df.iloc[-1] as in-progress candle (caller decides).
    if len(df) < 2:
        raise ValueError("Not enough rows to determine closed candle.")
    return df.iloc[:-1].reset_index(drop=True)  # last row considered not-closed

@router.post("/request-prediction")
def request_prediction(symbol: str, model_version: str = None):
    """
    Run ONE prediction for `symbol` using latest closed candle window.
    Saves prediction to DB; returns prediction_id and metadata.
    """
    db = SessionLocal()
    try:
        # 1) load model bundle (does not change caching behavior)
        M: ModelBundle = get_model(symbol.upper())

        # 2) fetch recent data and ensure closed candle usage
        df = DataIngestion(symbol).fin_data_ingestion()   # your ingestion returns OHLC rows
        df_closed = _ensure_last_candle_closed(df)        # ensure we use only closed candles

        # 3) build the last sequence
        X_seq, X_ind, y_ret, y_dir, feat, vol = M.transformer.fin_data_transform(df_closed)
        if len(X_seq) == 0:
            raise HTTPException(status_code=400, detail="Not enough data to build sequence for prediction.")
        X_seq_last = X_seq[-1:]
        X_ind_last = X_ind[-1:]
        last_vol = float(vol[-1])

        # 4) scale indicators
        X_ind_last_scaled = M.ind_scaler.transform(X_ind_last)

        # 5) run models
        dir_prob = float(M.direction.predict([X_seq_last, X_ind_last_scaled], verbose=0).flatten()[0])
        predicted_direction = 1 if dir_prob > 0.55 else 0
        confidence = round(abs(dir_prob - 0.5) * 2.0, 4)

        ret_scaled = float(M.return_model.predict([X_seq_last, X_ind_last_scaled], verbose=0).flatten()[0])
        ret_norm = float(M.target_scaler.inverse_transform([[ret_scaled]])[0][0])
        predicted_return = float(ret_norm * (last_vol + 1e-9))

        current_price = float(df_closed.iloc[-1]['close'])
        predicted_next_price = float(current_price * (1.0 + predicted_return))

        # 6) explanation snapshot (beginner-friendly)
        # store raw indicator values from last row
        last_feat_row = M.transformer._build_features(df_closed.copy()).dropna().iloc[-1]
        explain = {
            "RSI": float(last_feat_row.get("RSI", None)),
            "vol_ratio": float(last_feat_row.get("vol_ratio", None)),
            "bb_pos": float(last_feat_row.get("bb_pos", None)),
            "MACD": float(last_feat_row.get("MACD", None)),
            "z_close_50": float(last_feat_row.get("z_close_50", None)),
            "note": "Prediction created using last closed candle; not using live in-progress candle."
        }

        # 7) save to DB
        from database.models import Predictions
        pred_row = Predictions(
            stock_symbol=symbol.upper(),
            prediction_time=datetime.utcnow(),
            predicted_return=predicted_return,
            predicted_direction=predicted_direction,
            signal="Buy" if predicted_direction==1 else "Sell",
            confidence=confidence,
            explanation=explain,
            model_path=str(M.direction._saved_model) if hasattr(M.direction, "_saved_model") else None,
            model_version=model_version or None
        )
        db.add(pred_row)
        db.commit()
        db.refresh(pred_row)

        payload = {
            "prediction_id": pred_row.id,
            "symbol": symbol.upper(),
            "prediction_time": pred_row.prediction_time.isoformat(),
            "predicted_return": predicted_return,
            "predicted_direction": predicted_direction,
            "predicted_next_price": predicted_next_price,
            "confidence": confidence,
            "explain": explain
        }
        return JSONResponse(content=payload)
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()



# api/realtime.py (add)

@router.get("/predictions/latest")
def latest_prediction(symbol: str):
    db = SessionLocal()
    try:
        res = db.query(Predictions).filter(Predictions.stock_symbol==symbol.upper()).order_by(Predictions.id.desc()).first()
        if not res:
            raise HTTPException(status_code=404, detail="No predictions found for symbol")
        out = {
            "id": res.id,
            "symbol": res.stock_symbol,
            "prediction_time": res.prediction_time.isoformat(),
            "predicted_return": res.predicted_return,
            "predicted_direction": res.predicted_direction,
            "signal": res.signal,
            "confidence": res.confidence,
            "explanation": res.explanation,
            "model_path": res.model_path,
            "model_version": res.model_version
        }
        return out
    finally:
        db.close()


@router.get("/predictions/history")
def prediction_history(symbol: str, limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.query(Predictions).filter(Predictions.stock_symbol==symbol.upper()).order_by(Predictions.id.desc()).limit(limit).all()
        return {"items": [
            {
                "id": r.id,
                "prediction_time": r.prediction_time.isoformat(),
                "predicted_return": r.predicted_return,
                "predicted_direction": r.predicted_direction,
                "confidence": r.confidence,
                "explanation": r.explanation,
                "model_version": r.model_version
            } for r in rows
        ]}
    finally:
        db.close()
