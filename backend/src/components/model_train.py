
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential,Model
from tensorflow.keras.layers import LSTM, Dense,Dropout, GRU, Input,LayerNormalization, MultiHeadAttention,Flatten,Conv1D,MaxPooling1D,Concatenate
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import json
from statsmodels.tsa.stattools import adfuller
import io
import shap
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from src.utils import scalar,load_obj,save_object
from src.exception import CustomException
import sys


def hybrid_model(input_shape):
    inp=Input(shape=input_shape)
    lstm_out=LSTM(100,return_sequences=True)(inp)
    lstm_out=Dropout(0.3)(lstm_out)
    attn_out=MultiHeadAttention(num_heads=4,key_dim=16)(lstm_out,lstm_out)
    attn_out=LayerNormalization()(attn_out)
    attn_out=Dropout(0.2)(attn_out)
    flat=Flatten()(attn_out)
    dense1 = Dense(64, activation='relu')(flat)
    dense2 = Dropout(0.2)(dense1)
    dense3 = Dense(32, activation='relu')(dense2)
    out = Dense(1, activation='linear')(dense3)
    model = Model(inputs=inp, outputs=out)
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

class Model_Trainer:
    def __init__(self):
        self.order = (5, 1, 0)  # Default ARIMA order (p,d,q)
        self.scaler = load_obj('artifacts/scaler/scaler.pkl')
        self.close_scaler=load_obj('artifacts/scaler/close_scalar.pkl')
        
    def CNN_LSTM_hybrid(self, X_seq, X_ind, y_return, y_dir):
        
        seq_input = tf.keras.Input(shape=(X_seq.shape[1], X_seq.shape[2]), name="seq_input")
        ind_input = tf.keras.Input(shape=(X_ind.shape[1],), name="ind_input")

        # --- CNN Feature Extractor ---
        x = tf.keras.layers.Conv1D(128, 3, activation="relu")(seq_input)
        x = tf.keras.layers.Conv1D(64, 3, activation="relu")(x)
        x = tf.keras.layers.MaxPooling1D(2)(x)
        x = tf.keras.layers.LSTM(128, return_sequences=False)(x)
        x = tf.keras.layers.LayerNormalization()(x)
        x = tf.keras.layers.Dropout(0.4)(x)

        combined = tf.keras.layers.concatenate([x, ind_input])
        dense = tf.keras.layers.Dense(128, activation="relu")(combined)
        dense = tf.keras.layers.Dropout(0.4)(dense)

        # --- Dual Outputs ---
        out_return = tf.keras.layers.Dense(1, name="return_output")(dense)
        out_direction = tf.keras.layers.Dense(1, activation="sigmoid", name="direction_output")(dense)

        model = tf.keras.Model(inputs=[seq_input, ind_input],
                            outputs=[out_return, out_direction])

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss={
                "return_output": "mse",
                "direction_output": "binary_crossentropy"
            },
            loss_weights={"return_output": 0.4, "direction_output": 0.6},
            metrics={"direction_output": ["accuracy"]}
        )
        return model


    def CNN_LSTM(self,X_seq,X_ind,y):
        callbacks = [
                EarlyStopping(patience=5, restore_best_weights=True),
                ReduceLROnPlateau(patience=3, factor=0.5, min_lr=1e-6)
            ]
        timesteps = X_seq.shape[1]
        n_seq_feats = X_seq.shape[2]
        ind_dim = X_ind.shape[1]
        seq_input = Input(shape=(timesteps, n_seq_feats))
        x1=Conv1D(filters=32,kernel_size=3,activation='relu')(seq_input)
        x1=MaxPooling1D(pool_size=2)(x1)
        x1=LSTM(64)(x1)
        x1=Dense(64,activation='relu')(x1)
        ind_input=Input(shape=(ind_dim,))
        y1=Dense(32,activation='relu')(ind_input)
        y1=Dense(32,activation='relu')(y1)
        
        combined=Concatenate()([x1,y1])
        z1=Dense(64,activation='relu')(combined)
        z1=Dropout(0.3)(z1)
        z1=Dense(1,activation='linear')(z1)
        
        model=Model(inputs=[seq_input,ind_input],outputs=z1)
        model.compile(optimizer=Adam(learning_rate=0.001),loss='mse')
        
        model.fit(
            [X_seq,X_ind],y,
            validation_split=0.2,
            epochs=30,
            batch_size=32,
            callbacks=callbacks
        )
        return model
        
    def train_hybrid(self, X, y, features):
        model = hybrid_model((X.shape[1], X.shape[2]))
        early_stop = EarlyStopping(monitor='val_loss', patience=5)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6, verbose=1)
        train_size = int(len(X) * 0.8)
        X_train, X_val = X[:train_size], X[train_size:]
        y_train, y_val = y[:train_size], y[train_size:]
        model.fit(
            X_train, y_train,
            epochs=20,
            batch_size=32,
            validation_data=(X_val, y_val),
            callbacks=[early_stop, reduce_lr]
        )
        # save_object('artifacts/scaler/scaler.pkl', self.scaler)
        return model
            
    def evaluate_rmse(self, y_true, y_pred):
        return np.sqrt(np.mean((y_true - y_pred) ** 2))

    def evaluate_r2(self, y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot)
    
    def train_cnn(self, stock_symbol, X_seq_scaled, X_ind_scaled, y_scaled, features,scaler_y):
        try:
            train_size = int(len(X_seq_scaled) * 0.8)

            X_seq_train = X_seq_scaled[:train_size]
            X_seq_val   = X_seq_scaled[train_size:]

            X_ind_train = X_ind_scaled[:train_size]
            X_ind_val   = X_ind_scaled[train_size:]

            y_train     = y_scaled[:train_size]
            y_val       = y_scaled[train_size:]
            # Train the model
            model = self.CNN_LSTM(X_seq=X_seq_train,X_ind=X_ind_train, y=y_train)
            # y_pred_scaled = model.predict([X_seq_val, X_ind_val])
            # y_pred_scaled = y_pred_scaled.numpy().reshape(-1) if isinstance(y_pred_scaled, tf.Tensor) else y_pred_scaled.reshape(-1)
            # y_val = y_val.numpy().reshape(-1) if isinstance(y_val, tf.Tensor) else y_val.reshape(-1)

            y_pred_scaled = model.predict([X_seq_val, X_ind_val],verbose=0)
            y_pred_scaled = y_pred_scaled.reshape(-1)
            y_val = y_val.reshape(-1)
            
            # Inverse transform
            y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
            y_val = scaler_y.inverse_transform(y_val.reshape(-1, 1)).flatten()
            # idx = np.random.choice(X_seq_train.shape[0], size=100, replace=False)
            n_bg = min(100, X_seq_train.shape[0])
            replace_flag = X_seq_train.shape[0] < 100
            idx = np.random.choice(X_seq_train.shape[0], size=n_bg, replace=replace_flag)
            
            X_seq_train_tensor = tf.convert_to_tensor(X_seq_train, dtype=tf.float32)
            X_ind_train_tensor = tf.convert_to_tensor(X_ind_train, dtype=tf.float32)
            X_seq_bg = tf.gather(X_seq_train_tensor, indices=idx)
            X_ind_bg = tf.gather(X_ind_train_tensor, indices=idx)
            X_seq_val_tensor = tf.convert_to_tensor(X_seq_val[:10], dtype=tf.float32)
            X_ind_val_tensor = tf.convert_to_tensor(X_ind_val[:10], dtype=tf.float32)
             # 10 samples for SHAP
            # SHAP background
            tf.keras.backend.clear_session()
            tf.config.run_functions_eagerly(False)
            explainer = shap.GradientExplainer(model, data=[X_seq_bg, X_ind_bg])
            shap_values = explainer.shap_values([X_seq_val_tensor.numpy(), X_ind_val_tensor.numpy()])
            # SHAP serialization
            def _to_serializable(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, (list, tuple)):
                    return [_to_serializable(o) for o in obj]
                return obj
            
            model_explain_serializable = {
                "shap_values_seq": _to_serializable(shap_values[0]), # for sequence input
                "shap_values_ind": _to_serializable(shap_values[1]), # for indicator input
                "X_test_seq": _to_serializable(X_seq_val[:10]),
                "X_test_ind": _to_serializable(X_ind_val[:10]),
                "features": features
            }

            # Evaluation
            rmse = self.evaluate_rmse(y_true=y_val, y_pred=y_pred)
            r2 = self.evaluate_r2(y_true=y_val, y_pred=y_pred)

            return {
                "stock_symbol": stock_symbol,
                "best_model_name": "CNN-LSTM",
                "best_predictions": y_pred.tolist(),
                "best_model_object":model,
                "model_actuals": y_val.tolist(),
                "model_explain": json.dumps(model_explain_serializable),
                "best_rmse": rmse,
                "best_r2": r2,
            }
        except Exception as e:
            raise CustomException(e,sys)

    def train_cnn_hybrid(self, stock_symbol, X_seq, X_ind, y_return_scaled, y_dir, features, scaler_y):
        try:
            train_size = int(len(X_seq) * 0.8)
            X_seq_train, X_seq_val = X_seq[:train_size], X_seq[train_size:]
            X_ind_train, X_ind_val = X_ind[:train_size], X_ind[train_size:]
            y_return_train, y_return_val = y_return_scaled[:train_size], y_return_scaled[train_size:]
            y_dir_train, y_dir_val = y_dir[:train_size], y_dir[train_size:]

            model = self.CNN_LSTM_hybrid(X_seq_train, X_ind_train, y_return_train, y_dir_train)
            callbacks = [
                tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
                tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, verbose=1)
            ]

            model.fit(
                [X_seq_train, X_ind_train],
                {"return_output": y_return_train, "direction_output": y_dir_train},
                validation_data=(
                    [X_seq_val, X_ind_val],
                    {"return_output": y_return_val, "direction_output": y_dir_val}
                ),
                epochs=100,
                batch_size=32,
                callbacks=callbacks,
                verbose=1
            )

            # --- Predictions ---
            pred_return_scaled, pred_dir_prob = model.predict([X_seq_val, X_ind_val], verbose=0)
            pred_return = scaler_y.inverse_transform(pred_return_scaled).flatten()
            pred_dir = (pred_dir_prob.flatten() > 0.5).astype(int)

            # --- Evaluation ---
            y_true_return = scaler_y.inverse_transform(y_return_val.reshape(-1, 1)).flatten()
            rmse = np.sqrt(np.mean((y_true_return - pred_return) ** 2))
            r2 = 1 - np.sum((y_true_return - pred_return) ** 2) / np.sum(
                (y_true_return - np.mean(y_true_return)) ** 2)
            dir_acc = np.mean(pred_dir == y_dir_val)
            # explainer = shap.GradientExplainer(model, data=[X_seq_bg, X_ind_bg])
            # shap_values = explainer.shap_values([X_seq_val[:10], X_ind_val[:10]])
            
            # model_explain_serializable = {
            #     "shap_values_seq": shap_values[0].tolist(),
            #     "shap_values_ind": shap_values[1].tolist(),
            #     "X_test_seq": X_seq_val[:10].tolist(),
            #     "X_test_ind": X_ind_val[:10].tolist(),
            #     "features": features
            # }

            print({
                "stock_symbol": stock_symbol,
                "best_model_name": "CNN-LSTM-HYBRID",
                "best_model_object": model,
                "model_actuals": y_true_return.tolist(),
                "best_predictions": pred_return.tolist(),
                "model_explain": None,  # SHAP explanation can be added similarly as before
                "best_rmse": float(rmse),
                "best_r2": float(r2),
                "direction_accuracy": float(dir_acc),
                "scaler_y": scaler_y
            })
            return {
                "stock_symbol": stock_symbol,
                "best_model_name": "CNN-LSTM-HYBRID",
                "best_model_object": model,
                "model_actuals": y_true_return.tolist(),
                "best_predictions": pred_return.tolist(),
                "model_explain": None,  # SHAP explanation can be added similarly as before
                "best_rmse": float(rmse),
                "best_r2": float(r2),
                "direction_accuracy": float(dir_acc),
                "scaler_y": scaler_y
            }
        except Exception as e:
            raise CustomException(e, sys)

    def initiate_train(self,stock_symbol,X,y,features):
        results = {}
        models={}
        
        train_size=int(len(X)*0.8)
        X_train,X_test=X[:train_size],X[train_size:]
        y_train,y_test=y[:train_size],y[train_size:]

        lstm_model=self.train_hybrid(X_train,y_train,features)
        background = X_train[np.random.choice(X_train.shape[0], size=100, replace=False)]
        explainer = shap.GradientExplainer(lstm_model, data=background)
        shap_values = explainer.shap_values(X_test[:10])
        # shap.summary_plot(shap_values[0], feature_names=features, show=False)
        lstm_pred=lstm_model.predict(X_test).flatten()
        models['LSTM']=lstm_model
        
        results['LSTM']={
            'predictions':lstm_pred,
            'actuals':y_test.flatten(),
            'rmse':self.evaluate_rmse(y_test.flatten(),lstm_pred),
            'r2':self.evaluate_r2(y_test.flatten(),lstm_pred)
        }
        model_explain_serializable = {
            "shap_values": shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
            "X_test": X_test[:10].tolist() if isinstance(X_test, np.ndarray) else X_test,
            "features": features
        }
        
        return {
            "stock_symbol":stock_symbol,
            "best_model_name": "LSTM",  # Assuming LSTM is the best model for now
            "best_model_object": models['LSTM'],
            "best_predictions": self.close_scaler.inverse_transform(results['LSTM']["predictions"].reshape(-1,1)).flatten().tolist(),
            "model_actuals": self.close_scaler.inverse_transform(results['LSTM']["actuals"].reshape(-1,1)).flatten().tolist(),
            "model_explain":json.dumps(model_explain_serializable),
            "best_rmse": results['LSTM']["rmse"],
            "best_r2": results['LSTM']["r2"],
        }
        