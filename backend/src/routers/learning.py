# routes/learning_endpoints.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import numpy as np
import tensorflow as tf
import json
import shap
import pickle
import math
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation

from sklearn.metrics import (
    mean_squared_error,
    r2_score,
)
# import your existing helpers (adjust import paths as needed)
# from app.data import DataIngestion, DataTransformation
# from app.db import load_model_from_db, SessionLocal
# from app.utils import save_object, load_object, CustomException

router = APIRouter()

# ------------------------------
# Pydantic response models
# ------------------------------
class PredictResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float = Field(..., description="0-100 percent")
    prob_up: float = Field(..., description="Probability of up move (0-1)")
    predicted_return_pct: float = Field(..., description="Expected next-day return in percent")
    predicted_price: float
    last_close: float

class ExplainFeature(BaseModel):
    feature: str
    importance: float
    explanation: str

class ExplainResponse(BaseModel):
    symbol: str
    top_features: List[ExplainFeature]
    raw_shap: Optional[Dict[str, Any]] = None  # optional serialized shap arrays

class SimulationSummary(BaseModel):
    symbol: str
    initial_balance: float
    final_balance: float
    profit: float
    return_pct: float
    total_trades: int
    win_rate: float
    buy_and_hold_return_pct: float
    drawdown_max: float

class EducateResponse(BaseModel):
    indicator: str
    short: str
    long: str
    example: Optional[str] = None

# ------------------------------
# Plain-English explanations map
# ------------------------------
INDICATOR_EXPLANATIONS = {
    "RSI": {
        "short": "Momentum oscillator — overbought/oversold",
        "long": "RSI (Relative Strength Index) shows recent gains vs losses. Above 70 often signals overbought; below 30 oversold.",
        "example": "If RSI drops under 30 and then rises, it's often a mean-reversion buy signal.",
        "formula": "RSI = 100 - (100 / (1 + (Avg Gain / Avg Loss)))",
        "interpretation": "0-30: Oversold (potential buy), 70-100: Overbought (potential sell), 30-70: Neutral"
    },
    "MACD": {
        "short": "Momentum trend-following indicator",
        "long": "MACD is the difference between two EMAs (12 and 26). A cross of MACD above the signal line often indicates bullish momentum.",
        "example": "When MACD histogram turns positive after being negative, momentum is shifting upward.",
        "formula": "MACD = EMA(12) - EMA(26), Signal = EMA(9) of MACD",
        "interpretation": "MACD > Signal: Bullish, MACD < Signal: Bearish"
    },
    "BB": {
        "short": "Bollinger Bands — volatility bands",
        "long": "Bollinger Bands are a moving average ± 2 standard deviations. Price touching the lower band can signal oversold conditions; expansion signals rising volatility.",
        "example": "Price broke above the upper band after a squeeze → breakout.",
        "formula": "Middle Band = SMA(20), Upper/Lower = Middle ± (2 × StdDev)",
        "interpretation": "Price at lower band: Oversold, Price at upper band: Overbought, Band squeeze: Low volatility (breakout coming)"
    },
    "ATR": {
        "short": "Average True Range — volatility",
        "long": "ATR measures volatility as average range. Rising ATR means larger price swings; falling ATR means low volatility periods.",
        "example": "High ATR days require larger stop sizes.",
        "formula": "ATR = Moving Average of True Range over N periods",
        "interpretation": "High ATR: High volatility/risk, Low ATR: Low volatility/consolidation"
    },
    "ADX": {
        "short": "Trend strength index",
        "long": "ADX quantifies trend strength (not direction). Values above ~25 indicate a strong trend.",
        "example": "ADX rising while MACD is positive indicates a strengthening uptrend.",
        "formula": "ADX = SMA of DX (Directional Movement Index)",
        "interpretation": "0-25: Weak trend, 25-50: Strong trend, 50-75: Very strong trend, 75-100: Extremely strong trend"
    },
    "EMA": {
        "short": "Exponential Moving Average",
        "long": "EMA gives more weight to recent prices, making it more responsive than SMA.",
        "example": "Price crossing above EMA(50) = potential uptrend confirmation",
        "formula": "EMA = (Price × α) + (Previous EMA × (1 - α)), where α = 2/(N+1)",
        "interpretation": "Price > EMA: Bullish, Price < EMA: Bearish"
    },
    "Volume": {
        "short": "Trading volume",
        "long": "Number of shares traded. High volume confirms price moves; low volume suggests weak conviction.",
        "example": "Breakout with high volume = stronger signal",
        "formula": "Sum of shares traded in period",
        "interpretation": "Volume spike: Strong interest, Low volume: Weak move/reversal likely"
    },
    "OBV": {
        "short": "On-Balance Volume",
        "long": "Cumulative volume indicator: adds volume on up days, subtracts on down days.",
        "example": "OBV rising while price flat = accumulation (bullish)",
        "formula": "OBV = Previous OBV ± Current Volume (based on price direction)",
        "interpretation": "OBV divergence from price = potential reversal"
    }
}

