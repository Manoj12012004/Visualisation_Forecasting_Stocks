import numpy as np
import tensorflow as tf
from pathlib import Path
from src.utils import load_obj
from src.exception import CustomException
import sys

def load_trained_models(symbol, model_store_path="artifacts/models/"):
    """
    Loads direction model, return model, scalers.
    """
    try:
        base = Path(model_store_path) / symbol

        direction_model = tf.keras.models.load_model(base / f"{symbol}_direction.keras",
                                                     compile=False)
        return_model = tf.keras.models.load_model(base / f"{symbol}_return.keras",
                                                  compile=False)

        target_scaler = load_obj(base / f"{symbol}_target_scaler.pkl")
        ind_scaler = load_obj(base / f"{symbol}_ind_scaler.pkl")

        return direction_model, return_model, target_scaler, ind_scaler

    except Exception as e:
        raise CustomException(e, sys)


def make_prediction(symbol, df, transformer, model_store_path="artifacts/models/"):
    """
    Run prediction using latest trained model.

    Steps:
    1) Transform incoming DF
    2) Scale indicators using trained scaler
    3) Predict direction + scaled return
    4) Inverse-transform returns
    5) Combine hybrid rule → Buy/Sell/Hold
    """
    try:
        # Load trained models & scalers
        direction_model, return_model, target_scaler, ind_scaler = load_trained_models(
            symbol, model_store_path
        )

        # Fresh transform on full DF
        X_seq, X_ind, y_return, y_dir, feat, vol_array = transformer.fin_data_transform(df)

        # Apply only indicator scaler (ALREADY FITTED during training)
        X_ind_scaled = ind_scaler.transform(X_ind)

        # --- Single step prediction (use last sequence) ---
        last_seq = X_seq[-1].reshape(1, X_seq.shape[1], X_seq.shape[2])
        last_ind = X_ind_scaled[-1].reshape(1, -1)
        last_vol = vol_array[-1]

        # Direction
        prob = float(direction_model.predict([last_seq, last_ind], verbose=0)[0][0])

        # Return (scaled)
        pred_scaled = float(return_model.predict([last_seq, last_ind], verbose=0)[0][0])

        # Inverse scale using target scaler
        pred_norm = float(target_scaler.inverse_transform([[pred_scaled]])[0][0])

        # Multiply by volume normalization
        pred_actual = float(pred_norm * last_vol)

        # --- Final decision logic ---
        if prob > 0.52 and pred_actual > 0:
            direction = 1
            signal = "Buy"
        elif prob < 0.48 and pred_actual < 0:
            direction = 0
            signal = "Sell"
        else:
            direction = 0
            signal = "Hold"

        return {
            "symbol": symbol,
            "probability_up": prob,
            "predicted_return": pred_actual,
            "hybrid_direction": direction,
            "signal": signal,
            "confidence": max(prob, 1 - prob)
        }

    except Exception as e:
        raise CustomException(e, sys)
