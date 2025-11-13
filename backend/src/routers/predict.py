from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from src.database.connection import SessionLocal
from src.database.models import Models
from src.utils import load_obj
from src.routers.train import train_model
from src.pipeline.predict_pipeline import Predict
import threading
import sys
import numpy as np
import tensorflow as tf
import pickle
from pathlib import Path
from src.pipeline.train_pipeline import Train
from src.exception import CustomException
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from typing import List, Dict, Any

router = APIRouter()

class PredictRequest(BaseModel):
    forecast_days: int

class PredictResponse(BaseModel):
    symbol: str
    current_price: float
    predicted_return_pct: float
    predicted_price: float
    direction_probability: float
    signal: str
    confidence: float
    interpretation: str
@router.get('/stocks/{symbol}/predict_multi_horizon')
def predict_multi_horizon(
    symbol: str,
    horizons: str = Query("1,3,5,7,10,15,30", description="Comma-separated forecast horizons in days")
):
    """Predict stock returns for multiple time horizons using two-stage model.
    
    Educational notes:
    - Each horizon shows expected return % and predicted price
    - Direction probability indicates confidence (>0.65 = strong UP, <0.35 = strong DOWN)
    - Longer horizons have higher uncertainty (wider confidence intervals)
    - Use this to plan entry/exit points across different timeframes
    """
    try:
        db = SessionLocal()
        sym = symbol.upper()
        
        # Parse horizons
        horizon_list = [int(h.strip()) for h in horizons.split(',')]
        
        # Load models and scaler
        model_base = Path('artifacts/models') / sym
        direction_model_path = model_base / f"{sym}_direction.keras"
        return_model_path = model_base / f"{sym}_return.keras"
        scaler_path = model_base / f"{sym}_scaler_y.pkl"
        
        if not direction_model_path.exists() or not return_model_path.exists():
            return {
                "status": "Model not trained",
                "message": f"Train model for {sym} first using /stocks/{sym}/train",
                "learning_tip": "Models must be trained before making predictions"
            }
        
        direction_model = tf.keras.models.load_model(str(direction_model_path))
        return_model = tf.keras.models.load_model(str(return_model_path))
        
        with open(scaler_path, 'rb') as f:
            scaler_y = pickle.load(f)
        
        # Get latest data
        ingestor = DataIngestion(sym)
        raw_df = ingestor.fin_data_ingestion()
        transformer = DataTransformation()
        X_seq, X_ind, y_return_scaled, y_dir, features, _ = transformer.fin_data_transform(raw_df)
        
        if X_seq.shape[0] == 0:
            raise HTTPException(status_code=400, detail="Insufficient data")
        
        # Get current price
        raw_df = raw_df.sort_values("date").reset_index(drop=True)
        last_close = float(raw_df['close'].iloc[-1])

        
        # Multi-horizon predictions
        results = {}
        print(X_seq)
        for horizon in horizon_list:
            # Iterative prediction
            X_seq_current = X_seq[-1:].copy().astype(np.float32)
            X_ind_current = X_ind[-1:].copy().astype(np.float32)
            
            cumulative_return = 0.0
            direction_probs = []
            
            for step in range(horizon):
                # Predict direction and return for next day
                prob_up = float(direction_model.predict([X_seq_current, X_ind_current], verbose=0).flatten()[0])
                pred_return_scaled = float(return_model.predict([X_seq_current, X_ind_current], verbose=0).flatten()[0])
                pred_return_pct = float(scaler_y.inverse_transform([[pred_return_scaled]])[0][0])
                
                cumulative_return += pred_return_pct
                direction_probs.append(prob_up)
                
                # Update sequence for next iteration (simplified - assumes features repeat)
                if step < horizon - 1:
                    # Shift sequence
                    X_seq_current = np.roll(X_seq_current, -1, axis=1)
                    # Update last timestep with prediction
                    X_seq_current[0, -1, 0] = pred_return_scaled  # scaled return as proxy
            
            avg_prob_up = float(np.mean(direction_probs))
            predicted_price = round(last_close * (1 + cumulative_return / 100.0), 2)
            
            # Generate signal
            if avg_prob_up >= 0.65 and cumulative_return > 0:
                signal = "STRONG BUY"
            elif avg_prob_up >= 0.55 and cumulative_return > 0:
                signal = "BUY"
            elif avg_prob_up <= 0.35 and cumulative_return < 0:
                signal = "STRONG SELL"
            elif avg_prob_up <= 0.45 and cumulative_return < 0:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            results[f"{horizon}d"] = {
                "horizon_days": horizon,
                "predicted_return_pct": round(cumulative_return, 2),
                "predicted_price": predicted_price,
                "direction_probability": round(avg_prob_up, 3),
                "signal": signal,
                "confidence": round(abs(avg_prob_up - 0.5) * 200, 1),
                "interpretation": f"{signal}: {cumulative_return:+.2f}% expected in {horizon} days"
            }
        
        return {
            "symbol": sym,
            "current_price": last_close,
            "predictions": results,
            "learning_notes": {
                "how_to_read": "Higher confidence (>70) suggests stronger signal",
                "direction_probability": ">0.65 = bullish, <0.35 = bearish, 0.4-0.6 = neutral",
                "use_case": "Compare short-term (1-5d) vs long-term (15-30d) for trend confirmation"
            }
        }
        
    except Exception as e:
        raise CustomException(e, sys)
    finally:
        db.close()

