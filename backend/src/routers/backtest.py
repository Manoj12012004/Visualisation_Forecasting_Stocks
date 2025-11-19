from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import numpy as np
import pandas as pd

from src.realtime_engine.predict import load_for_inference
from src.components.data_ingestion import DataIngestion
import yfinance as yf

router = APIRouter()


@router.get("/simple")
def simple_backtest(
    symbol: str,
    threshold: float = Query(0.6, ge=0.0, le=1.0),
    fee_bps: int = Query(1, ge=0, le=1000),
    slippage_bps: int = Query(1, ge=0, le=2000),
    initial: float = Query(10000.0, gt=0.0),
):
    """
    One-bar horizon long-only strategy:
    - Enter at t when P(direction=UP) > threshold AND predicted_return > costs
    - Exit at t+1; realized return = close[t+1]/close[t] - 1 - costs
    - Costs approximated as (fee_bps + slippage_bps)/1e4 per trade
    """
    artifacts = load_for_inference(symbol)
    df = DataIngestion(symbol).fin_data_ingestion()

    # Build features across history
    X_seq, X_ind, y_ret, y_dir, feat, vol_array = artifacts["transformer"].fin_data_transform(df)
    if X_seq is None or len(X_seq) < 2:
        return {"error": "Not enough data for backtest"}

    # Scale indicators
    X_ind_scaled = artifacts["ind_scaler"].transform(X_ind)

    # Batch predict
    prob = artifacts["direction"].predict([X_seq, X_ind_scaled], verbose=0).reshape(-1)
    ret_scaled = artifacts["return"].predict([X_seq, X_ind_scaled], verbose=0).reshape(-1)
    ret_norm = artifacts["target_scaler"].inverse_transform(ret_scaled.reshape(-1, 1)).reshape(-1)
    pred_ret = ret_norm * np.asarray(vol_array).reshape(-1)

    n = len(pred_ret)
    closes = df["close"].values
    # Align closes to last n+1 bars
    if len(closes) < n + 1:
        start = 0
    else:
        start = len(closes) - (n + 1)
    c_slice = closes[start: start + n + 1]
    if len(c_slice) < n + 1:
        return {"error": "Close series length misalignment"}

    # Realized next-bar returns
    real_ret = c_slice[1:] / c_slice[:-1] - 1.0

    cost = (fee_bps + slippage_bps) / 10000.0
    signals = (prob > threshold) & (pred_ret > cost)

    # Apply simple one-bar trades
    trade_ret = np.where(signals, real_ret - cost, 0.0)

    equity = [initial]
    for r in trade_ret:
        equity.append(equity[-1] * (1.0 + float(r)))
    equity = np.array(equity)

    final_balance = float(equity[-1])
    profit = final_balance - float(initial)
    return_pct = float(final_balance / float(initial) - 1.0)
    win_rate = float(np.mean(trade_ret[signals] > 0.0)) if np.any(signals) else 0.0

    # Max drawdown
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    drawdown_max = float(dd.min())

    # Buy & Hold
    buy_hold = float(closes[-1] / closes[0] - 1.0) if len(closes) >= 2 else 0.0

    # Time span for CAGR and Sharpe annualization
    try:
        dates = pd.to_datetime(df["date"]).reset_index(drop=True)
        start_dt = dates.iloc[start]
        end_dt = dates.iloc[start + n]
        days = max(1, (end_dt - start_dt).days)
        years = days / 365.25
    except Exception:
        years = max(1e-9, n / 252.0)  # fallback: assume daily bars

    # CAGR
    cagr = None
    if years and years > 0 and final_balance > 0 and initial > 0:
        try:
            cagr = float((final_balance / float(initial)) ** (1.0 / years) - 1.0)
        except Exception:
            cagr = None

    # Sharpe ratio (risk-free ~ 0), using per-period returns and annualizing
    periods_per_year = n / years if years and years > 0 else 252.0
    mu = float(np.mean(trade_ret)) if trade_ret.size > 0 else 0.0
    sigma = float(np.std(trade_ret, ddof=1)) if trade_ret.size > 1 else 0.0
    sharpe = float(np.sqrt(periods_per_year) * mu / sigma) if sigma > 0 else None

    # Profit factor (using only executed trades)
    tr = trade_ret[signals]
    gross_profit = float(np.sum(tr[tr > 0])) if tr.size > 0 else 0.0
    gross_loss = float(-np.sum(tr[tr < 0])) if tr.size > 0 else 0.0
    profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else None

    return {
        "symbol": symbol.upper(),
        "initial": initial,
        "final_balance": round(final_balance, 2),
        "profit": round(profit, 2),
        "return_pct": return_pct,
        "cagr": cagr,
        "sharpe_ratio": sharpe,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "drawdown_max": drawdown_max,
        "buy_and_hold_return_pct": buy_hold,
        "trades": int(np.sum(signals)),
    }


