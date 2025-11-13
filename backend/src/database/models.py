from sqlalchemy import Column,LargeBinary,Integer,String,Float,DateTime,Text,TEXT,JSON,Enum
from sqlalchemy.dialects.mysql import LONGTEXT
from .connection import Base
from datetime import datetime

class Stocks(Base):
    __tablename__='stocks'
    id=Column(Integer,primary_key=True,index=True)
    symbol=Column(String(10),unique=True,nullable=False)
    company_name=Column(String(100),nullable=True)
    last_updated=Column(DateTime,default=datetime.utcnow)
    
class Models(Base):
    __tablename__='models'
    id=Column(Integer,primary_key=True,index=True)
    stock_symbol=Column(String(10),nullable=False)
    direction_model_path=Column(String(255),nullable=True)
    return_model_path=Column(String(255),nullable=True)
    scaler_path=Column(String(255),nullable=True)
    accuracy=Column(Float,nullable=True)
    precision=Column(Float,nullable=True)
    recall=Column(Float,nullable=True)
    rmse=Column(Float,nullable=True)
    r2_score=Column(Float,nullable=True)
    created_at=Column(DateTime,default=datetime.utcnow)
    
    
class Predictions(Base):
    __tablename__='predictions'
    id=Column(Integer,primary_key=True,index=True)
    stock_symbol=Column(String(10),nullable=False)
    prediction_time=Column(DateTime,default=datetime.utcnow)
    predicted_return=Column(Float,nullable=False)
    predicted_direction=Column(Integer,nullable=False)  # 1 for up, 0
    signal=Column(Enum('buy','sell','hold'),nullable=False)
    confidence=Column(Float,nullable=True)
    explaination=Column(JSON,nullable=True)
    
class Education(Base):
    __tablename__='education'
    id=Column(Integer,primary_key=True,index=True)
    indicator=Column(String(30),nullable=False)
    title=Column(String(100))
    description=Column(TEXT)
    
    