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


class DataIngestion:
    def __init__(self, stock_symbol="AAPL"):
        self.stock_symbol = stock_symbol.upper()
        self.api_key = "6a7c4a11380c48c0a644dd1cd06f2702"
        self.ws_url = f"wss://ws.twelvedata.com/v1/quotes/price?apikey={self.api_key}"
        self.data = []
        self.last_timestamp = None
        
        
    def save_to_csv(self):
        os.makedirs("artifacts", exist_ok=True)
        df = pd.DataFrame(self.data)
        df.to_csv("artifacts/live_stock_data.csv", index=False)
        print(f"✅ Saved {len(self.data)} rows to artifacts/live_stock_data.csv")
        
    async def connect_and_stream(self):
        logging.info("Starting WebSocket connection")

        try:
            async with websockets.connect(self.ws_url, open_timeout=10) as ws:
                # Subscribe
                await ws.send(json.dumps({
                    "action": "subscribe",
                    "params": {"symbols": self.stock_symbol}
                }))
                logging.info(f"Subscribed to {self.stock_symbol}")

                while True:
                    try:
                        message = await ws.recv()
                        d = json.loads(message)
                        if d.get("event") != "price":
                            continue
                        print(f"Received message: {d}")
                        
                        timestamp = int(d.get("timestamp"))

                        dt_str = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                        
                        entry = {
                            "timestamp": timestamp,
                            "datetime": dt_str,
                            "symbol": d.get("symbol"),
                            "price": float(d.get("price"))
                        }
                        print(f"Processed entry: {entry}")
                        
                        if timestamp != self.last_timestamp:
                            self.last_timestamp = timestamp
                            self.data.append(entry)
                            self.save_to_csv()

                    except Exception as e:
                        logging.error(f"Error receiving/parsing message: {e}")
                        break

        except Exception as e:
            raise CustomException(e, sys)

    async def initiate_live_ingestion(self):
        await self.connect_and_stream()

    def initiate_data_ingestion(self,interval):
        try:
            td=TDClient(apikey=self.api_key)
            df = td.time_series(symbol=self.stock_symbol, outputsize=5000, interval=interval).as_pandas()
            # os.makedirs("/ml/artifacts", exist_ok=True)
            # df.to_csv("/ml/artifacts/stock_data.csv")
            return df
        except Exception as e:
            raise CustomException(e, sys)
        
    
    def get_stock_info(self):
        try:
            td=TDClient(apikey=self.api_key)
            stock=td.quote(symbol=self.stock_symbol).as_json()
            return stock
        except Exception as e:
            raise CustomException(e, sys)
        
    def get_market_movers(self):
        try:
            td=TDClient(apikey=self.api_key)
            all_stocks=td.get_stocks_list().as_json()
            top_stocks=[item['symbol'] for item in all_stocks[:100]]
            results=[]
            for stock in top_stocks:
                df = td.time_series(symbol=stock, outputsize=1, interval='1d').as_pandas()
                if 'values' in df and len(df['values'])>0:
                    latest=data['values'][0]
                    volume=float(latest['volume'])
                    price=float(latest['close'])
                    results.append({
                        "symbol": stock,
                        "price": price,
                        "volume": volume
                    })
            for stock in top_stocks:
                ts=td.time_series(symbol=stock, outputsize=1, interval='1d').as_pandas()
                vals=ts.get('values',[])
                if len(vals)>0:
                    current=float(vals[0]['close'])
                    previous=float(vals[1]['close'])
                    pct_change=((current-previous)/previous)*100
                    results.append({
                        "symbol": stock,
                        "pct_change": pct_change,
                        'volume':float(vals[0]['volume']),
                        'price':current
                    })
            results_sorted=sorted(results,key=lambda x: x['pct_change'],reverse=True)
            top_gainers=results_sorted[:10]
            top_losers=results_sorted[-10:]
            most_active=sorted(results,key=lambda x: x['volume'],reverse=True)[:10]
            trending=sorted(results,key=lambda x: x['price'],reverse=True)[:10]
            return top_gainers, top_losers, most_active, trending
        except Exception as e:
            raise CustomException(e, sys)
# ✅ Utility
def get_latest_price(symbol: str):
    path = "artifacts/live_stock_data.csv"
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        df_symbol = df[df["symbol"] == symbol.upper()]
        if df_symbol.empty:
            return None
        latest = df_symbol.iloc[-1]
        return {
            "symbol": latest["symbol"],
            "price": float(latest["price"]),
            "timestamp": int(latest["timestamp"]),
            "time": latest["datetime"]
        }
    except Exception as e:
        return None
