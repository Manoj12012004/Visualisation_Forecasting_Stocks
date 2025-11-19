import numpy as np
import pandas as pd
import json
import os
import sys
import tensorflow as tf
from sklearn.metrics import (
    mean_squared_error, r2_score,
    precision_score, recall_score, confusion_matrix,accuracy_score
)
import datetime
from pathlib import Path
from src.exception import CustomException
from src.services.model_store import save_model_to_db, save_predictions
from src.utils import save_object
from src.logger import logging

def focal_loss(gamma=1.0, alpha=0.35):
    def loss_fn(y_true, y_pred):
        bce = tf.keras.losses.binary_crossentropy(y_true, y_pred)
        p_t = y_true * y_pred + (1 - y_true) * (1 - y_pred)
        return alpha * (1 - p_t) ** gamma * bce
    return loss_fn

class SimpleTrainer:
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length

    # ----------------------------------------------------------
    # 1) DIRECTION MODEL (Binary classification)
    # ----------------------------------------------------------
    def build_direction_model(self, seq_shape, ind_shape):
        seq_input = tf.keras.Input(shape=seq_shape, name="seq_input")
        ind_input = tf.keras.Input(shape=ind_shape, name="ind_input")

        # Temporal CNN
        x = tf.keras.layers.Conv1D(64, 3, activation="relu", padding="causal")(seq_input)
        x = tf.keras.layers.Conv1D(64, 3, activation="relu", padding="causal")(x)

        # LSTM
        x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64,return_sequences=True))(x)
        att = tf.keras.layers.Attention()([x, x])
        x = tf.keras.layers.GlobalAveragePooling1D()(att)

        # Combine indicators
        combined = tf.keras.layers.concatenate([x, ind_input])

        # Dense
        combined = tf.keras.layers.Dense(128, activation="relu")(combined)
        combined = tf.keras.layers.Dropout(0.4)(combined)

        out = tf.keras.layers.Dense(1, activation="sigmoid")(combined)

        model = tf.keras.Model(inputs=[seq_input, ind_input], outputs=out)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(1e-3),
            loss=tf.keras.losses.BinaryCrossentropy(label_smoothing=0.02),
            # loss=focal_loss(gamma=1.5, alpha=0.5),
            metrics=["accuracy"]
        )
        return model

    # ----------------------------------------------------------
    # 2) RETURN MODEL (Regression)
    # ----------------------------------------------------------
    def build_return_model(self, seq_shape, ind_shape):
        seq_input = tf.keras.Input(shape=seq_shape, name="seq_input")
        ind_input = tf.keras.Input(shape=ind_shape, name="ind_input")

        x = tf.keras.layers.Conv1D(64, 3, activation="relu", padding="causal")(seq_input)
        x = tf.keras.layers.Conv1D(64, 3, activation="relu", padding="causal")(x)

        x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64,return_sequences=True))(x)
        att = tf.keras.layers.Attention()([x, x])
        x = tf.keras.layers.GlobalAveragePooling1D()(att)
        combined = tf.keras.layers.concatenate([x, ind_input])

        combined = tf.keras.layers.Dense(64, activation="relu")(combined)
        combined = tf.keras.layers.Dropout(0.3)(combined)

        out = tf.keras.layers.Dense(1)(combined)

        model = tf.keras.Model(inputs=[seq_input, ind_input], outputs=out)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(1e-3),
            loss=tf.keras.losses.Huber(delta=1.0),
            metrics=["mae"]
        )
        return model

    # ----------------------------------------------------------
    # TRAIN DIRECTION
    # ----------------------------------------------------------
    def train_direction(self, X_seq, X_ind, y_dir):
        seq_shape = (X_seq.shape[1], X_seq.shape[2])
        ind_shape = (X_ind.shape[1],)

        model = self.build_direction_model(seq_shape, ind_shape)

        n = len(X_seq)
        split = int(n * 0.8)
        X_seq_train, X_seq_val = X_seq[:split], X_seq[split:]
        X_ind_train, X_ind_val = X_ind[:split], X_ind[split:]
        y_train, y_val = y_dir[:split], y_dir[split:]

        from sklearn.utils.class_weight import compute_class_weight

        classes = np.unique(y_train)
        weights = compute_class_weight("balanced", classes=classes, y=y_train)
        class_weights = {int(c): float(w) for c, w in zip(classes, weights)}

        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=1e-6)
        ]

        model.fit(
            [X_seq_train, X_ind_train], y_train,
            validation_data=([X_seq_val, X_ind_val], y_val),
            epochs=35,
            batch_size=32,
            verbose=1,
            callbacks=callbacks,
            class_weight=class_weights
        )

        # Eval
        y_val_prob = model.predict([X_seq_val, X_ind_val], verbose=0).flatten()
        signal = np.zeros_like(y_val_prob, dtype=int)
        signal[y_val_prob > 0.55] = 1     # UP
        signal[y_val_prob < 0.45] = -1    # DOWN
        # 0 = NO TRADE
        trade_mask = signal != 0
        if np.any(trade_mask):
            y_true_trade = y_val[trade_mask]
            y_pred_trade = (signal[trade_mask] == 1).astype(int)   # convert -1 -> 0
            precision_trade = float(precision_score(y_true_trade, y_pred_trade, zero_division=0))
            recall_trade = float(recall_score(y_true_trade, y_pred_trade, zero_division=0))
            acc_trade = float(accuracy_score(y_true_trade, y_pred_trade))
            cm_trade = confusion_matrix(y_true_trade, y_pred_trade).tolist()
            signals_count = int(np.sum(trade_mask))
            no_trade_count = int(np.sum(~trade_mask))
        else:
            # No trade signals were generated in validation
            precision_trade = 0.0
            recall_trade = 0.0
            acc_trade = 0.0
            cm_trade = [[0, 0], [0, 0]]
            signals_count = 0
            no_trade_count = len(signal)

        y_pred_binary = (y_val_prob > 0.5).astype(int)
        mask = ~np.isnan(y_val_prob) & ~np.isnan(y_val)
        y_val_masked = y_val[mask]
        y_pred_binary_masked = y_pred_binary[mask]

        precision = float(precision_score(y_val_masked, y_pred_binary_masked, zero_division=0))
        recall = float(recall_score(y_val_masked, y_pred_binary_masked, zero_division=0))
        acc = float(np.mean(y_pred_binary_masked == y_val_masked))
        cm = confusion_matrix(y_val_masked, y_pred_binary_masked).tolist()
        
        
        return model, {
            "binary_metrics": {
                "accuracy": acc,
                "precision": precision,
                "recall": recall,
                "confusion_matrix": cm
            },
            "three_zone_metrics": {
                "accuracy": acc_trade,
                "precision": precision_trade,
                "recall": recall_trade,
                "confusion_matrix": cm_trade,
                "signals_count": int(np.sum(trade_mask)),
                "no_trade_count": int(np.sum(~trade_mask))}
        }, (X_seq_val, X_ind_val, y_val, y_val_prob, signal)

    # ----------------------------------------------------------
    # TRAIN RETURN REGRESSION
    # ----------------------------------------------------------
    def train_return(self, X_seq, X_ind, y_return_scaled):
        seq_shape = (X_seq.shape[1], X_seq.shape[2])
        ind_shape = (X_ind.shape[1],)

        model = self.build_return_model(seq_shape, ind_shape)

        n = len(X_seq)
        split = int(n * 0.8)
        X_seq_train, X_seq_val = X_seq[:split], X_seq[split:]
        X_ind_train, X_ind_val = X_ind[:split], X_ind[split:]
        y_train, y_val = y_return_scaled[:split], y_return_scaled[split:]

        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
        ]

        model.fit(
            [X_seq_train, X_ind_train], y_train,
            validation_data=([X_seq_val, X_ind_val], y_val),
            epochs=40,
            batch_size=32,
            verbose=1,
            callbacks=callbacks
        )

        y_val_pred = model.predict([X_seq_val, X_ind_val], verbose=0).flatten()

        return model, (X_seq_val, X_ind_val, y_val, y_val_pred)

    # ----------------------------------------------------------
    # REG METRICS
    # ----------------------------------------------------------
    @staticmethod
    def regression_metrics(y_true, y_pred):
        # mask NaNs, ensure lengths
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        mask = ~np.isnan(y_true) & ~np.isnan(y_pred)
        y_true_m, y_pred_m = y_true[mask], y_pred[mask]

        if len(y_true_m) == 0:
            raise ValueError("No valid samples for regression metrics after masking NaNs.")

        return {
            "rmse": float(np.sqrt(mean_squared_error(y_true_m, y_pred_m))),
            "r2": float(r2_score(y_true_m, y_pred_m))
        }


