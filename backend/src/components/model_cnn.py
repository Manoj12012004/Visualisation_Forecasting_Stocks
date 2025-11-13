# Required imports (put near top of file)
import numpy as np
import pandas as pd
import json
import os
import sys
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_squared_error, r2_score,
    precision_score, recall_score, confusion_matrix
)
import datetime
from pathlib import Path
from src.exception import CustomException
from src.services.model_store import save_model_to_db,save_predictions
from src.utils import save_object
from src.logger import logging
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, precision_score, recall_score, confusion_matrix
from keras.models import Model
from keras.layers import Input, Conv1D, BatchNormalization, Dropout, Bidirectional, LSTM, LayerNormalization, Dense, concatenate
from keras.optimizers import Adam
import ta
import shap

# If you use ta already, it's used in DataTransformation; keep it.
# Also reuse existing helpers: save_object, save_model_to_db, CustomException, SessionLocal, etc.

class TwoStageTrainer:
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length

    def build_direction_model(self, seq_shape, ind_shape):
        seq_input = tf.keras.Input(shape=seq_shape, name="seq_input")
        ind_input = tf.keras.Input(shape=ind_shape, name="ind_input")

        x = tf.keras.layers.Conv1D(128, 5, activation="relu", padding="causal")(seq_input)
        x = tf.keras.layers.Conv1D(64, 3, activation="relu", padding="causal")(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Dropout(0.3)(x)
        x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(128, return_sequences=False))(x)
        x = tf.keras.layers.LayerNormalization()(x)

        combined = tf.keras.layers.concatenate([x, ind_input])
        combined = tf.keras.layers.Dense(256, activation="relu")(combined)
        combined = tf.keras.layers.Dropout(0.5)(combined)
        combined = tf.keras.layers.Dense(128, activation="relu")(combined)

        out_dir = tf.keras.layers.Dense(1, activation="sigmoid", name="direction_output")(combined)

        model = tf.keras.Model(inputs=[seq_input, ind_input], outputs=out_dir, name="cnn_bilstm_direction")
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss="binary_crossentropy",
            metrics=["accuracy"]
        )
        return model

    def build_return_model_from_direction(self, direction_model):
        # Freeze most layers of direction_model except last dense block
        for layer in direction_model.layers:
            layer.trainable = True  # we will selectively freeze below

        # find index to freeze until (all except last 3 dense layers ideally)
        # We'll freeze everything up to before the final Dense(128) + dropout block if exists
        # A safe approach: freeze all Conv/LSTM layers, keep Dense layers trainable
        for layer in direction_model.layers:
            if isinstance(layer, (tf.keras.layers.Conv1D, tf.keras.layers.Bidirectional, tf.keras.layers.LSTM, tf.keras.layers.BatchNormalization)):
                layer.trainable = False

        # attach a regression output to the same combined dense representation if exists
        # find the last layer before the final Dense(128) by name search fallback
        last_common = direction_model.get_layer(index=-3).output if len(direction_model.layers) >= 3 else direction_model.outputs[0]
        out_return = tf.keras.layers.Dense(1, name="return_output")(last_common)

        model = tf.keras.Model(inputs=direction_model.inputs, outputs=out_return, name="cnn_bilstm_return")
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
            loss="mse",
            metrics=["mae"]
        )
        return model

    def fit_direction(self, X_seq, X_ind, y_dir):
        seq_shape = (X_seq.shape[1], X_seq.shape[2])
        ind_shape = (X_ind.shape[1],)
        model = self.build_direction_model(seq_shape, ind_shape)

        # train/val split
        X_seq_train, X_seq_val, X_ind_train, X_ind_val, y_train, y_val = train_test_split(
            X_seq, X_ind, y_dir, test_size=0.2, random_state=42, stratify=y_dir if len(np.unique(y_dir)) > 1 else None
        )

        # class weight
        pos = np.sum(y_train == 1)
        neg = np.sum(y_train == 0)
        if pos == 0 or neg == 0:
            class_weights = None
        else:
            w0 = (1 / neg) * (len(y_train) / 2.0)
            w1 = (1 / pos) * (len(y_train) / 2.0)
            class_weights = {0: w0, 1: w1}

        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, verbose=1)
        ]

        history = model.fit(
            [X_seq_train, X_ind_train],
            y_train,
            validation_data=([X_seq_val, X_ind_val], y_val),
            epochs=60,
            batch_size=32,
            class_weight=class_weights,
            callbacks=callbacks,
            verbose=1
        )

        # Eval on validation
        y_val_pred_prob = model.predict([X_seq_val, X_ind_val], verbose=0).flatten()
        y_val_pred = (y_val_pred_prob > 0.5).astype(int)
        precision = precision_score(y_val, y_val_pred, zero_division=0)
        recall = recall_score(y_val, y_val_pred, zero_division=0)
        cm = confusion_matrix(y_val, y_val_pred).tolist()

        dir_metrics = {
            "val_accuracy": float(np.mean(y_val_pred == y_val)),
            "precision": float(precision),
            "recall": float(recall),
            "confusion_matrix": cm
        }

        return model, history, dir_metrics, (X_seq_val, X_ind_val, y_val)

    def fine_tune_return(self, direction_model, X_seq, X_ind, y_return_scaled):
        # Build regression model that reuses direction_model base
        return_model = self.build_return_model_from_direction(direction_model)

        # train/val split
        X_seq_train, X_seq_val, X_ind_train, X_ind_val, y_train, y_val = train_test_split(
            X_seq, X_ind, y_return_scaled, test_size=0.2, random_state=42
        )

        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, verbose=1)
        ]

        history = return_model.fit(
            [X_seq_train, X_ind_train],
            y_train,
            validation_data=([X_seq_val, X_ind_val], y_val),
            epochs=60,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )

        y_val_pred_scaled = return_model.predict([X_seq_val, X_ind_val], verbose=0).flatten()

        # Return predictions and metrics computed by caller after inverse-scaling
        return return_model, history, (X_seq_val, X_ind_val, y_val, y_val_pred_scaled)

    def compute_regression_metrics(self, y_true, y_pred):
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))
        return {"rmse": rmse, "r2": r2}

