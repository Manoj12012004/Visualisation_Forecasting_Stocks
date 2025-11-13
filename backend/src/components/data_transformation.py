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

    def fin_data_transform(self, df):
        try:
            df=df.sort_index('date').reset_index(drop=True)
            df["target_return"] = ((df["close"].shift(-5) / df["close"]) - 1) * 100
            df["target_direction"] = (df["target_return"] > 0).astype(int)

            df['50ma'] = df['close'].rolling(50).mean()
            df['200ma'] = df['close'].rolling(200).mean()

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
            df["direction_persistence"] = (
                (df["close"] > df["close"].shift(1)).rolling(5).sum()
            )
            bb_window = 20
            df["BB_Middle"] = df["close"].rolling(bb_window).mean()
            df["BB_STD"] = df["close"].rolling(bb_window).std()
            df["BB_Upper"] = df["BB_Middle"] + (2 * df["BB_STD"])
            df["BB_Lower"] = df["BB_Middle"] - (2 * df["BB_STD"])

            df["volume_ma_20"] = df["volume"].rolling(20).mean()
            df["volume_spike"] = (df["volume"] > 1.5 * df["volume_ma_20"]).astype(int)

            df['golden_cross'] = ((df['50ma'] > df['200ma']) & (df['50ma'].shift(1) <= df['200ma'].shift(1))).astype(int)
            df['death_cross'] = ((df['50ma'] < df['200ma']) & (df['50ma'].shift(1) >= df['200ma'].shift(1))).astype(int)

            df["ADX"] = ta.trend.adx(df["high"], df["low"], df["close"])
            df["ATR"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"])
            df["momentum_10"] = df["close"].pct_change(10)
            df["volatility_10"] = df["close"].rolling(10).std()
            df["momentum_3"] = df["close"].pct_change(3)
            df["momentum_5"] = df["close"].pct_change(5)
            df["volatility_5"] = df["close"].rolling(5).std()
            df["daily_range"] = (df["high"] - df["low"]) / df["close"]
            df["gap"] = (df["open"] - df["close"].shift(1)) / df["close"].shift(1)
            df["prev_day_return"] = df["target_return"].shift(1)
            df["rolling_volatility_20"] = df["close"].rolling(20).std()
            df["price_position_in_bb"] = (df["close"] - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"])
            df["macd_signal_ratio"] = df["MACD"] / (df["Signal"] + 1e-6)
            df["rsi_slope"] = df["RSI"].diff()
            df["atr_pct"] = df["ATR"] / df["close"]
            df["adx_slope"] = df["ADX"].diff()
            df["trend_strength"] = (df["close"] - df["200ma"]) / df["200ma"]
            df["compression"] = (df["high"] - df["low"]) / df["close"]
            df['sma_ratio'] = df['50ma'] / df['200ma']

            
            df = df.dropna().reset_index(drop=True)
            df['BB_Width'] = df["BB_Upper"] - df["BB_Lower"]

            seq_features = ['open', 'high', 'low', 'close', 'volume', '50ma', '200ma']
            indicator_features = [
                'RSI',
                'MACD',
                'BB_Width',
                'ADX',
                'volatility_10',
                'momentum_10',
                'gap',
                'volume_ma_20',
                'trend_strength',
                'compression',
                'sma_ratio'
            ]


            sequence_length = 30

            X_seq, X_ind, y_return, y_dir = [], [], [], []

            for i in range(sequence_length, len(df)):
                seq_data = df[seq_features].iloc[i-sequence_length:i].values
                ind_data = df[indicator_features].iloc[i].values
                t_return = df['target_return'].iloc[i]
                t_dir = df['target_direction'].iloc[i]

                if np.isnan(seq_data).any() or np.isnan(ind_data).any() or pd.isna(t_return) or pd.isna(t_dir):
                    continue

                X_seq.append(seq_data)
                X_ind.append(ind_data)
                y_return.append(t_return)
                y_dir.append(t_dir)

            X_seq = np.array(X_seq)
            X_ind = np.array(X_ind)
            y_return = np.array(y_return)
            y_dir = np.array(y_dir)

            scaler_seq = StandardScaler()
            scaler_ind = StandardScaler()
            scaler_y_return = StandardScaler()

            X_seq_flat = X_seq.reshape(-1, len(seq_features))
            X_seq_scaled = scaler_seq.fit_transform(X_seq_flat).reshape(X_seq.shape)
            X_ind_scaled = scaler_ind.fit_transform(X_ind)
            y_return_scaled = scaler_y_return.fit_transform(y_return.reshape(-1, 1)).flatten()

            return (
                X_seq_scaled, X_ind_scaled, y_return_scaled, y_dir,
                {"sequence": seq_features, "indicator": indicator_features},
                scaler_y_return
            )
        except Exception as e:
            raise CustomException(e, sys)

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
