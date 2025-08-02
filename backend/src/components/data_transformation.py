import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler,StandardScaler
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
        self.close_scaler=MinMaxScaler()
        

    def create_sequences(self, data):
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i][0])
        return np.array(X), np.array(y)

    def fin_data_transform(self,df):
        df['50ma']=df['close'].rolling(50).mean()
        df['200ma']=df['close'].rolling(200).mean()

        window = 14
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()

        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))

        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()

        df["MACD"] = ema_12 - ema_26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Histogram"] = df["MACD"] - df["Signal"]

        bb_window = 20
        df["BB_Middle"] = df["close"].rolling(bb_window).mean()
        df["BB_STD"] = df["close"].rolling(bb_window).std()

        df["BB_Upper"] = df["BB_Middle"] + (2 * df["BB_STD"])
        df["BB_Lower"] = df["BB_Middle"] - (2 * df["BB_STD"])

        df["volume_ma_20"] = df["volume"].rolling(20).mean()
        df["volume_spike"] = df["volume"] > 1.5 * df["volume_ma_20"]

        df['golden_cross']=(df['50ma']>df['200ma'])&(df['50ma'].shift(1)<=df['200ma'].shift(1))
        df['death_cross']=(df['50ma']<df['200ma'])&(df['50ma'].shift(1)>=df['200ma'].shift(1))
        
        seq_features = ['open', 'high', 'low', 'close', 'volume']
        indicator_features = [
            'RSI', 'MACD', 'Signal', 'MACD_Histogram',
            'BB_Middle', 'BB_Upper', 'BB_Lower',
            'volume_ma_20', 'golden_cross', 'death_cross'
        ]
        target_column = 'close'  # or 'changePercent' or 'next_day_return'

        sequence_length = 20

        X_seq, X_ind, y = [], [], []

        # Convert boolean to int if needed
        df['golden_cross'] = df['golden_cross'].astype(int)
        df['death_cross'] = df['death_cross'].astype(int)

        for i in range(sequence_length, len(df)):
            seq_data = df[seq_features].iloc[i-sequence_length:i].values
            ind_data = df[indicator_features].iloc[i].values
            target = df[target_column].iloc[i]

            # Skip rows with NaN
            if np.isnan(seq_data).any() or np.isnan(ind_data).any() or pd.isna(target):
                continue

            X_seq.append(seq_data)
            X_ind.append(ind_data)
            y.append(target)

        # Convert to arrays
        X_seq = np.array(X_seq)       # Shape: (N, 20, 5)
        X_ind = np.array(X_ind)       # Shape: (N, 10)
        y = np.array(y) # Shape: (N,)
        
        scaler_seq = StandardScaler()
        scaler_ind = StandardScaler()
        scaler_y = StandardScaler()

        X_seq_flat = X_seq.reshape(-1, len(seq_features))  # Flatten time dimension
        X_seq_scaled = scaler_seq.fit_transform(X_seq_flat).reshape(X_seq.shape)

        X_ind_scaled = scaler_ind.fit_transform(X_ind)
        y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()
        
        return X_seq_scaled,X_ind_scaled,y_scaled,{
            "sequence":seq_features,
            "indicator":indicator_features
        },scaler_y

    def initiate_data_transformation(self, data):
        try:
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
            # If datetime is index
            data['dayofweek'] = data.index.dayofweek
            data['month'] = data.index.month
            data['day_sin'] = np.sin(2 * np.pi * data.index.dayofweek / 7)
            data['day_cos'] = np.cos(2 * np.pi * data.index.dayofweek / 7)
            data=data.reset_index()
            features = ['close', 'RSI', 'MACD', 'Signal', 'SMA_20', 'SMA_50', 'volume']
            technical_indicators = ['datetime','RSI', 'MACD', 'Signal', 'SMA_20', 'SMA_50']
            tech_data=data[technical_indicators]
            data=data[features]
            scaled_data = self.scaler.fit_transform(data)
            scaled_close=self.close_scaler.fit_transform(data[['close']])
            save_object("artifacts/scaler/scaler.pkl", self.scaler)
            save_object("artifacts/scaler/close_scalar.pkl",self.close_scaler)
            X, y = self.create_sequences(scaled_data)
            
            return X,y,tech_data,scaled_data,features
        except Exception as e:
            raise CustomException(e,sys)
    
    def get_heatmap_data(self, data):
        heatmap_data = []
        previous_close = None

        try:
            for idx, row in data[::-1].iterrows():
                close = float(row['close'])
                volume = float(row['volume'])
                date = idx.strftime('%Y-%m-%d')

                if previous_close is not None:
                    percent_change = ((close - previous_close) / previous_close) * 100
                else:
                    percent_change = 0.0  # No previous day to compare with

                heatmap_data.append({
                    'date': date,
                    'percent_change': round(percent_change, 2),
                    'close': close,
                    'volume': volume
                })

                previous_close = close  # Update for next iteration

            return heatmap_data

        except Exception as e:
            raise CustomException(e,sys)