# ------------------------------
# Helper utilities (adapt to your codebase)
# ------------------------------
def load_tf_model(path: str):
    """Load a TF model (handles both keras and saved_model)."""
    try:
        return tf.keras.models.load_model(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model {path}: {e}")

def load_pickle(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)

def generate_signal_from_outputs(prob_up: float, pred_return_pct: float) -> Dict[str, Any]:
    """Simple rule-based mapping to BUY/SELL/HOLD + confidence"""
    if prob_up >= 0.65 and pred_return_pct > 0:
        signal = "BUY"
    elif prob_up <= 0.35 and pred_return_pct < 0:
        signal = "SELL"
    else:
        signal = "HOLD"
    confidence = float(round(abs(prob_up - 0.5) * 200, 2))  # map to 0-100
    return {"signal": signal, "confidence": confidence}

def simple_backtest_from_signals(df, signals_col="signal", price_col="close", initial_balance=10000.0):
    """
    Very simple backtester:
    - Buy with full cash on BUY (market close price), sell all on SELL.
    - Hold otherwise.
    - Returns final balance, number of trades, win rate, drawdown, buy&hold return
    Note: This is an illustrative, beginner-friendly backtest only.
    """
    cash = initial_balance
    position = 0.0
    entry_price = 0.0
    wins = 0
    trades = 0
    equity_curve = []

    for i in range(len(df)-1):  # use next day's close for execution simplicity
        s = df[signals_col].iloc[i]
        price = float(df[price_col].iloc[i])
        next_price = float(df[price_col].iloc[i+1])
        # BUY
        if s == "BUY" and cash > 0:
            position = cash / price
            entry_price = price
            cash = 0.0
            trades += 1
        # SELL
        elif s == "SELL" and position > 0:
            cash = position * price
            # win if sold at higher than entry
            if price > entry_price:
                wins += 1
            position = 0.0
            trades += 1
        # else HOLD
        equity = cash + (position * next_price)
        equity_curve.append(equity)

    final_balance = cash + position * float(df[price_col].iloc[-1])
    profit = final_balance - initial_balance
    win_rate = (wins / trades) if trades > 0 else 0.0
    buy_and_hold_return = (float(df[price_col].iloc[-1]) / float(df[price_col].iloc[0]) - 1) * 100.0

    # compute max drawdown (simple)
    peak = -math.inf
    drawdown = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > drawdown:
            drawdown = dd

    return {
        "final_balance": round(final_balance, 2),
        "profit": round(profit, 2),
        "return_pct": round((profit / initial_balance) * 100, 2),
        "total_trades": trades,
        "win_rate": round(win_rate * 100, 2),
        "buy_and_hold_return_pct": round(buy_and_hold_return, 2),
        "drawdown_max": round(drawdown * 100, 2),
    }

# ------------------------------
# Endpoint: predict
# ------------------------------

    """
    Predict endpoint:
    - Loads direction & return model + scaler (paths must match how you saved them).
    - Runs the transformer to prepare X_seq, X_ind for the latest row.
    - Returns signal, confidence, prob_up (0-1), predicted_return_pct (raw), predicted_price, last_close.
    """
    try:
        sym = symbol.upper()

        # load saved model metadata from your DB or file registry
        # existing helper: load_model_from_db(session, sym)  OR load from path names you used
        # Example: direction model at artifacts/models/{sym}_direction.keras, return model at artifacts/models/{sym}_return.keras

        direction_model = load_tf_model(f"artifacts/models/{sym}_direction.keras")
        return_model = load_tf_model(f"artifacts/models/{sym}_return.keras")
        scaler_y = load_pickle(f"artifacts/models/{sym}_scaler_y.pkl")  # must exist

        # Build inputs via your existing ingestion/transformer
        ing = DataIngestion(sym)
        raw_df = ing.fin_data_ingestion()
        transformer = DataTransformation()
        X_seq, X_ind, y_return_scaled, y_dir, features, scaler_y_local = transformer.fin_data_transform(raw_df)

        if X_seq.shape[0] == 0:
            raise HTTPException(status_code=400, detail="Not enough data to form sequences")

        # get latest sample (last sequence)
        X_seq_latest = X_seq[-1:].astype(np.float32)
        X_ind_latest = X_ind[-1:].astype(np.float32).reshape(1, -1)

        prob_up = float(direction_model.predict([X_seq_latest, X_ind_latest], verbose=0).flatten()[0])
        pred_return_scaled = float(return_model.predict([X_seq_latest, X_ind_latest], verbose=0).flatten()[0])
        pred_return_pct = float(scaler_y.inverse_transform([[pred_return_scaled]])[0][0])  # inverse if required

        last_close = float(raw_df["close"].iloc[-1])
        predicted_price = round(last_close * (1 + pred_return_pct / 100.0), 4)

        signal_info = generate_signal_from_outputs(prob_up, pred_return_pct)

        return PredictResponse(
            symbol=sym,
            signal=signal_info["signal"],
            confidence=signal_info["confidence"],
            prob_up=round(prob_up, 4),
            predicted_return_pct=round(pred_return_pct, 4),
            predicted_price=predicted_price,
            last_close=last_close
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------
# Endpoint: explain
# ------------------------------
@router.get("/{symbol}/explain", response_model=ExplainResponse)
def explain(symbol: str, top_k: int = 5):
    """
    Returns SHAP-based top features and plain-English explanations.
    WARNING: SHAP calculation can be expensive. For production, precompute and cache explanations.
    """
    try:
        sym = symbol.upper()
        # load models and transformer similar to predict()
        direction_model = load_tf_model(f"artifacts/models/{sym}/{sym}_direction.keras")
        return_model = load_tf_model(f"artifacts/models/{sym}/{sym}_return.keras")
        scaler_y = load_pickle(f"artifacts/models/{sym}/{sym}_scaler_y.pkl")

        ing = DataIngestion(sym)
        raw_df = ing.fin_data_ingestion()
        transformer = DataTransformation()
        X_seq, X_ind, y_return_scaled, y_dir, features, scaler_y_local = transformer.fin_data_transform(raw_df)

        if X_seq.shape[0] < 20:
            raise HTTPException(status_code=400, detail="Not enough data for explainability")

        # create small background sample for shap (10-50 samples from training-like data)
        background_size = min(100, max(10, X_seq.shape[0] // 4))
        bg_idx = np.random.choice(X_seq.shape[0], size=background_size, replace=False)
        X_seq_bg = X_seq[bg_idx]
        X_ind_bg = X_ind[bg_idx]

        # Explanation for the return model (regression)
        explainer = shap.GradientExplainer(return_model, data=[X_seq_bg, X_ind_bg])
        # pick last 10 validation-like samples to explain
        explain_samples_seq = X_seq[-10:].astype(np.float32)
        explain_samples_ind = X_ind[-10:].astype(np.float32)
        shap_values = explainer.shap_values([explain_samples_seq, explain_samples_ind])

        # shap_values typically a list: [seq_shap, ind_shap] depending on model input structure
        # We'll aggregate absolute mean importance per indicator feature
        # shap_values[1] -> indicator shap (shape: samples x num_ind_features)
        ind_shap = np.abs(shap_values[1]).mean(axis=0)
        feat_names = features["indicator"]
        feature_importances = sorted(
            [{"feature": f, "importance": float(imp)} for f, imp in zip(feat_names, ind_shap)],
            key=lambda x: x["importance"], reverse=True
        )[:top_k]

        # Map to plain English explanations
        top_features_with_explanations = []
        for item in feature_importances:
            key = item["feature"]
            expl = INDICATOR_EXPLANATIONS.get(key.split("_")[0].upper(), None)
            explanation = expl["long"] if expl else "Feature used by model (no human-friendly text available)."
            top_features_with_explanations.append(
                ExplainFeature(feature=key, importance=round(item["importance"], 6), explanation=explanation)
            )

        # optional: return raw shap arrays serialized (careful—can be large)
        raw_shap_serialized = {
            "seq_shap_sample_mean": np.mean(np.abs(shap_values[0]), axis=(0, 1)).tolist() if len(shap_values) > 0 else None,
            "ind_shap_sample_mean": ind_shap.tolist()
        }

        return ExplainResponse(symbol=sym, top_features=top_features_with_explanations, raw_shap=raw_shap_serialized)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------
# Endpoint: simulate
# ------------------------------
@router.get("/{symbol}/simulate", response_model=SimulationSummary)
def simulate(symbol: str, initial_balance: float = 10000.0):
    """
    Runs a simple backtest using model signals on recent historical data.
    NOTE: This is a simple illustrative backtest; extend for slippage, fees, partial allocations.
    """
    try:
        sym = symbol.upper()
        direction_model = load_tf_model(f"artifacts/models/{sym}_direction.keras")
        return_model = load_tf_model(f"artifacts/models/{sym}_return.keras")
        scaler_y = load_pickle(f"artifacts/models/{sym}_scaler_y.pkl")

        ing = DataIngestion(sym)
        raw_df = ing.fin_data_ingestion()
        transformer = DataTransformation()
        X_seq, X_ind, y_return_scaled, y_dir, features, scaler_y_local = transformer.fin_data_transform(raw_df)

        if X_seq.shape[0] < 20:
            raise HTTPException(status_code=400, detail="Not enough data to simulate")

        preds_prob = direction_model.predict([X_seq, X_ind], verbose=0).flatten()
        preds_return_scaled = return_model.predict([X_seq, X_ind], verbose=0).flatten()
        preds_return_pct = scaler_y_local.inverse_transform(preds_return_scaled.reshape(-1, 1)).flatten()

        # assemble a DataFrame-compatible structure (we will attach signals to raw_df tail)
        df = raw_df.iloc[-len(preds_prob):].copy().reset_index(drop=True)
        df["prob_up"] = preds_prob
        df["pred_return_pct"] = preds_return_pct

        # map to signals
        df["signal"] = df.apply(lambda r: generate_signal_from_outputs(r["prob_up"], r["pred_return_pct"])["signal"], axis=1)

        bt = simple_backtest_from_signals(df, signals_col="signal", price_col="close", initial_balance=initial_balance)

        return SimulationSummary(
            symbol=sym,
            initial_balance=initial_balance,
            final_balance=bt["final_balance"],
            profit=bt["profit"],
            return_pct=bt["return_pct"],
            total_trades=bt["total_trades"],
            win_rate=bt["win_rate"],
            buy_and_hold_return_pct=bt["buy_and_hold_return_pct"],
            drawdown_max=bt["drawdown_max"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------
# Endpoint: educate
# ------------------------------
@router.get("/{indicator}/educate", response_model=EducateResponse)
def educate(indicator: str):
    """Get plain-English explanation of a technical indicator.
    
    Available indicators: RSI, MACD, BB, ATR, ADX, EMA, Volume, OBV
    """
    key = indicator.strip().upper()
    item = INDICATOR_EXPLANATIONS.get(key)
    if not item:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return EducateResponse(indicator=key, short=item["short"], long=item["long"], example=item.get("example"))

# ------------------------------
# Endpoint: learning concepts
# ------------------------------
@router.get("/concepts/list")
def list_learning_concepts():
    """Get all available learning concepts and indicators."""
    return {
        "technical_indicators": list(INDICATOR_EXPLANATIONS.keys()),
        "machine_learning_concepts": [
            "two_stage_training",
            "direction_vs_return",
            "transfer_learning",
            "overfitting",
            "precision_vs_recall",
            "confusion_matrix",
            "r2_score"
        ],
        "trading_concepts": [
            "risk_management",
            "position_sizing",
            "stop_loss",
            "take_profit",
            "diversification",
            "backtesting"
        ]
    }

@router.get("/concepts/{concept}")
def get_concept_explanation(concept: str):
    """Get detailed explanation of ML or trading concepts."""
    concepts_db = {
        "two_stage_training": {
            "title": "Two-Stage Training",
            "summary": "Train two related models sequentially, reusing learned features",
            "explanation": "Stage 1 learns general market patterns (direction), Stage 2 fine-tunes for specific predictions (return %). This improves generalization and reduces overfitting.",
            "benefits": ["Better generalization", "Faster convergence", "Reuses learned features"],
            "when_to_use": "When you have related tasks (classification + regression on same data)"
        },
        "direction_vs_return": {
            "title": "Direction vs Return Prediction",
            "summary": "Classify direction (up/down) vs predict actual return percentage",
            "explanation": "Direction = binary (will price go up or down?). Return = continuous (how much % change?). Direction is easier but less precise; return is harder but more actionable.",
            "benefits": ["Direction: More robust", "Return: More profitable if accurate"],
            "when_to_use": "Use both: direction for confidence, return for sizing"
        },
        "transfer_learning": {
            "title": "Transfer Learning",
            "summary": "Reuse pre-trained model knowledge for new tasks",
            "explanation": "Instead of training from scratch, freeze early layers (feature extractors) and only retrain final layers. Saves time and improves performance with less data.",
            "benefits": ["Faster training", "Better with limited data", "Reduces overfitting"],
            "when_to_use": "When tasks share common patterns (e.g., all stock prediction)"
        },
        "overfitting": {
            "title": "Overfitting",
            "summary": "Model memorizes training data but fails on new data",
            "explanation": "Signs: Training accuracy >> Test accuracy. Causes: Too complex model, too little data, no regularization. Solutions: Dropout, early stopping, more data.",
            "how_to_detect": "Compare train vs validation metrics - gap >10% suggests overfitting",
            "solutions": ["Add dropout layers", "Use early stopping", "Get more data", "Simplify model"]
        },
        "precision_vs_recall": {
            "title": "Precision vs Recall",
            "summary": "Quality vs completeness of predictions",
            "explanation": "Precision = Of all BUY signals, how many were correct? Recall = Of all actual UP moves, how many did we catch? High precision = fewer false signals. High recall = catch more opportunities.",
            "formulas": {
                "precision": "True Positives / (True Positives + False Positives)",
                "recall": "True Positives / (True Positives + False Negatives)"
            },
            "trading_context": "High precision: Conservative (less risk), High recall: Aggressive (more trades)"
        },
        "confusion_matrix": {
            "title": "Confusion Matrix",
            "summary": "Table showing correct and incorrect predictions",
            "explanation": "Rows = Actual, Columns = Predicted. Shows: True Positives (TP), False Positives (FP), True Negatives (TN), False Negatives (FN).",
            "interpretation": {
                "TP": "Correctly predicted UP (wins!)",
                "FP": "Predicted UP but went DOWN (loss)",
                "TN": "Correctly predicted DOWN",
                "FN": "Predicted DOWN but went UP (missed opportunity)"
            },
            "ideal": "High TP and TN, Low FP and FN"
        },
        "r2_score": {
            "title": "R² Score (Coefficient of Determination)",
            "summary": "How well model explains variance in data",
            "explanation": "R² = 1 means perfect predictions. R² = 0 means model is no better than average. Negative R² means model is worse than just predicting the mean.",
            "ranges": {
                "0.9-1.0": "Excellent (but check for overfitting!)",
                "0.7-0.9": "Good",
                "0.5-0.7": "Moderate",
                "below 0.5": "Poor - model has little predictive power"
            },
            "formula": "R² = 1 - (Sum of Squared Residuals / Total Sum of Squares)"
        },
        "risk_management": {
            "title": "Risk Management",
            "summary": "Protect capital through position sizing and stops",
            "explanation": "Never risk more than 1-2% of portfolio per trade. Use stop losses. Diversify across assets and strategies.",
            "rules": [
                "Risk 1-2% per trade maximum",
                "Use stop losses (e.g., 2x ATR below entry)",
                "Diversify: Don't put all capital in one stock",
                "Have an exit plan before entering"
            ],
            "example": "$10,000 portfolio → max $200 risk per trade"
        },
        "backtesting": {
            "title": "Backtesting",
            "summary": "Test strategy on historical data",
            "explanation": "Simulate trades using past data to estimate strategy performance. Essential but beware: past performance ≠ future results. Watch for look-ahead bias and overfitting.",
            "key_metrics": ["Win rate", "Profit factor", "Max drawdown", "Sharpe ratio"],
            "common_pitfalls": [
                "Look-ahead bias: using future info",
                "Curve fitting: over-optimizing to past",
                "Ignoring costs: fees and slippage",
                "Too short test period"
            ]
        }
    }
    
    concept_key = concept.lower()
    if concept_key not in concepts_db:
        return {
            "error": "Concept not found",
            "available": list(concepts_db.keys()),
            "tip": "Try /learning/concepts/list for all topics"
        }
    
    return concepts_db[concept_key]

@router.get("/tutorial/getting_started")
def getting_started_tutorial():
    """Complete beginner's guide to using this forecasting tool."""
    return {
        "title": "Stock Forecasting with Machine Learning - Getting Started",
        "steps": [
            {
                "step": 1,
                "title": "Train a Model",
                "endpoint": "GET /stocks/{symbol}/train",
                "description": "Train a two-stage model on historical data for your chosen stock",
                "example": "GET /stocks/AAPL/train",
                "what_happens": "Downloads data, engineers features, trains direction + return models",
                "time": "~2-5 minutes depending on data size"
            },
            {
                "step": 2,
                "title": "Get Multi-Horizon Predictions",
                "endpoint": "GET /stocks/{symbol}/predict_multi_horizon",
                "description": "See forecasts for 1, 3, 5, 7, 10, 15, 30 days ahead",
                "example": "GET /stocks/AAPL/predict_multi_horizon",
                "how_to_read": {
                    "signal": "BUY/SELL/HOLD recommendation",
                    "confidence": "0-100, higher = stronger",
                    "predicted_return_pct": "Expected % change",
                    "direction_probability": ">0.65 bullish, <0.35 bearish"
                }
            },
            {
                "step": 3,
                "title": "Understand Model Decisions",
                "endpoint": "GET /learning/{symbol}/explain",
                "description": "See which technical indicators drive predictions",
                "example": "GET /learning/AAPL/explain",
                "insight": "SHAP values show feature importance - which indicators matter most"
            },
            {
                "step": 4,
                "title": "Backtest Strategy",
                "endpoint": "GET /learning/{symbol}/simulate",
                "description": "See how strategy would have performed historically",
                "example": "GET /learning/AAPL/simulate",
                "metrics": {
                    "profit": "Total return in $",
                    "win_rate": "% of profitable trades",
                    "max_drawdown": "Largest peak-to-trough decline",
                    "vs_buy_hold": "Compare to just buying and holding"
                }
            },
            {
                "step": 5,
                "title": "Learn Indicators",
                "endpoint": "GET /learning/{indicator}/educate",
                "description": "Understand technical indicators used by the model",
                "example": "GET /learning/RSI/educate",
                "indicators": ["RSI", "MACD", "BB", "ATR", "ADX", "EMA", "Volume", "OBV"]
            }
        ],
        "best_practices": [
            "Start with liquid stocks (AAPL, MSFT, GOOGL, etc.)",
            "Compare multiple time horizons for confirmation",
            "Never trade based solely on model - use it as one input",
            "Backtest results are historical - real trading differs",
            "Monitor model performance and retrain periodically"
        ],
        "risk_warning": "This is an educational tool. Always do your own research and never invest more than you can afford to lose."
    }

