import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import ta
import math

class DataTransformation:
    def __init__(self, sequence_length=30, horizon=3, min_rows=300):
        """
        sequence_length: number of past days per sample
        horizon: forward horizon in days for the target (3 in your original)
        min_rows: minimum rows required to avoid too-short datasets
        """
        self.sequence_length = sequence_length
        self.horizon = horizon
        self.min_rows = min_rows

        # scalers that you should fit on TRAIN only (see helper methods below)
        self.indicator_scaler = None
        self.target_scaler = None

        # final feature lists (set after transform)
        self.seq_features = [
            "ret_1", "ret_3", "atr_pct", "volatility_10",
            "vol_ratio", "RSI"
        ]
        self.indicator_features = [
            "MACD", "MACD_Hist", "bb_pos", "z_close_50"
        ]

    def _build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("date").reset_index(drop=True).copy()

        # Basic sanity
        if len(df) < self.min_rows:
            # Not an exception — sometimes you still want to work with small data,
            # but warn user (we won't raise to keep pipeline usable).
            print(f"Warning: dataset only has {len(df)} rows (<{self.min_rows}). Proceeding anyway.")

        # ---------- TARGETS ----------
        # log-return target over horizon (no percent, stationarity)
        df["target_return"] = df["close"].shift(-self.horizon) / df["close"] - 1.0
        thr = df["target_return"].rolling(200).std().fillna(method="bfill") * 0.5

        df["target_direction"] = (
            df["target_return"] > thr
        ).astype(int)
        
        # ---------- STATIONARY CORE ----------
        # short / multi-day returns
        df["ret_1"] = df["close"].pct_change(1)
        df["ret_3"] = df["close"].pct_change(self.horizon)

        # rolling volatility (std of close)
        df["volatility_10"] = df["close"].rolling(10).std()

        # ATR and ATR percentage
        df["ATR"] = ta.volatility.average_true_range(high=df["high"], low=df["low"], close=df["close"], window=14)
        df["atr_pct"] = df["ATR"] / df["close"]

        # Volume features: ratio to 20-day moving average
        df["vol_ma_20"] = df["volume"].rolling(20).mean()
        df["vol_ratio"] = df["volume"] / (df["vol_ma_20"] + 1e-9)
        df["vol20"] = df["close"].rolling(20).std()

        # z-score of price to capture deviation from medium-term mean
        df["z_close_50"] = (df["close"] - df["close"].rolling(50).mean()) / (df["close"].rolling(50).std() + 1e-9)

        # ---------- MOMENTUM INDICATORS ----------
        df["RSI"] = ta.momentum.rsi(close=df["close"], window=14)

        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema_12 - ema_26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["Signal"]

        # ---------- BOLLINGER: position only (standardized) ----------
        bb_mid = df["close"].rolling(20).mean()
        bb_std = df["close"].rolling(20).std()
        df["bb_pos"] = (df["close"] - bb_mid) / (bb_std + 1e-9)

        # Clean up columns that are intermediate-only
        # (we keep ATR because atr_pct is used; but drop raw ATR to reduce columns if desired)
        # We'll keep them – user can drop later.

        return df

    def _check_feature_availability(self, df: pd.DataFrame):
        needed = {"date", "open", "high", "low", "close", "volume"}
        missing = needed - set(df.columns)
        if missing:
            raise ValueError(f"Input dataframe missing required columns: {missing}")

    def fin_data_transform(self, df: pd.DataFrame):
        """
        Main entry. Returns:
          X_seq: np.array (n_samples, sequence_length, n_seq_features) -- scaled per sample
          X_ind: np.array (n_samples, n_indicator_features) -- NOT scaled here (fit on train)
          y_return: np.array (n_samples,) raw log-target (scale on train if desired)
          y_dir: np.array (n_samples,) 0/1
          feature_info: dict with feature lists
        """
        self._check_feature_availability(df)
        df = self._build_features(df)

        # drop NA rows produced by indicators
        df = df.dropna().reset_index(drop=True)

        if len(df) < (self.sequence_length + self.horizon):
            raise ValueError("Not enough rows after feature creation to build sequences. Reduce sequence_length or collect more data.")
        
        df = df.iloc[:-self.horizon].reset_index(drop=True)
        # Build sequences
        X_seq_list, X_ind_list, y_return_list, y_dir_list,vol_list = [], [], [], [],[]
        date_list, price_list = [], []
        seq_len = self.sequence_length

        # Prepare arrays for indexing speed
        seq_feats = self.seq_features
        ind_feats = self.indicator_features

        for i in range(seq_len, len(df) - 0):  # last row corresponds to sample where label exists (we used shift(-horizon) earlier)
            # current row is i
            seq_slice = df.iloc[i - seq_len:i]  # historical window (no future)
            ind_row = df.iloc[i]  # indicators at time i
            target_return = df["target_return"].iloc[i]
            target_dir = df["target_direction"].iloc[i]
            vol20=df['vol20'].iloc[i]
            cur_date = df["date"].iloc[i]
            cur_close = df["close"].iloc[i]

            # Basic sanity: a few NaNs can show up if windows are short; skip
            if seq_slice[seq_feats].isna().any().any() or ind_row[ind_feats].isna().any() or pd.isna(target_return) or pd.isna(vol20):
                continue

            # Convert seq to numpy (shape: seq_len x n_feats)
            seq_arr = seq_slice[seq_feats].values.astype(np.float32)
            ind_arr = ind_row[ind_feats].values.astype(np.float32)

            # Scale the sequence per-sample: fit a StandardScaler on the sequence itself (no leakage).
            # This removes global distributional shifts while keeping temporal internal structure.
            # NOTE: fitting per-sample is deliberate to avoid using any future info.
            scaler_seq = StandardScaler()
            seq_arr_scaled = scaler_seq.fit_transform(seq_arr)  # shape preserved

            norm_target=target_return/(vol20+1e-9)
            
            X_seq_list.append(seq_arr_scaled)
            X_ind_list.append(ind_arr)
            y_return_list.append(norm_target)
            y_dir_list.append(int(target_dir))
            vol_list.append(vol20)
            date_list.append(cur_date)
            price_list.append(cur_close)

        if len(X_seq_list) == 0:
            raise ValueError("No sequences could be built. Check data length / NaNs / sequence length.")

        y_return_arr = np.array(y_return_list, dtype=np.float32)
        # EWMA smoothing (span=5) to stabilize target for regression training
        y_return_series = pd.Series(y_return_arr).ewm(span=5).mean().values
        # clip extremes to reduce influence of outliers
        y_return_series = np.clip(y_return_series, -3.0, 3.0)

        X_seq = np.stack(X_seq_list, axis=0)
        X_ind = np.vstack(X_ind_list)
        y_return = y_return_series.astype(np.float32) 
        y_dir = np.array(y_dir_list, dtype=np.int8)
        vol_array = np.array(vol_list, dtype=np.float32) 
        dates_array = np.array(date_list)
        prices_array = np.array(price_list, dtype=np.float32)

        feature_info = {"sequence": seq_feats, "indicator": ind_feats}

        return X_seq, X_ind, y_return, y_dir, feature_info, vol_array, dates_array, prices_array

    # ------------------------ Utilities for training-time scaling ------------------------
    def fit_train_scalers(self, X_ind_train: np.ndarray, y_train: np.ndarray):
        """
        Fit scalers that MUST be fit only on TRAIN data.
        - indicator_scaler: fits on indicator matrix (2D)
        - target_scaler: fits on y_train if you want to scale regression targets
        Save to self.*
        """
        if X_ind_train is None or y_train is None:
            raise ValueError("Provide X_ind_train and y_train to fit train scalers.")

        self.indicator_scaler = StandardScaler()
        self.indicator_scaler.fit(X_ind_train)

        self.target_scaler = StandardScaler()
        self.target_scaler.fit(y_train.reshape(-1, 1))

        return self.indicator_scaler, self.target_scaler

    def apply_train_scalers(self, X_ind: np.ndarray, y: np.ndarray):
        """
        Apply fitted scalers to indicator and target arrays.
        Must call fit_train_scalers ON TRAIN before calling this on train/val/test.
        """
        if self.indicator_scaler is None or self.target_scaler is None:
            raise ValueError("Indicator/target scalers not fitted. Call fit_train_scalers() first (on training data).")

        X_ind_scaled = self.indicator_scaler.transform(X_ind)
        y_scaled = self.target_scaler.transform(y.reshape(-1, 1)).flatten()
        return X_ind_scaled, y_scaled

    # ------------------------ Helper: train/test split for sequences ------------------------
    @staticmethod
    def time_series_train_test_split(X_seq, X_ind, y_return, y_dir, train_frac=0.8):
        """
        Simple chronological split: first train_frac of samples -> train, rest -> test.
        Returns train/test tuples.
        """
        n = X_seq.shape[0]
        split = int(n * train_frac)
        return (
            X_seq[:split], X_ind[:split], y_return[:split], y_dir[:split],
            X_seq[split:], X_ind[split:], y_return[split:], y_dir[split:]
        )

    # ------------------------ Technical view for API ------------------------
    def technical_view(
        self,
        df: pd.DataFrame,
        sma_window: int = 20,
        ema_window: int = 20,
        bb_window: int = 20,
        rsi_window: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_k: float = 2.0,
    ) -> pd.DataFrame:
        """
        Build a UI-friendly technical indicators dataframe using this transformer.
        Returns a dataframe with columns:
         [date, open, high, low, close, volume,
          sma, ema, rsi, macd, macd_signal, macd_hist,
          bb_mid, bb_upper, bb_lower]
        """
        # --- Column normalization BEFORE availability check ---
        try:
            # Flatten MultiIndex if present (e.g. yfinance multi-ticker frames)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [ (c[0] if isinstance(c, tuple) and len(c)>0 else c) for c in df.columns ]
            # Lowercase all names for consistency
            df.columns = [ str(c).lower().strip() for c in df.columns ]
            # Common alternate names mapping
            rename_map = {
                'datetime': 'date',
                'timestamp': 'date',
                'adj close': 'close',
                'close*': 'close',  # sometimes providers append markers
            }
            for k,v in list(rename_map.items()):
                if k in df.columns and v not in df.columns:
                    df = df.rename(columns={k: v})
            # If date is index instead of column convert
            if 'date' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index().rename(columns={'index':'date'})
        except Exception:
            pass

        self._check_feature_availability(df)
        df = df.sort_values("date").reset_index(drop=True).copy()

        # Ensure numeric types to avoid ta errors on object dtypes
        for col in ["open","high","low","close","volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # SMA / EMA (defensive)
        try:
            df["sma"] = df["close"].rolling(int(max(1, sma_window))).mean()
        except Exception:
            df["sma"] = np.nan
        try:
            df["ema"] = df["close"].ewm(span=int(max(1, ema_window)), adjust=False).mean()
        except Exception:
            df["ema"] = np.nan

        # RSI with fallback manual computation if ta fails
        try:
            df["rsi"] = ta.momentum.rsi(close=df["close"], window=int(max(2, rsi_window)))
        except Exception:
            win = int(max(2, rsi_window))
            delta = df["close"].diff()
            gain = (delta.clip(lower=0)).rolling(win).mean()
            loss = (-delta.clip(upper=0)).rolling(win).mean()
            rs = gain / (loss + 1e-9)
            df["rsi"] = 100 - (100 / (1 + rs))

        # MACD family
        try:
            ema_f = df["close"].ewm(span=int(max(2, macd_fast)), adjust=False).mean()
            ema_s = df["close"].ewm(span=int(max(2, macd_slow)), adjust=False).mean()
            df["macd"] = ema_f - ema_s
            df["macd_signal"] = df["macd"].ewm(span=int(max(2, macd_signal)), adjust=False).mean()
            df["macd_hist"] = df["macd"] - df["macd_signal"]
        except Exception:
            df["macd"] = df["macd_signal"] = df["macd_hist"] = np.nan

        # Bollinger Bands
        try:
            bb_mid = df["close"].rolling(int(max(1, bb_window))).mean()
            bb_std = df["close"].rolling(int(max(1, bb_window))).std()
            df["bb_mid"] = bb_mid
            df["bb_upper"] = bb_mid + float(bb_k) * bb_std
            df["bb_lower"] = bb_mid - float(bb_k) * bb_std
        except Exception:
            df["bb_mid"] = df["bb_upper"] = df["bb_lower"] = np.nan

        # Drop rows where close is NaN to keep output clean
        df = df.dropna(subset=["close"]).reset_index(drop=True)

        # Keep only the fields needed for UI
        keep = [c for c in [
            "date", "open", "high", "low", "close", "volume",
            "sma", "ema", "rsi", "macd", "macd_signal", "macd_hist",
            "bb_mid", "bb_upper", "bb_lower"
        ] if c in df.columns]
        return df[keep]
