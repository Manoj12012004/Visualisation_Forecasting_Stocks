from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.database.connection import SessionLocal
from src.database.models import StockModel
from src.utils import load_obj
from src.pipeline.predict_pipeline import Predict
import numpy as np

router = APIRouter()

class PredictRequest(BaseModel):
    forecast_days: int

@router.get("/stocks/{symbol}/predict")
def predict_stock(symbol:str):
    try:
        db = SessionLocal()
        stock = db.query(StockModel).filter(StockModel.stock_symbol == symbol).first()
        
        if not stock or not stock.model_path:
            raise HTTPException(status_code=404, detail="Model not found for this stock.")

        
        predict= Predict()
        predict.running_predict(stock.model_path, stock.stock_symbol)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting: {str(e)}")
