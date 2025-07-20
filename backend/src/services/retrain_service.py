from datetime import datetime
from src.database.connection import SessionLocal
from src.database.models import StockModel
from src.pipeline.train_pipeline import Train

def auto_retrain():
    train=Train()
    db=SessionLocal()
    stocks=db.query(StockModel).all()
    
    for stock in stocks:
        model_path,acc=train.run_training_pipeline(stock.stock_symbol)
        stock.last_trained=datetime.utcnow()
        stock.accuracy=acc
        stock.model_path=model_path
        db.commit()
        