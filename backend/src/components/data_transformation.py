import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import ta.momentum
from src.logger import logging
import sys
import ta
from src.exception import CustomException
from src.utils import scalar,save_object

class DataTransformation:
    def __init__(self, sequence_length=60):
        self.sequence_length = sequence_length
        self.scaler = scalar()

    def create_sequences(self, data):
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i][0])
        return np.array(X), np.array(y)

    def initiate_data_transformation(self, data):
        try:
            logging.info("Starting Data Transformation...")
            data['SMA_20']=data['close'].rolling(window=20).mean()
            data['SMA_50']=data['close'].rolling(window=50).mean()
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            data['RSI'] = 100 - (100 / (1 + rs))
            ema_12=data['close'].ewm(span=12,adjust=False).mean()
            ema_26=data['close'].ewm(span=26,adjust=False).mean()
            data['MACD']=ema_12-ema_26
            data['Signal']=data['MACD'].ewm(span=9,adjust=False).mean()
            data['AvgVolume']=data['volume'].rolling(window=20).mean()
            data=data.dropna()
            features = ['close', 'RSI', 'MACD', 'Signal', 'SMA_20', 'SMA_50', 'volume']
            technical_indicators = ['RSI', 'MACD', 'Signal', 'SMA_20', 'SMA_50']
            data=data[features]
            scaled_data = self.scaler.fit_transform(data)
            save_object("/backend/artifacts/scaler.pkl", self.scaler)
            X, y = self.create_sequences(scaled_data)
            
            return X,y,data[technical_indicators],features
        except Exception as e:
            raise CustomException(e,sys)
