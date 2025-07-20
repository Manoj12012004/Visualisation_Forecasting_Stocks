from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import retrain, train, predict,live_data
from src.services import alpha_stream
from src.database.connection import Base, engine
from src.services.retrain_service import auto_retrain
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

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
app.include_router(alpha_stream.router)
app.include_router(live_data.router)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(alpha_stream.twelvedata_websocket_listener())


# Background auto-retrain every 24 hours
scheduler = BackgroundScheduler()
scheduler.add_job(auto_retrain, 'interval', hours=24)
scheduler.start()
