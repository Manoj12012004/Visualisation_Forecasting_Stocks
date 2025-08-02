from fastapi import APIRouter, HTTPException
from src.pipeline.train_pipeline import Train
from src.database.connection import SessionLocal
from src.services.model_store import save_model_to_db,load_model_from_db
from tensorflow.keras.models import load_model
import json
from src.exception import CustomException
from pathlib import Path
from src.logger import logging
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import sys
router = APIRouter()

@router.get("/stocks/{symbol}/train")
def train_model(symbol: str):
    db = SessionLocal()
    try:
        existing_model=load_model_from_db(db,symbol.upper())
        if existing_model:
            db.close()
            model_dict=existing_model.__dict__.copy()
            model_dict.pop('_sa_instance_state',None)
            
            return {
                'status':"Model already exists", 
                'model_data':jsonable_encoder(model_dict)  
            }
        
        train_pipeline = Train()
        result = train_pipeline.run_training_pipeline(symbol.upper())
        
        model_saved,model=save_model_to_db(
            db,
            model_path=result['best_model_path'],
            accuracy=result['best_r2'],
            stock_symbol=result['stock_symbol'],
            model_preds=result['best_predictions'],
            model_actuals=result['model_actuals'],
            model_explain=result['model_explain'])      
        
        
        db.close()
        return {
            "status": "Training completed successfully",
            'model_data':JSONResponse(content=model)
        }
    except Exception as e:
        db.rollback()
        raise CustomException(e,sys)
    finally:
        db.close()

@router.get("/stocks/{symbol}/train_cnn")
def train_model(symbol):
    db=SessionLocal()
    try:
        existing_model=load_model_from_db(db,symbol.upper())
        if existing_model:
            model_dict=existing_model.__dict__.copy()
            model_dict.pop('_sa_istance_state',None)
            return {
                'status':"Model trained already exists",
                'model_data':jsonable_encoder(model_dict)
            }
        train=Train()
        res=train.train_cnn(symbol.upper())
        model_saved,model=save_model_to_db(
            session=db,
            stock_symbol=symbol.upper(),
            accuracy=res['best_r2'],
            model_actuals=res['model_actuals'],
            model_preds=res['best_predictions'],
            model_explain=res['model_explain'],
            model_path=res['best_model_path']
        )
        db.close()
        return{
            "status":"Training completed",
        }
    except Exception as e:
        raise CustomException(e,sys)
    finally:
        db.close()
        