# ---------- Integration function to be used by your endpoint ----------
def train_two_stage_and_persist(symbol, data, transformer_obj, model_store_path="artifacts/models/", db_session=None):
    """
    symbol: stock symbol
    data: raw DataFrame (or will call DataIngestion upstream)
    transformer_obj: instance of your DataTransformation class with fin_data_transform method
    model_store_path: folder where to save models/scalers
    db_session: optional DB session for save_model_to_db
    Returns a dictionary with metrics and model paths.
    """
    try:
        # 1) Transform data using your fin_data_transform (expects it returns same tuple)
        X_seq, X_ind, y_return_scaled, y_dir, features, scaler_y = transformer_obj.fin_data_transform(data)

        # quick sanity: need > minimal samples
        if X_seq.shape[0] < 200:
            # still allow but warn (you can adjust threshold)
            print(f"[train_two_stage] Warning: small dataset N={X_seq.shape[0]}")

        trainer = TwoStageTrainer(sequence_length=transformer_obj.sequence_length if hasattr(transformer_obj, "sequence_length") else 30)

        # Stage 1: direction
        direction_model, hist1, dir_metrics, dir_val_data = trainer.fit_direction(X_seq, X_ind, y_dir)

        # Save direction model
        model_store_path=Path(model_store_path)/symbol
        model_store_path.mkdir(parents=True, exist_ok=True)
        dir_model_path = model_store_path/f"{symbol}_direction.keras"
        direction_model.save(dir_model_path)

        # Stage 2: return fine-tune
        return_model, hist2, ret_val_tuple = trainer.fine_tune_return(direction_model, X_seq, X_ind, y_return_scaled)

        ret_model_path = model_store_path/f"{symbol}_return.keras"
        return_model.save(ret_model_path)

        # Prepare metrics: inverse-scale regression preds to original units
        X_seq_val_rt, X_ind_val_rt, y_val_scaled, y_val_pred_scaled = ret_val_tuple
        y_val_true = scaler_y.inverse_transform(y_val_scaled.reshape(-1, 1)).flatten()
        y_val_pred = scaler_y.inverse_transform(y_val_pred_scaled.reshape(-1, 1)).flatten()

        reg_metrics = trainer.compute_regression_metrics(y_val_true, y_val_pred)

        # Evaluate direction on the held-out val split from direction training
        X_seq_val_dir, X_ind_val_dir, y_val_dir = dir_val_data
        y_val_dir_prob = direction_model.predict([X_seq_val_dir, X_ind_val_dir], verbose=0).flatten()
        y_val_dir_pred = (y_val_dir_prob > 0.5).astype(int)
        dir_precision = float(precision_score(y_val_dir, y_val_dir_pred, zero_division=0))
        dir_recall = float(recall_score(y_val_dir, y_val_dir_pred, zero_division=0))
        dir_conf_mat = confusion_matrix(y_val_dir, y_val_dir_pred).tolist()
        dir_acc = float(np.mean(y_val_dir_pred == y_val_dir))

        # SHAP explainability for regression head (use small background)
        try:
            # prepare background from training split (sample up to 200)
            bg_n = min(200, X_seq.shape[0])
            idx_bg = np.random.choice(X_seq.shape[0], size=bg_n, replace=False)
            X_seq_bg = X_seq[idx_bg]
            X_ind_bg = X_ind[idx_bg]

            shap_explainer = shap.GradientExplainer(return_model, data=[X_seq_bg, X_ind_bg])
            # use a few validation samples for explanation
            expl_n = min(10, X_seq_val_rt.shape[0])
            shap_vals = shap_explainer.shap_values([X_seq_val_rt[:expl_n], X_ind_val_rt[:expl_n]])
            # shap_vals is list corresponding to outputs; for single regression output shap_vals may be array-like
            # make serializable
            def _to_list(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, (list, tuple)):
                    return [_to_list(o) for o in obj]
                return obj

            shap_serial = {
                "shap_values_seq": _to_list(shap_vals[0]) if isinstance(shap_vals, (list, tuple)) else _to_list(shap_vals),
                "shap_values_ind": _to_list(shap_vals[1]) if isinstance(shap_vals, (list, tuple)) and len(shap_vals) > 1 else None,
                "features": features
            }
            shap_json = json.dumps(shap_serial)
        except Exception as e:
            # don't fail training for shap issues
            print(f"[train_two_stage] SHAP failed: {e}")
            shap_json = None

        # Persist scaler and metadata
        scaler_path = model_store_path/f"{symbol}_scaler_y.pkl"
        try:
            save_object(scaler_path, scaler_y)  # use your existing save helper
        except Exception:
            # fallback: tf.keras.models.save_model can't save scaler; you have save_object
            print("[train_two_stage] Warning: scaler save failed")

        # Optionally save full model metadata into DB if session provided (mirror your earlier flow)
        db_result = None
        if db_session is not None:
            try:
                # Example: save_model_to_db(session=db, stock_symbol=symbol, accuracy=dir_acc, model_actuals=y_val_true.tolist(), model_preds=y_val_pred.tolist(), model_explain=shap_json, model_path=ret_model_path)
                model_saved, model_row = save_model_to_db(
                    session=db_session,
                    stock_symbol=symbol.upper(),
                    accuracy=dir_acc,
                    direction_model_path=str(dir_model_path),
                    return_model_path=str(ret_model_path),
                    scaler_path=str(scaler_path),
                    precision=dir_precision,
                    recall=dir_recall,
                    rmse=reg_metrics['rmse'],
                    r2_score=reg_metrics['r2'],
                )
                db_result = {"saved": model_saved, "db_row": model_row}
            except Exception as e:
                print(f"[train_two_stage] DB save failed: {e}")
            
            try:
                predictions=save_predictions(
                    session=db_session,
                    stock_symbol=symbol.upper(),
                    prediction_time=datetime.datetime.now(),
                    predicted_return=float(y_val_pred[-1]),
                    predicted_direction=int(y_val_dir_pred[-1]),
                    signal="Buy" if y_val_dir_pred[-1]==1 else "Sell",
                    confidence=float(max(dir_metrics['precision'], dir_metrics['recall'])),
                    explaination=shap_json
                )
            except Exception as e:
                raise CustomException(e,sys)

        result = {
            "stock_symbol": symbol,
            "direction_model_path": dir_model_path,
            "return_model_path": ret_model_path,
            "scaler_path": scaler_path,
            "regression_metrics": reg_metrics,
            "direction_metrics": {
                "accuracy": dir_acc,
                "precision": dir_precision,
                "recall": dir_recall,
                "confusion_matrix": dir_conf_mat
            },
            "model_explain": shap_serial if shap_json else None,
            "db_result": db_result,
            "predictions":predictions
        }
        return result

    except Exception as e:
        raise CustomException(e, sys)
