# src/services/evaluator.py

from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Predictions
from src.components.data_ingestion import DataIngestion

def evaluate_pending_predictions(symbol: str, db: Session):
    """
    Evaluates predictions whose next-candle data is now available.
    """
    ingestor = DataIngestion(symbol)
    df = ingestor.fin_data_ingestion()

    results = []
    rows = (
        db.query(Predictions)
        .filter(
            Predictions.stock_symbol == symbol.upper(),
            Predictions.realized_return.is_(None)   # only unevaluated ones
        )
        .order_by(Predictions.id.asc())
        .all()
    )

    if not rows:
        return {"evaluated": 0, "items": []}

    for pred in rows:
        pred_time = pred.prediction_time

        # find candle after prediction_time (next closed candle)
        mask = df["date"] > pred_time.isoformat()
        next_candle = df[mask].head(1)

        if next_candle.empty:
            # Not enough data yet — skip
            continue

        actual_close = float(next_candle.iloc[-1]["close"])
        real_return = (actual_close - pred.predicted_next_price) / pred.predicted_next_price

        actual_direction = 1 if actual_close > pred.predicted_next_price else 0
        correct = 1 if actual_direction == pred.predicted_direction else 0

        # update DB row
        pred.realized_price = actual_close
        pred.realized_return = real_return
        pred.actual_direction = actual_direction
        pred.direction_correct = correct
        db.add(pred)
        results.append(pred.id)

    db.commit()

    return {
        "evaluated": len(results),
        "items": results
    }
