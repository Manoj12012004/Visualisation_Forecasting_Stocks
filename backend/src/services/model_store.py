import joblib
import io
from sqlalchemy.orm import Session
from src.database.models import StockModel
import datetime
from src.exception import CustomException
import sys
from tensorflow.keras.models import load_model


def save_model_to_db(session:Session,stock_symbol,accuracy,model_actuals,model_preds,model_explain,model_path=None):
    try:
        
        existing=session.query(StockModel).filter(StockModel.stock_symbol==stock_symbol).first()
        if existing:
            return False,existing
        
        stock_model=StockModel(
            stock_symbol=stock_symbol,
            accuracy=accuracy,
            model_path=model_path,
            model_preds=model_preds,
            model_actuals=model_actuals,
            model_explain=model_explain
        )
        session.add(stock_model)
        session.commit()
        return True,stock_model
    except Exception as e:
        raise CustomException(e,sys)

def load_model_from_db(session: Session, stock_symbol: str):
    record = session.query(StockModel).filter(StockModel.stock_symbol==stock_symbol.upper()).first()
    if record and record.model_path: 
        return record
    return None
    
        