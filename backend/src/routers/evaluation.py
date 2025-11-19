from fastapi import APIRouter, HTTPException
from src.database.connection import SessionLocal
from src.database.models import Predictions
from src.realtime_engine.evaluator import evaluate_pending_predictions
import numpy as np

router = APIRouter()

@router.post("/evaluate")
def evaluate_predictions(symbol: str):
    db = SessionLocal()
    try:
        result = evaluate_pending_predictions(symbol, db)
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "evaluated_count": result["evaluated"],
            "prediction_ids": result["items"]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()

@router.get("/performance")
def performance(symbol: str):
    db = SessionLocal()
    try:
        rows = db.query(Predictions).filter(
            Predictions.stock_symbol == symbol.upper(),
            Predictions.realized_return.isnot(None)
        ).all()

        if not rows:
            return {"message": "No evaluated predictions yet"}

        total = len(rows)
        correct = sum(1 for r in rows if r.direction_correct == 1)
        avg_error = sum(abs(r.realized_return - r.predicted_return) for r in rows) / total

        win_rate = correct / total if total else 0

        return {
            "symbol": symbol.upper(),
            "total_predictions": total,
            "direction_accuracy": round(win_rate * 100, 2),
            "avg_return_error": avg_error,
        }

    finally:
        db.close()


@router.get("/metrics")
def detailed_metrics(symbol: str):
    """Compute classification and regression metrics for evaluated predictions of a symbol.

    Classification: accuracy, precision, recall, F1, confusion matrix (tp, fp, tn, fn)
    Regression: RMSE, R2, MAPE on returns (realized_return vs predicted_return)
    """
    db = SessionLocal()
    try:
        rows = db.query(Predictions).filter(
            Predictions.stock_symbol == symbol.upper(),
            Predictions.realized_return.isnot(None)
        ).all()

        if not rows:
            return {"message": "No evaluated predictions yet", "symbol": symbol.upper()}

        # Prepare arrays
        y_true_dir = []
        y_pred_dir = []
        y_true_ret = []
        y_pred_ret = []

        for r in rows:
            # actual direction: use stored if available, else derive from realized_return
            if r.actual_direction is not None:
                a_dir = int(r.actual_direction)
            else:
                a_dir = 1 if (r.realized_return or 0.0) > 0 else 0

            # predicted direction: infer from signal
            sig = (r.signal or "").strip().upper()
            p_dir = 1 if sig in ("UP", "BUY") else 0

            y_true_dir.append(a_dir)
            y_pred_dir.append(p_dir)

            if r.realized_return is not None and r.predicted_return is not None:
                y_true_ret.append(float(r.realized_return))
                y_pred_ret.append(float(r.predicted_return))

        # Convert to numpy
        y_true_dir = np.array(y_true_dir, dtype=int)
        y_pred_dir = np.array(y_pred_dir, dtype=int)
        y_true_ret = np.array(y_true_ret, dtype=float)
        y_pred_ret = np.array(y_pred_ret, dtype=float)

        # Classification metrics
        tp = int(np.sum((y_pred_dir == 1) & (y_true_dir == 1)))
        tn = int(np.sum((y_pred_dir == 0) & (y_true_dir == 0)))
        fp = int(np.sum((y_pred_dir == 1) & (y_true_dir == 0)))
        fn = int(np.sum((y_pred_dir == 0) & (y_true_dir == 1)))
        total = max(1, tp + tn + fp + fn)
        acc = (tp + tn) / total
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        # Regression metrics (on returns)
        if y_true_ret.size >= 2:
            rmse = float(np.sqrt(np.mean((y_true_ret - y_pred_ret) ** 2)))
            # R2: 1 - SS_res/SS_tot; handle degenerate variance
            ss_res = float(np.sum((y_true_ret - y_pred_ret) ** 2))
            ss_tot = float(np.sum((y_true_ret - np.mean(y_true_ret)) ** 2))
            r2 = float(1 - ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
            # MAPE with epsilon for zero targets
            eps = 1e-8
            mape = float(np.mean(np.abs((y_true_ret - y_pred_ret) / np.maximum(np.abs(y_true_ret), eps))) * 100.0)
        else:
            rmse = None
            r2 = None
            mape = None

        return {
            "symbol": symbol.upper(),
            "counts": {
                "evaluated": int(total),
            },
            "classification": {
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn}
            },
            "regression": {
                "rmse": rmse,
                "r2": r2,
                "mape": mape
            }
        }
    finally:
        db.close()
