from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.database.connection import SessionLocal
from src.database.models import StockModel
from src.utils import load_obj
from src.routers.train import train_model
from src.pipeline.predict_pipeline import Predict
import threading
import sys
import numpy as np
from src.pipeline.train_pipeline import Train
from src.exception import CustomException

router = APIRouter()

class PredictRequest(BaseModel):
    forecast_days: int

@router.get("/stocks/{symbol}/predict")
def predict_stock(symbol:str):
    try:
        db = SessionLocal()
        stock = db.query(StockModel).filter(StockModel.stock_symbol == symbol).first()
        
        if not stock or not stock.model_path:
            return{
                'status':'Training Started',
                'message':f'Model for {symbol} is not trained.Please try again shortly.'
            }
        
        model_path=stock.model_path
        predictor=Predict()
        predictions=predictor.running_predict(model_path=model_path,stock=symbol,days_ahead=7)
        
        return {
            'symbol':symbol.upper(),
            'days_ahead':7,
            'predictions':predictions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting: {str(e)}")
    finally:
        db.close()

@router.get('/stocks/{symbol}/predict_cnn')
def predict_cnn(symbol:str):
    try:
        db=SessionLocal()
        stock=db.query(StockModel).filter(StockModel.stock_symbol==symbol.upper()).first()
        if not stock and stock.model_path:
            return {
                "status":"Training started successfully"
            }
        model_path=stock.model_path
        predictor=Predict()
        predictions=predictor.predict_cnn(model_path=model_path,stock_symbol=symbol,days_ahead=7)
        
        return {
            "symbol":symbol.upper(),
            "days_ahead":7,
            "predictions":predictions
        }
    except Exception as e:
        raise CustomException(e,sys)