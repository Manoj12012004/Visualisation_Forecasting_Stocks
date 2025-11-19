import joblib
import io
from sqlalchemy.orm import Session
from src.database.models import Models,Predictions
import datetime
from src.exception import CustomException
import sys
from keras.models import load_model


def save_model_to_db(session:Session,stock_symbol,accuracy,direction_model_path,return_model_path,ind_scaler_path,target_scaler_path,rmse):
    try:
        
        existing=session.query(Models).filter(Models.stock_symbol==stock_symbol).first()
        if existing:
            return False,existing
        
        stock_model=Models(
            stock_symbol=stock_symbol,
            direction_model_path=direction_model_path,
            return_model_path=return_model_path,
            ind_scaler_path=ind_scaler_path,
            target_scaler_path=target_scaler_path,
            accuracy=accuracy,
            rmse=rmse             
        )
        session.add(stock_model)
        session.commit()
        return True,stock_model
    except Exception as e:
        raise CustomException(e,sys)

def load_model_from_db(session: Session, stock_symbol: str):
    record = session.query(Models).filter(Models.stock_symbol==stock_symbol.upper()).first()
    if record: 
        return record
    return None

def save_predictions(session:Session,stock_symbol,prediction_time,predicted_return,predicted_direction,signal,confidence,explaination):
    try:
        prediction=Predictions(
            stock_symbol=stock_symbol,
            prediction_time=prediction_time,
            predicted_return=predicted_return,
            signal=signal,
            confidence=confidence,
        )
        session.add(prediction)
        session.commit()
        return prediction
    except Exception as e:
        raise CustomException(e,sys)
    
def load_predictions(session: Session, stock_symbol: str):
    records = session.query(Predictions).filter(Predictions.stock_symbol==stock_symbol.upper()).all()
    if records:
        return records
    return None
    
        