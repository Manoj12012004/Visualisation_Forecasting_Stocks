from fastapi import APIRouter, HTTPException
import numpy as np

from src.realtime_engine.predict import load_for_inference
from src.components.data_ingestion import DataIngestion

router = APIRouter()


def _prepare_data(symbol: str):
    artifacts = load_for_inference(symbol)
    df = DataIngestion(symbol).fin_data_ingestion()
    X_seq, X_ind, y_ret, y_dir, feat, vol_array = artifacts["transformer"].fin_data_transform(df)
    X_ind_scaled = artifacts["ind_scaler"].transform(X_ind)
    return artifacts, df, X_seq, X_ind_scaled, y_dir, feat


@router.get("/feature-importance")
def feature_importance(symbol: str, sample: int = 512, method: str = "permutation"):
    """
    Global feature importance over indicator features via permutation importance on classifier probability.
    - method kept for forward-compat; currently supports 'permutation'.
    """
    try:
        artifacts, df, X_seq, X_ind_scaled, y_dir, feat = _prepare_data(symbol)
        n = X_ind_scaled.shape[0]
        if n == 0:
            return {"message": "No samples available after transform"}

        # sample subset for speed
        idx = np.arange(n)
        np.random.shuffle(idx)
        idx = idx[: min(sample, n)]
        Xs = X_seq[idx]
        Xi = X_ind_scaled[idx].copy()

        # base probabilities
        base = artifacts["direction"].predict([Xs, Xi], verbose=0).reshape(-1)

        m = Xi.shape[1]
        scores = []
        for j in range(m):
            Xi_perm = Xi.copy()
            np.random.shuffle(Xi_perm[:, j])
            p_perm = artifacts["direction"].predict([Xs, Xi_perm], verbose=0).reshape(-1)
            # mean absolute change in probability
            imp = float(np.mean(np.abs(p_perm - base)))
            scores.append(imp)

        scores = np.array(scores, dtype=float)
        total = float(scores.sum())
        norm = (scores / total).tolist() if total > 0 else [0.0] * len(scores)
        names = feat.get("indicator", [f"f{i}" for i in range(len(scores))])

        items = [
            {"feature": names[i], "score": float(scores[i]), "importance": float(norm[i])}
            for i in range(len(scores))
        ]
        items.sort(key=lambda x: x["importance"], reverse=True)
        return {"symbol": symbol.upper(), "method": method, "items": items}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sequence-attribution")
def sequence_attribution(symbol: str, sample: int = 256):
    """
    Attention-like timestep attribution by occlusion: zero out each timestep in the sequence and
    measure average change in predicted probability.
    Returns importance per timestep (higher => more impact).
    """
    try:
        artifacts, df, X_seq, X_ind_scaled, y_dir, feat = _prepare_data(symbol)
        n = X_seq.shape[0]
        if n == 0:
            return {"message": "No samples available after transform"}

        idx = np.arange(n)
        np.random.shuffle(idx)
        idx = idx[: min(sample, n)]
        Xs = X_seq[idx].copy()
        Xi = X_ind_scaled[idx]

        base = artifacts["direction"].predict([Xs, Xi], verbose=0).reshape(-1)
        T = Xs.shape[1]
        impacts = np.zeros(T, dtype=float)

        for t in range(T):
            Xs_occ = Xs.copy()
            Xs_occ[:, t, :] = 0.0
            p_occ = artifacts["direction"].predict([Xs_occ, Xi], verbose=0).reshape(-1)
            impacts[t] = float(np.mean(np.abs(p_occ - base)))

        total = float(impacts.sum())
        norm = (impacts / total).tolist() if total > 0 else [0.0] * len(impacts)
        return {
            "symbol": symbol.upper(),
            "sequence_length": T,
            "raw": impacts.tolist(),
            "importance": norm,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sentiment endpoint intentionally removed per project requirements.
