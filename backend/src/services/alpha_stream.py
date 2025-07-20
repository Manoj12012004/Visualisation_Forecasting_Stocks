from fastapi import APIRouter, BackgroundTasks
from src.components.data_ingestion import DataIngestion, get_latest_price
from src.logger import logging
from src.exception import CustomException
import sys
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import random
import websockets
import json
import asyncio

router = APIRouter()


@router.get("/stream/start/{symbol}")
async def start_streaming(symbol: str, background_tasks: BackgroundTasks):
    try:
        ingestor = DataIngestion(stock_symbol=symbol)
        background_tasks.add_task(ingestor.initiate_live_ingestion)
        logging.info(f"Started streaming for {symbol}")
        return {"message": f"Live streaming started for {symbol}"}
    except Exception as e:
        raise CustomException(e, sys)


@router.get("/stream/current/{symbol}")
async def get_current_stock(symbol: str):
    try:
        data = get_latest_price(symbol)
        if not data:
            return {"error": "No data available"}
        return data
    except Exception as e:
        raise CustomException(e, sys)




class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions = {}  # websocket: list of symbols

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = []

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        self.subscriptions.pop(websocket, None)

    async def subscribe(self, websocket: WebSocket, symbol: str):
        if websocket in self.subscriptions:
            if symbol not in self.subscriptions[websocket]:
                self.subscriptions[websocket].append(symbol)

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()
router = APIRouter()


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "subscribe":
                symbol = data.get("symbol")
                await manager.subscribe(websocket, symbol)
                await manager.send_message({"msg": f"Subscribed to {symbol}"}, websocket)
            else:
                await manager.send_message({"error": "Invalid action"}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print("WebSocket Error:", e)
        manager.disconnect(websocket)


# Background broadcast task to send price updates
async def price_update_broadcaster():
    while True:
        await asyncio.sleep(2)
        # Aggregate all unique symbols for which there are subscribers
        symbols = set()
        for subs in manager.subscriptions.values():
            symbols.update(subs)
        # Send a price update for each tracked symbol
        for sym in symbols:
            price = round(random.uniform(100, 500), 2)  # Replace with real-time feed in production
            message = {"symbol": sym, "price": price}
            for conn, subs in manager.subscriptions.items():
                if sym in subs:
                    await conn.send_json(message)

TWELVE_WS_URL = f"wss://ws.twelvedata.com/v1/quotes/price?apikey=6a7c4a11380c48c0a644dd1cd06f2702"

@router.websocket("/ws/ticker")
async def twelvedata_websocket_listener():
    async with websockets.connect(TWELVE_WS_URL) as ws:
        print("Connected to Twelve Data WebSocket")

        # Subscribe to all currently tracked symbols
        while True:
            symbols = list(set(sym for subs in manager.subscriptions.values() for sym in subs))
            if symbols:
                subscribe_payload = {
                    "action": "subscribe",
                    "params": {
                        "symbols": ",".join(symbols)
                    }
                }
                await ws.send(json.dumps(subscribe_payload))
                break  # subscribe once and start receiving

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                print("Received from Twelve Data:", data)

                # Forward update to subscribed clients
                symbol = data.get("symbol")
                price = data.get("price")

                if symbol and price:
                    message = {"symbol": symbol, "price": price}
                    for conn, subs in manager.subscriptions.items():
                        if symbol in subs:
                            await conn.send_json(message)

            except Exception as e:
                print("TwelveData WebSocket Error:", e)
                await asyncio.sleep(5)  # retry