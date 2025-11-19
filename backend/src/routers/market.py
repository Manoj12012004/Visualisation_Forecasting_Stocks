from fastapi import APIRouter
from src.components.data_ingestion import DataIngestion

router = APIRouter()


@router.get("/heatmap")
def heatmap(symbols: str = "AAPL,GOOGL,TSLA,MSFT,AMZN"):
    """
    Returns simple daily percent change for a list of symbols.
    Query: symbols=SYM1,SYM2,...
    """
    items = []
    for sym in [s.strip().upper() for s in symbols.split(",") if s.strip()]:
        try:
            df = DataIngestion(sym).fin_data_ingestion()
            if len(df) < 2:
                items.append({"symbol": sym, "change_pct": None})
                continue
            last = float(df.iloc[-1]["close"])
            prev = float(df.iloc[-2]["close"])
            change = (last - prev) / prev if prev else 0.0
            items.append({"symbol": sym, "change_pct": change})
        except Exception:
            items.append({"symbol": sym, "change_pct": None})
    return {"items": items}