@router.get("/simulate_range")
def simulate_range(
    symbol: str,
    start: str = "2023-01-01",
    end: str = "2023-12-31",
    threshold: float = Query(0.6, ge=0.0, le=1.0),
    fee_bps: int = Query(1, ge=0, le=1000),
    slippage_bps: int = Query(1, ge=0, le=2000),
    initial: float = Query(10000.0, gt=0.0),
):
    """
    Simulate model over a date range and return equity curve plus S&P 500 benchmark.
    Dates should be ISO strings (YYYY-MM-DD). If out of data bounds, range is clipped.
    """
    artifacts = load_for_inference(symbol)
    df = DataIngestion(symbol).fin_data_ingestion()

    # predictions over full available data
    X_seq, X_ind, y_ret, y_dir, feat, vol_array = artifacts["transformer"].fin_data_transform(df)
    if X_seq is None or len(X_seq) < 2:
        return {"error": "Not enough data for backtest"}

    X_ind_scaled = artifacts["ind_scaler"].transform(X_ind)
    prob = artifacts["direction"].predict([X_seq, X_ind_scaled], verbose=0).reshape(-1)
    ret_scaled = artifacts["return"].predict([X_seq, X_ind_scaled], verbose=0).reshape(-1)
    ret_norm = artifacts["target_scaler"].inverse_transform(ret_scaled.reshape(-1, 1)).reshape(-1)
    pred_ret = ret_norm * np.asarray(vol_array).reshape(-1)

    n = len(pred_ret)
    closes = df["close"].values
    if len(closes) < n + 1:
        start_idx = 0
    else:
        start_idx = len(closes) - (n + 1)
    c_slice = closes[start_idx: start_idx + n + 1]
    if len(c_slice) < n + 1:
        return {"error": "Close series length misalignment"}

    dates = pd.to_datetime(df["date"]).reset_index(drop=True)
    d_slice = dates.iloc[start_idx: start_idx + n + 1]

    # Realized next-bar returns
    real_ret = c_slice[1:] / c_slice[:-1] - 1.0
    cost = (fee_bps + slippage_bps) / 10000.0
    signals = (prob > threshold) & (pred_ret > cost)
    trade_ret = np.where(signals, real_ret - cost, 0.0)

    # Range filtering
    try:
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
    except Exception:
        start_dt = d_slice.iloc[0]
        end_dt = d_slice.iloc[-1]

    # periods go from d_slice[j] -> d_slice[j+1]; choose j where d_slice[j] >= start_dt and d_slice[j+1] <= end_dt
    idx0 = int(np.searchsorted(d_slice.values, start_dt, side='left'))
    idx0 = max(0, min(idx0, n-1))
    # ensure we don't exceed
    idx1 = int(np.searchsorted(d_slice.values, end_dt, side='right')) - 1
    idx1 = max(idx0, min(idx1, n-1))

    tr = trade_ret[idx0: idx1 + 1]
    ds = d_slice.iloc[idx0: idx1 + 2]  # n_points = len(tr)+1

    # Build equity starting from initial at ds[0]
    equity = [initial]
    for r in tr:
        equity.append(equity[-1] * (1.0 + float(r)))

    equity_curve = [
        {"date": str(ds.iloc[i].date()) if hasattr(ds.iloc[i], 'date') else str(ds.iloc[i]), "value": float(equity[i])}
        for i in range(len(equity))
    ]

    # Benchmark S&P 500 using yfinance
    try:
        sp = yf.download("^GSPC", start=str(ds.iloc[0].date()), end=str(ds.iloc[-1].date()) )
        sp = sp[~sp.index.duplicated(keep='first')]
        if not sp.empty:
            sp0 = float(sp['Close'].iloc[0])
            bench = [
                {"date": idx.strftime('%Y-%m-%d'), "value": float(initial * (row['Close'] / sp0))}
                for idx, row in sp.iterrows()
            ]
        else:
            bench = []
    except Exception:
        bench = []

    result = {
        "symbol": symbol.upper(),
        "range": {"start": str(ds.iloc[0].date()), "end": str(ds.iloc[-1].date())},
        "initial": float(initial),
        "model_equity": equity_curve,
        "benchmark": {"symbol": "^GSPC", "equity": bench},
        "params": {"threshold": threshold, "fee_bps": fee_bps, "slippage_bps": slippage_bps},
    }
    return result
