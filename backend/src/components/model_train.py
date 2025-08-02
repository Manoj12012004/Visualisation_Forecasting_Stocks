
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
        self.scaler = load_obj('/backend/artifacts/scaler.pkl')
        self.close_scaler=load_obj('/backend/artifacts/close_scalar.pkl')
        
    def CNN_LSTM(self,X_seq,X_ind,y):
        callbacks = [
                EarlyStopping(patience=5, restore_best_weights=True),
                ReduceLROnPlateau(patience=3, factor=0.5, min_lr=1e-6)
            ]
        seq_input=Input(shape=(20,5))
        x1=Conv1D(filters=32,kernel_size=3,activation='relu')(seq_input)
        x1=MaxPooling1D(pool_size=2)(x1)
        x1=LSTM(64)(x1)
        x1=Dense(64,activation='relu')(x1)
        
        ind_input=Input(shape=(10,))
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
        save_object('artifacts/scaler/scaler.pkl', self.scaler)
        return model
            
    def evaluate_rmse(self, y_true, y_pred):
        return np.sqrt(np.mean((y_true - y_pred) ** 2))

    def evaluate_r2(self, y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot)
    
    def train_cnn(self, stock_symbol, X_seq_scaled, X_ind_scaled, y_scaled, features,scaler_y):
        try:
            X_seq_train, X_seq_val, X_ind_train, X_ind_val, y_train, y_val = train_test_split(
                X_seq_scaled, X_ind_scaled, y_scaled, test_size=0.2, random_state=42
            )
            # Train the model
            model = self.CNN_LSTM(X_seq=X_seq_scaled,X_ind=X_ind_scaled, y=y_scaled)
            y_pred_scaled = model.predict([X_seq_val, X_ind_val])
            y_pred_scaled = y_pred_scaled.numpy().reshape(-1) if isinstance(y_pred_scaled, tf.Tensor) else y_pred_scaled.reshape(-1)
            y_val = y_val.numpy().reshape(-1) if isinstance(y_val, tf.Tensor) else y_val.reshape(-1)

            # Inverse transform
            y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
            y_val = scaler_y.inverse_transform(y_val.reshape(-1, 1)).flatten()
            idx = np.random.choice(X_seq_train.shape[0], size=100, replace=False)
            
            X_seq_train_tensor = tf.convert_to_tensor(X_seq_train, dtype=tf.float32)
            X_ind_train_tensor = tf.convert_to_tensor(X_ind_train, dtype=tf.float32)
            X_seq_bg = tf.gather(X_seq_train_tensor, indices=idx)
            X_ind_bg = tf.gather(X_ind_train_tensor, indices=idx)
            X_seq_val_tensor = tf.convert_to_tensor(X_seq_val[:10], dtype=tf.float32)
            X_ind_val_tensor = tf.convert_to_tensor(X_ind_val[:10], dtype=tf.float32)
             # 10 samples for SHAP
            # SHAP background
            explainer = shap.GradientExplainer(model, data=[X_seq_bg, X_ind_bg])
            shap_values = explainer.shap_values([X_seq_val_tensor.numpy(), X_ind_val_tensor.numpy()])
            # SHAP serialization
            model_explain_serializable = {
                "shap_values_seq": shap_values[0].tolist(), # for sequence input
                "shap_values_ind": shap_values[1].tolist(), # for indicator input
                "X_test_seq": X_seq_val[:10].tolist(),
                "X_test_ind": X_ind_val[:10].tolist(),
                "features": features
            }

            # Evaluation
            rmse = mean_squared_error(y_true=y_val,y_pred= y_pred)
            r2 = r2_score(y_true=y_val, y_pred=y_pred)

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
        