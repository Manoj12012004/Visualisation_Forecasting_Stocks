from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import train
from src.routers import backtest as backtest_router
from src.routers import evaluation as evaluation_router
from src.routers import market as market_router
from src.routers import forecast as forecast_router
from src.routers import data_models as data_models_router
from src.realtime_engine import realtime_ws
from src.database.connection import Base, engine
import asyncio
from contextlib import asynccontextmanager
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    yield
    # shutdown logic

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base.metadata.create_all(bind=engine)

@app.get("/stocks/list")
def list_stocks():
    return ["AAPL", "GOOGL", "TSLA", "MSFT", "AMZN"]

 # Removed duplicate /stocks endpoint for simplicity

# Routers
app.include_router(train.router)
app.include_router(backtest_router.router, prefix="/backtest")
app.include_router(evaluation_router.router, prefix="/evaluation")
app.include_router(market_router.router, prefix="/market")
app.include_router(forecast_router.router)
app.include_router(data_models_router.router, prefix="/data")
app.include_router(realtime_ws.router, prefix="/ws")

# Lightweight route introspection for debugging
@app.get("/__routes")
def __routes():
    routes = []
    try:
        for r in app.routes:
            methods = sorted(list(getattr(r, "methods", []) or []))
            path = getattr(r, "path", None)
            if path:
                routes.append({"path": path, "methods": methods})
    except Exception as e:
        return {"error": str(e)}
    return {"routes": routes}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
