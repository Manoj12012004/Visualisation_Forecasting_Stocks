# api/websocket.py (price-only stream)

from fastapi import APIRouter, WebSocket
import asyncio
import json
from datetime import datetime
from src.components.data_ingestion import DataIngestion

router = APIRouter()


@router.websocket("/price/{symbol}")
async def ws_price(ws: WebSocket, symbol: str):
    await ws.accept()
    ingest = DataIngestion(symbol)
    while True:
        try:
            df = ingest.fin_data_ingestion()
            # send last N candles or last tick
            payload = {
                "symbol": symbol.upper(),
                "timestamp": datetime.utcnow().isoformat(),
                "last_candle": {
                    "time": df.iloc[-1]['date'],
                    "open": float(df.iloc[-1]['open']),
                    "high": float(df.iloc[-1]['high']),
                    "low": float(df.iloc[-1]['low']),
                    "close": float(df.iloc[-1]['close']),
                    "volume": float(df.iloc[-1]['volume'])
                }
            }
            await ws.send_text(json.dumps(payload))
            await asyncio.sleep(1)   # tune frequency (1s or your candle timeframe)
        except Exception as e:
            await ws.send_text(json.dumps({"error": str(e)}))
            await asyncio.sleep(5)
