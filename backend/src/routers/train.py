from fastapi import APIRouter, HTTPException
from src.pipeline.train_pipeline import Train
from src.database.connection import SessionLocal
from src.services.model_store import save_model_to_db,load_model_from_db
from keras.models import load_model
import tensorflow as tf
import plotly.graph_objects as go
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.components.model_cnn import TwoStageTrainer,train_two_stage_and_persist
import numpy as np
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
    """Train a two-stage CNN-BiLSTM model: direction classifier + return regressor.
    
    Educational notes:
    - Stage 1: Predicts if price will go up/down (binary classification)
    - Stage 2: Fine-tunes to predict actual return percentage (regression)
    - Uses transfer learning: Stage 2 reuses Stage 1's feature extractor
    """
    db = SessionLocal()
    try:
        existing_model=load_model_from_db(db,symbol.upper())
        if existing_model:
            db.close()
            model_dict=existing_model.__dict__.copy()
            model_dict.pop('_sa_instance_state',None)
            
            return {
                'status':"Model already exists", 
                'message': 'Use retrain endpoint to update the model',
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
            'stock_symbol': result['stock_symbol'],
            'direction_metrics': result['direction_metrics'],
            'regression_metrics': result['regression_metrics'],
            'model_paths': {
                'direction': str(result['direction_model_path']),
                'return': str(result['return_model_path']),
                'scaler': str(result['scaler_path'])
            },
            'learning_insights': {
                'accuracy': f"{result['direction_metrics']['accuracy']*100:.2f}% direction accuracy",
                'r2_score': f"R² = {result['regression_metrics']['r2']:.4f} (1.0 is perfect fit)",
                'precision': f"{result['direction_metrics']['precision']*100:.2f}% precision - when model says UP, it's right this often",
                'recall': f"{result['direction_metrics']['recall']*100:.2f}% recall - model catches this many actual UP moves"
            }
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
            "status":"Training completed","res":model,"train":model_saved
        }
    except Exception as e:
        raise CustomException(e,sys)
    finally:
        db.close()



@router.get("/stocks/{symbol}/train_cnn_two_stage")
def train_two_stage_endpoint(symbol: str):
    db = SessionLocal()
    try:
        # check existing
        existing_model = load_model_from_db(db, symbol.upper())
        if existing_model:
            return {'status': "Model trained already exists", 'model_data': jsonable_encoder(existing_model.__dict__)}

        ingestor = DataIngestion(symbol)
        raw_df = ingestor.fin_data_ingestion()

        transformer = DataTransformation()
        trainer = TwoStageTrainer()

        res = train_two_stage_and_persist(symbol.upper(), raw_df, transformer, model_store_path='artifacts/models', db_session=db)

        db.close()
        return {"status": "Training completed", "result": res}
    except Exception as e:
        raise CustomException(e, sys)
    finally:
        db.close()

