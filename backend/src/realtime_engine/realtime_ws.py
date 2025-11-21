# api/websocket.py (price-only stream)

from fastapi import APIRouter, WebSocket
import asyncio
import json
from datetime import datetime
from src.components.data_ingestion import DataIngestion
import os

router = APIRouter()


@router.websocket("/price/{symbol}")
async def ws_price(ws: WebSocket, symbol: str):
    await ws.accept()
    ingest = DataIngestion(symbol)
    # Determine update interval from query string or env var, default 2s
    try:
        q_interval = ws.query_params.get("interval") if hasattr(ws, "query_params") else None
        interval = int(q_interval) if q_interval is not None else int(os.getenv("WS_PRICE_INTERVAL", "2"))
    except Exception:
        interval = 2
    interval = max(1, min(60, interval))
    while True:
        try:
            df = ingest.fin_data_ingestion()
            # send last N candles or last tick
            # Normalize date to string for JSON safety
            last_time = df.iloc[-1]['date']
            if hasattr(last_time, "isoformat"):
                last_time = last_time.isoformat()
            payload = {
                "symbol": symbol.upper(),
                "timestamp": datetime.utcnow().isoformat(),
                "last_candle": {
                    "time": last_time,
                    "open": float(df.iloc[-1]['open']),
                    "high": float(df.iloc[-1]['high']),
                    "low": float(df.iloc[-1]['low']),
                    "close": float(df.iloc[-1]['close']),
                    "volume": float(df.iloc[-1]['volume'])
                }
            }
            await ws.send_text(json.dumps(payload))
            await asyncio.sleep(interval)   # throttled by interval seconds
        except Exception as e:
            await ws.send_text(json.dumps({"error": str(e)}))
            await asyncio.sleep(max(5, interval))
