from sqlalchemy import Column,LargeBinary,Integer,String,Float,DateTime,Text,TEXT,JSON
from sqlalchemy.dialects.mysql import LONGTEXT
from .connection import Base
from datetime import datetime

class StockModel(Base):
    __tablename__='models'
    id=Column(Integer,primary_key=True,index=True)
    stock_symbol=Column(String(10),unique=True,nullable=True)
    last_trained=Column(DateTime,default=datetime.utcnow)
    accuracy=Column(Float)
    model_path=Column(String(255),nullable=True)
    model_actuals=Column(JSON,nullable=True)
    model_preds=Column(JSON,nullable=True)
    model_explain=Column(JSON,nullable=True)


    