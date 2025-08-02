from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from flask import jsonify   
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
import time
import json
from src.exception import CustomException
import sys
from src.logger import logging
from datetime import timedelta
import pandas as pd
from typing import List
from src.services.live_stream import active_connections
import asyncio

active_connections: List[WebSocket] = []
router = APIRouter()

    
@router.get("/stocks/")
async def get_top_movers():
    try:
        ingestor= DataIngestion()
        gainers, losers,most_active,trending = ingestor.get_market_movers()
        return {
            "gainers": gainers,
            "losers": losers,
            "most_active":most_active,
            "trending": trending
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{symbol}")
def stock_info(symbol: str):
    try:
        symbol = symbol.upper()
        ingestor = DataIngestion(stock_symbol=symbol)
        stock_info=ingestor.get_stock_info()
        return stock_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.websocket('/ws/price_feed')
async def websocket_endpoint(websocket:WebSocket):
    await websocket.accept()
    try: 
        message=await websocket.receive_text()
        data=json.loads(message)
        symbol=data.get('symbol')
        
        if not symbol:
            await websocket.send_text('No symbol provided')
            return
        
        ingestor=DataIngestion(stock_symbol="AAPL")
        await ingestor.twelve_data_stream()
        
    except WebSocketDisconnect as e:
        raise CustomException(e,sys)
    except Exception as e:
        await websocket.send_text("Internal server error.")
        await websocket.close()

    
@router.get('/stocks/{symbol}/technical')
def get_technical_indicators(symbol: str, interval: str = Query(None, description="e.g. 1min, 5min, 1day"), start_date: str = Query(None, description="e.g. 2023-09-01"), end_date: str = Query(None, description="e.g. 2023-10-01")):
    try:
        symbol = symbol.upper()
        start_dt=pd.to_datetime(start_date) if start_date else None
        end_dt=pd.to_datetime(end_date) if end_date else None
        buffer_days=100
        extended_start=(start_dt - timedelta(days=buffer_days)).strftime('%Y-%m-%d') if start_dt else None
        ingestor = DataIngestion(stock_symbol=symbol)
        df = ingestor.initiate_data_ingestion(interval=interval,start=extended_start, end=end_dt)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the given symbol.")
        data_transformation = DataTransformation()
        _, _, technical_indicators,_, _ = data_transformation.initiate_data_transformation(df)
        return technical_indicators.to_dict(orient='records')
    except Exception as e:
        raise CustomException(e, sys)
    
    
@router.get("/stocks/{symbol}/current")
async def get_current_price(symbol: str):
    symbol = symbol.upper()
    try:
        ingestor=DataIngestion(stock_symbol=symbol.upper())
        res=ingestor.fetch_current_price(symbol)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stocks/{symbol}/historical/{interval}")
async def get_historical_data(symbol: str, interval: str):
    try:
        ingestor = DataIngestion(stock_symbol=symbol.upper())
        df = ingestor.initiate_data_ingestion(interval=interval,start="2023-09-01",end="2025-07-25")
        print(df)
        if df.empty:
            raise HTTPException(status_code=404, detail="No historical data found for the given symbol.")
        return df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/stream/start/{symbol}")
async def start_streaming(symbol: str, background_tasks: BackgroundTasks):
    try:
        ingestor = DataIngestion(stock_symbol=symbol)
        background_tasks.add_task(ingestor.initiate_live_ingestion)
        return {"message": f"Live streaming started for {symbol}"}
    except Exception as e:
        raise CustomException(e, sys)


@router.get("/stream/current/{symbol}")
async def get_current_stock(symbol: str):
    try:
        ingestor=DataIngestion(stock_symbol=symbol)
        data = ingestor.get_latest_price(symbol.upper())
        if not data:
            return {"error": "No data available"}
        return data
    except Exception as e:
        raise CustomException(e, sys)
@router.get('/stock/{symbol}/heatmap')
def stock_heatmap(symbol:str):
    ingestor=DataIngestion(stock_symbol=symbol)
    data=ingestor.initiate_data_ingestion(interval="1day")
    transformer=DataTransformation()
    heap=transformer.get_heatmap_data(data)
    print(heap)
    return heap
    
@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)  
    ingestor=DataIngestion()  
    await ingestor.twelve_data_stream()