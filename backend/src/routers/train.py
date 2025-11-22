from fastapi import APIRouter, HTTPException
from src.pipeline.train_pipeline import Train
from src.database.connection import SessionLocal
from src.services.model_store import save_model_to_db,load_model_from_db
from keras.models import load_model
import tensorflow as tf
import plotly.graph_objects as go
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.components.two_stage_trainer import SimpleTrainer,train_two_stage_and_persist
import numpy as np
import json
from src.exception import CustomException
from src.database.models import Models
from pathlib import Path
from src.logger import logging
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import sys
router = APIRouter()

@router.get("/list")
def list_stocks():
    db = SessionLocal()
    rows = db.query(Models.stock_symbol).all()
    db.close()
    return {"stocks": [r[0] for r in rows]}

@router.get("/stocks/{symbol}/train")
def train_model(symbol: str, force: bool = False):
    """Train a two-stage CNN-BiLSTM model: direction classifier + return regressor.
    
    Educational notes:
    - Stage 1: Predicts if price will go up/down (binary classification)
    - Stage 2: Fine-tunes to predict actual return percentage (regression)
    - Uses transfer learning: Stage 2 reuses Stage 1's feature extractor
    """
    db = SessionLocal()
    try:
        if not force:
            existing_model=load_model_from_db(db,symbol.upper())
            if existing_model:
                db.close()
                model_dict=existing_model.__dict__.copy()
                model_dict.pop('_sa_instance_state',None)
                
                return {
                    'status':"Model already exists", 
                    'message': 'Use force=true to retrain the model',
                    'model_data':jsonable_encoder(model_dict),
                    'learning_tip': 'Two-stage training improves generalization by first learning market direction, then refining return predictions'
                }
        
        # Use TwoStageTrainer
        ingestor = DataIngestion(symbol)
        raw_df = ingestor.fin_data_ingestion()
        transformer = DataTransformation()
        
        result = train_two_stage_and_persist(
            symbol.upper(), 
            raw_df, 
            transformer, 
            model_store_path='artifacts/models', 
            db_session=db
        )
        
        db.close()
        return {
            "status": "Training completed successfully",
            'stock_symbol': symbol,
            'direction_metrics': result['direction_metrics'],
            'regression_metrics': result['regression_metrics'],
            'validation_data': result.get('validation_data')
        }
    except Exception as e:
        db.rollback()
        raise CustomException(e,sys)
    finally:
        db.close()

