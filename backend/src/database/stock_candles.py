from sqlalchemy import Column,Integer,String,Float,DateTime,Text,TEXT,BIGINT
from sqlalchemy.dialects.mysql import LONGTEXT
from .connection import Base
from datetime import datetime

class StockCandle(Base):
    __tablename__='candles'
    id=Column(Integer,primary_key=True,index=True)
    stock_symbol=Column(String(10),unique=True,nullable=True)
    timestamp=Column(DateTime,default=datetime.utcnow)
    open=Column(Float,nullable=False)
    high=Column(Float,nullable=False)
    low=Column(Float,nullable=False)
    close=Column(Float,nullable=False)
    volume=Column(BIGINT,nullable=False)
    