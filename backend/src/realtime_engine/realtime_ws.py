# api/websocket.py (price-only stream)

from fastapi import APIRouter, WebSocket
import asyncio
import json
from datetime import datetime
import pandas as pd
import numpy as np
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
import os

router = APIRouter()


@router.websocket("/price/{symbol}")
async def ws_price(ws: WebSocket, symbol: str):
    await ws.accept()
    ingest = DataIngestion(symbol)
    tfm = DataTransformation()
    
    # Fetch initial history for indicators (daily)
    try:
        history_df = ingest.fin_data_ingestion(period="6mo", interval="1d")
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        history_df = pd.DataFrame()

    # Determine update interval from query string or env var, default 2s
    try:
        q_interval = ws.query_params.get("interval") if hasattr(ws, "query_params") else None
        interval = int(q_interval) if q_interval is not None else int(os.getenv("WS_PRICE_INTERVAL", "2"))
    except Exception:
        interval = 2
    interval = max(1, min(60, interval))
    
    while True:
        try:
            candle = ingest.get_latest_candle()
            last_time = candle.get('date')
            
            # Update history for indicators
            latest_tech = {}
            if not history_df.empty:
                try:
                    # Parse dates
                    candle_dt = pd.to_datetime(last_time)
                    last_hist_dt = pd.to_datetime(history_df.iloc[-1]['date'])
                    
                    # Update logic:
                    # If candle is same day as last history, update last row
                    # Else append new row
                    if candle_dt.date() == last_hist_dt.date():
                        idx = history_df.index[-1]
                        history_df.at[idx, 'close'] = candle['close']
                        history_df.at[idx, 'high'] = max(history_df.at[idx, 'high'], candle['high'])
                        history_df.at[idx, 'low'] = min(history_df.at[idx, 'low'], candle['low'])
                        # Note: Volume is tricky (daily vs 1m), skipping volume update for indicators
                    elif candle_dt.date() > last_hist_dt.date():
                        new_row = {
                            'date': candle_dt, # Keep it as timestamp
                            'open': candle['open'],
                            'high': candle['high'],
                            'low': candle['low'],
                            'close': candle['close'],
                            'volume': candle['volume']
                        }
                        history_df = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    # Recalculate indicators
                    tech_df = tfm.technical_view(history_df)
                    if not tech_df.empty:
                        # Get last row as dict
                        last_row = tech_df.iloc[-1].to_dict()
                        # Clean NaNs and non-serializable types
                        for k, v in last_row.items():
                            if pd.isna(v):
                                latest_tech[k] = None
                            elif isinstance(v, (np.integer, int)):
                                latest_tech[k] = int(v)
                            elif isinstance(v, (np.floating, float)):
                                latest_tech[k] = float(v)
                            else:
                                latest_tech[k] = str(v)
                except Exception as e:
                    print(f"Indicator calc error: {e}")

            if hasattr(last_time, 'isoformat'):
                last_time = last_time.isoformat()
                
            payload = {
                "symbol": symbol.upper(),
                "timestamp": datetime.utcnow().isoformat(),
                "last_candle": {
                    "time": last_time,
                    "open": candle.get('open'),
                    "high": candle.get('high'),
                    "low": candle.get('low'),
                    "close": candle.get('close'),
                    "volume": candle.get('volume')
                },
                "indicators": latest_tech
            }
            await ws.send_text(json.dumps(payload))
            await asyncio.sleep(interval)
        except Exception as e:
            await ws.send_text(json.dumps({"error": f"price_feed_error: {e}"}))
            await asyncio.sleep(max(5, interval))
