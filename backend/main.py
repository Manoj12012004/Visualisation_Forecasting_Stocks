from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import retrain, train, predict,live_data
from src.services import live_stream
from src.database.connection import Base, engine
from src.services.retrain_service import auto_retrain
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base.metadata.create_all(bind=engine)

@app.get("/stocks")
def get_stocks():
    return [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
        {"symbol": "TSLA", "name": "Tesla Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corp"},
        {"symbol": "AMZN", "name": "Amazon.com Inc."}
    ]

# Routers
app.include_router(train.router)
app.include_router(predict.router)
app.include_router(retrain.router)
app.include_router(live_data.router)

@app.on_event("startup")
def startup():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)