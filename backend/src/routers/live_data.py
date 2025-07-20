from fastapi import APIRouter, HTTPException
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.services.datafetch import fetch_current_price
from src.exception import CustomException
import sys

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
    
@router.get('/stocks/{symbol}/technical')
def get_technical_indicators(symbol: str):
    try:
        symbol = symbol.upper()
        ingestor = DataIngestion(stock_symbol=symbol)
        df = ingestor.initiate_data_ingestion(interval='1day')
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the given symbol.")
        data_transformation = DataTransformation()
        _, _, technical_indicators, _ = data_transformation.initiate_data_transformation(df)
        return technical_indicators.to_dict(orient='records')
    except Exception as e:
        raise CustomException(e, sys)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/stocks/{symbol}/current")
async def get_current_price(symbol: str):
    symbol = symbol.upper()
    try:
        res=fetch_current_price(symbol)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stocks/{symbol}/historical/{interval}")
async def get_historical_data(symbol: str, interval: str):
    try:
        ingestor = DataIngestion(stock_symbol=symbol.upper())
        df = ingestor.initiate_data_ingestion(interval=interval)
        if df.empty:
            raise HTTPException(status_code=404, detail="No historical data found for the given symbol.")
        return df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))