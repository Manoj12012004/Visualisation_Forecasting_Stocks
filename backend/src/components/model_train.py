
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense,Dropout, GRU, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
# from prophet import Prophet
import base64
from xgboost import XGBRegressor
from statsmodels.tsa.stattools import adfuller
import io
from fastapi import Response
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from src.utils import scalar,load_obj,save_object

class Model_Trainer:
    def __init__(self):
        self.order = (5, 1, 0)  # Default ARIMA order (p,d,q)
        self.scaler = load_obj('/backend/artifacts/scaler.pkl')

    def train_lstm(self,X,y,features):
        
        # split = int(0.8 * len(X))
        # X_train, X_test = X[:split], X[split:]
        # y_train, y_test = y[:split], y[split:]

        # Build LSTM model
        model = Sequential()
        model.add(LSTM(100, return_sequences=True, input_shape=(60, len(features))))
        model.add(Dropout(0.3))
        model.add(LSTM(50))
        model.add(Dropout(0.2))
        model.add(Dense(1))

        model.compile(optimizer='adam', loss='mean_squared_error')

        # Callbacks
        early_stop = EarlyStopping(monitor='val_loss', patience=5)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6, verbose=1)

        # Train model
        history = model.fit(
            X, y,
            epochs=10,
            batch_size=32,
            validation_data=(X_test, y_test),
            callbacks=[early_stop, reduce_lr]
        )

        # Predict on test data
        # y_pred = model.predict(X_test)

        # Inverse scale predictions and true values (only Close price)
        # inv_pred = np.zeros((len(y_pred), len(features)))
        # inv_pred[:, 0] = y_pred[:, 0]

        # inv_true = np.zeros((len(y_test), len(features)))
        # inv_true[:, 0] = y_test

        # y_pred_unscaled = self.scaler.inverse_transform(inv_pred)[:, 0]
        # y_test_unscaled = self.scaler.inverse_transform(inv_true)[:, 0]

        # Plot results
        # plt.figure(figsize=(12, 6))
        # plt.plot(y_test_unscaled, label='Actual Close Price')
        # plt.plot(y_pred_unscaled, label='Predicted Close Price')
        # plt.title('LSTM Stock Price Prediction')
        # plt.xlabel('Time Steps')
        # plt.ylabel('Price')
        # plt.legend()
        
        # buf=io.BytesIO()
        # plt.savefig(buf, format='png')
        # plt.close()
        # buf.seek(0)
        # img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        

        # Optional: Evaluation metrics
        # from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        # mae = mean_absolute_error(y_test_unscaled, y_pred_unscaled)
        # mse = mean_squared_error(y_test_unscaled, y_pred_unscaled)
        # rmse = np.sqrt(mse)
        # r2 = r2_score(y_test_unscaled, y_pred_unscaled)

        # print(f"MAE: {mae:.4f}")
        # print(f"MSE: {mse:.4f}")
        # print(f"RMSE: {rmse:.4f}")
        # print(f"R^2 Score: {r2:.4f}")
        save_object('/backend/artifacts/scaler.pkl',self.scaler)
        return model
            
    def evaluate_rmse(self, y_true, y_pred):
        return np.sqrt(np.mean((y_true - y_pred) ** 2))

    def evaluate_r2(self, y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot)
    
    def initiate_train(self,X,y,features):
        results = {}
        models={}
        
        train_size=int(len(X)*0.8)
        X_train,X_test=X[:train_size],X[train_size:]
        y_train,y_test=y[:train_size],y[train_size:]
        
        print(X_train.shape,y_train.shape)

        lstm_model=self.train_lstm(X_train,y_train,features)
        lstm_pred=lstm_model.predict(X_test).flatten()
        models['LSTM']=lstm_model
        
        results['LSTM']={
            'predictions':lstm_pred,
            'actuals':y_test.flatten(),
            'rmse':self.evaluate_rmse(y_test.flatten(),lstm_pred),
            'r2':self.evaluate_r2(y_test.flatten(),lstm_pred)
        }
        
        return {
            "best_model_name": "LSTM",  # Assuming LSTM is the best model for now
            "best_model_object": models['LSTM'],
            "best_predictions": results['LSTM']["predictions"],
            "best_actuals": results['LSTM']["actuals"],
            "best_rmse": results['LSTM']["rmse"],
            "best_r2": results['LSTM']["r2"],
        }
        