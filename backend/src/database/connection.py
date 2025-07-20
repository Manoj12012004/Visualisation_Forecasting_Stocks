from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:root@localhost/stockdb"

engine= create_engine(
    SQLALCHEMY_DATABASE_URL,
)

SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base=declarative_base()