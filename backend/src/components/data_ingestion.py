import os
import sys
import json
import pandas as pd
import asyncio
import websockets
import yfinance as yf
from datetime import datetime
from src.logger import logging
from src.exception import CustomException
from twelvedata import TDClient
import requests


class DataIngestion:
    def __init__(self, stock_symbol="AAPL"):
        self.stock_symbol = stock_symbol.upper()
        # Load API keys from environment to avoid hardcoding secrets
        self.api_key = os.getenv("TWELVEDATA_API_KEY", "6a7c4a11380c48c0a644dd1cd06f2702")
        self.fmp_api_key = os.getenv("FMP_API_KEY", "IGGm8FEoum4A8ffKfCTsHvrjW8XCR5rL")
        # Prefer official v3 historical-price-full endpoint; fallback kept for backward compatibility
        self.fin_api = f"https://financialmodelingprep.com/api/v3/historical-price-full/{self.stock_symbol}?apikey={self.fmp_api_key}"
        self.ws_url = f"wss://ws.twelvedata.com/v1/quotes/price?apikey={self.api_key}"
        self.data = []
        self.last_timestamp = None
        
        
    def save_to_csv(self,data):
        os.makedirs("artifacts", exist_ok=True)
        df = pd.DataFrame(data)
        
        df.to_csv("artifacts/live_stock_data.csv", index=False)
        
    def fin_data_ingestion(self, period="5y", interval="1d"):
        """Fetch historical OHLCV via yfinance only to avoid external rate limits.
        Returns a DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            # Use max available daily data; adjust period if needed
            raw = yf.download(self.stock_symbol, period=period, interval=interval, progress=False)
            if raw is None or raw.empty:
                raise ValueError(f"No data returned by yfinance for symbol: {self.stock_symbol}")
            
            # Handle MultiIndex columns if present (common in newer yfinance)
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)

            # Reset index to make Date a column
            raw = raw.reset_index()
            # Standardize column names
            rename_map = {
                'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
            }
            raw = raw.rename(columns=rename_map)
            # Keep only required columns (adj_close optional)
            cols = [c for c in ['date','open','high','low','close','volume'] if c in raw.columns]
            df = raw[cols].copy()
            # Ensure sorted by date ascending
            if 'date' in df.columns:
                df = df.sort_values('date').reset_index(drop=True)
            self.save_to_csv(df)
            return df
        except Exception as e:
            raise CustomException(e, sys)

    def get_latest_candle(self):
        """
        Returns the most recent 1-minute candle from Yahoo Finance.
        Output:
        {
            "date": "...",
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float
        }
        """

        # Fetch the last 1m candle (Yahoo may delay; tail(1) is fine for last price)
        data = yf.download(self.stock_symbol, period="1d", interval="1m", progress=False).tail(1)

        if data.empty:
            raise ValueError(f"No data returned by Yahoo Finance for symbol: {self.stock_symbol}")
        
        # Handle MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        last = data.iloc[-1]

        return {
            "date": last.name.strftime("%Y-%m-%d %H:%M:%S"),
            "open": float(last["Open"]),
            "high": float(last["High"]),
            "low": float(last["Low"]),
            "close": float(last["Close"]),
            "volume": float(last["Volume"])
        }
