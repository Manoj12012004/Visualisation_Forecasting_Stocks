from fastapi import APIRouter, HTTPException
from src.pipeline.train_pipeline import Train
from src.database.connection import SessionLocal
from src.database.models import StockModel
import json
from pathlib import Path
from src.logger import logging
router = APIRouter()

@router.get("/stocks/{symbol}/train")
def train_model(symbol: str):
    db = SessionLocal()
    try:
        logging.info(f"Starting training for {symbol.upper()}")
        train_pipeline = Train()
        result = train_pipeline.run_training_pipeline(symbol.upper())

        stock_obj = db.query(StockModel).filter(StockModel.stock_symbol == symbol.upper()).first()
        if not stock_obj:
            stock_obj = StockModel(stock_symbol=symbol.upper())

        db.add(stock_obj)
        db.commit()

        return {
            "status": "Training completed successfully",
            "model_path": stock_obj.model_path,
            "accuracy": result.best_r2,
            "rmse":result.best_rmse
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
