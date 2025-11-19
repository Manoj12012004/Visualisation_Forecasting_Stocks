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
        self.api_key = "6a7c4a11380c48c0a644dd1cd06f2702"
        self.fin_api=f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={self.stock_symbol}&apikey=6jOSYrWTaOpAwmkxYBIwAHQoSszIUx4G"
        self.ws_url = f"wss://ws.twelvedata.com/v1/quotes/price?apikey={self.api_key}"
        self.data = []
        self.last_timestamp = None
        
        
    def save_to_csv(self,data):
        os.makedirs("artifacts", exist_ok=True)
        df = pd.DataFrame(data)
        
        df.to_csv("artifacts/live_stock_data.csv", index=False)
        
    def fin_data_ingestion(self):
        response=requests.get(url=self.fin_api)
        data=pd.DataFrame(response.json())
        data=data.sort_values('date').reset_index(drop=True)
        print(data)
        self.save_to_csv(data)
        return data
    

    def get_latest_candle(symbol: str):
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

        ticker = yf.Ticker(symbol)

        # Fetch the last 5 minutes (safer than 1 minute — Yahoo sometimes delays)
        data = yf.download(symbol, period="1d", interval="1m").tail(1)

        if data.empty:
            raise ValueError(f"No data returned by Yahoo Finance for symbol: {symbol}")

        last = data.iloc[-1]

        return {
            "date": last.name.strftime("%Y-%m-%d %H:%M:%S"),
            "open": float(last["Open"]),
            "high": float(last["High"]),
            "low": float(last["Low"]),
            "close": float(last["Close"]),
            "volume": float(last["Volume"])
        }