# ----------------------------------------------------------
# MAIN TRAIN FUNCTION — simplified and correct
# ----------------------------------------------------------

def train_two_stage_and_persist(symbol, df, transformer, model_store_path="artifacts/models/", db_session=None):
    try:
        # 1) transform
        X_seq, X_ind, y_return, y_dir, feat, vol_array = transformer.fin_data_transform(df)

        # 2) split chronological

        # 3) fit scalers only on TRAIN part
        n = len(X_seq)
        split = int(n * 0.8)
        transformer.fit_train_scalers(X_ind[:split], y_return[:split])

        X_ind_scaled, y_return_scaled = transformer.apply_train_scalers(X_ind, y_return)

        vol_train = vol_array[:split]
        vol_val = vol_array[split:]
        
        trainer = SimpleTrainer(sequence_length=transformer.sequence_length)

        # --------------------
        # Train Direction
        # --------------------
        direction_model, dir_metrics, dir_val = trainer.train_direction(
            X_seq, X_ind_scaled, y_dir
        )

        # --------------------
        # Train Return
        # --------------------
        return_model, ret_val = trainer.train_return(
            X_seq, X_ind_scaled, y_return_scaled
        )

        # inverse scale regression preds
        X_seq_val_r, X_ind_val_r, y_val_scaled, y_pred_scaled = ret_val
        
        y_val_norm = transformer.target_scaler.inverse_transform(y_val_scaled.reshape(-1, 1)).flatten()
        y_pred_norm = transformer.target_scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()

        if len(vol_val) >= len(y_val_norm):
            vol_for_val = vol_val[-len(y_val_norm):]
        else:
            # fallback: repeat or pad — but this indicates something odd in sequence build
            vol_for_val = np.pad(vol_val, (max(0, len(y_val_norm)-len(vol_val)), 0), mode="edge")[-len(y_val_norm):]

        y_val_actual = (y_val_norm * vol_for_val).astype(np.float32)
        y_pred_actual = (y_pred_norm * vol_for_val).astype(np.float32)

        reg_metrics = trainer.regression_metrics(y_val_actual, y_pred_actual)

        # --------------------
        # Save models
        # --------------------
        model_dir = Path(model_store_path) / symbol
        model_dir.mkdir(parents=True, exist_ok=True)

        dir_path = model_dir / f"{symbol}_direction.keras"
        ret_path = model_dir / f"{symbol}_return.keras"
        

        direction_model.save(dir_path)
        return_model.save(ret_path)
        
        tar_scaler_path=model_dir/f"{symbol}_target_scaler.pkl"
        ind_scaler_path=model_dir/f"{symbol}_ind_scaler.pkl"
        save_object(tar_scaler_path, transformer.target_scaler)
        save_object(ind_scaler_path, transformer.indicator_scaler)

        # --------------------
        # DB save
        # --------------------
        predictions = None
        db_result = None
        if db_session:
            try:
                binary_metrics = dir_metrics.get("binary_metrics", {})
                precision_db = binary_metrics.get("precision", 0.0)
                recall_db = binary_metrics.get("recall", 0.0)
                accuracy_db = binary_metrics.get("accuracy", 0.0)
                model_saved, model_row = save_model_to_db(
                    session=db_session,
                    stock_symbol=symbol.upper(),
                    accuracy=accuracy_db,
                    direction_model_path=str(dir_path),
                    return_model_path=str(ret_path),
                    ind_scaler_path=str(ind_scaler_path),
                    target_scaler_path=str(tar_scaler_path),
                    rmse=reg_metrics["rmse"],
                )
                db_result = {"saved": model_saved, "db_row": model_row}
                _, _, _, y_val_prob_array, signal_array = dir_val
                last_signal = int(signal_array[-1])  # -1,0,1

                if last_signal == 1:
                    predicted_direction = 1
                    signal_str = "Buy"
                elif last_signal == -1:
                    predicted_direction = 0
                    signal_str = "Sell"
                else:
                    predicted_direction = 0
                    signal_str = "NoTrade"
                # last val pred
                predictions = save_predictions(
                    session=db_session,
                    stock_symbol=symbol.upper(),
                    prediction_time=datetime.datetime.now(),
                    predicted_return=float(y_pred_actual[-1]),
                    signal=signal_str,
                    confidence=float(max(precision_db, recall_db)),
                )
            except Exception as e:
                raise CustomException(e, sys)

        return {
            "symbol": symbol,
            "regression_metrics": reg_metrics,
            "direction_metrics": dir_metrics,
            "paths": {
                "direction": str(dir_path),
                "return": str(ret_path),
            },
            "db_result": db_result,
            "predictions": predictions
        }

    except Exception as e:
        raise CustomException(e, sys)
