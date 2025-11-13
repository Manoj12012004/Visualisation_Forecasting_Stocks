# 🚀 Quick Start Guide

## Setup (5 minutes)

### 1. Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend runs on: `http://localhost:8000`

### 2. Frontend
```powershell
cd frontend
npm install
npm start
```

Frontend runs on: `http://localhost:3000`

## First Steps

### Option 1: Use the UI (Easiest)
1. Open `http://localhost:3000`
2. Select a stock (e.g., AAPL)
3. Click **"Train Model"** (takes 2-5 min)
4. Click **"Multi-Horizon Forecast"** to see predictions
5. Explore **Learning Center** tab for concepts
6. Check **Tutorial** tab for detailed guide

### Option 2: Use the API
```bash
# 1. Train a model
curl http://localhost:8000/stocks/AAPL/train

# 2. Get multi-horizon predictions
curl "http://localhost:8000/stocks/AAPL/predict_multi_horizon?horizons=1,7,30"

# 3. Explain predictions
curl http://localhost:8000/learning/AAPL/explain?top_k=5

# 4. Backtest strategy
curl "http://localhost:8000/learning/AAPL/simulate?initial_balance=10000"

# 5. Learn about indicators
curl http://localhost:8000/learning/RSI/educate
```

## What You Get

### 🎯 Multi-Horizon Predictions
Forecasts for **1, 3, 5, 7, 10, 15, 30 days** ahead with:
- Expected return %
- Target price
- BUY/SELL/HOLD signal
- Confidence score (0-100)
- Direction probability

### 🧠 Model Explainability
See **which features** drive predictions:
- SHAP importance values
- Plain-English explanations
- Technical indicator details

### 📊 Backtesting
Historical performance metrics:
- Total profit/loss
- Win rate
- Max drawdown
- vs Buy-and-Hold comparison

### 📚 Learning Center
Interactive education on:
- **ML Concepts**: Two-stage training, transfer learning, overfitting
- **Technical Indicators**: RSI, MACD, Bollinger Bands, ATR, ADX
- **Trading Strategies**: Risk management, position sizing

## Understanding Results

### Reading Predictions
```json
{
  "7d": {
    "signal": "BUY",
    "confidence": 75.3,
    "predicted_return_pct": 3.45,
    "predicted_price": 185.20,
    "direction_probability": 0.876
  }
}
```

- **signal**: BUY/SELL/HOLD recommendation
- **confidence**: 0-100, higher = stronger signal
  - >70: Strong
  - 50-70: Moderate
  - <50: Weak
- **predicted_return_pct**: Expected % change
- **direction_probability**: 
  - >0.65: Bullish (expect UP)
  - <0.35: Bearish (expect DOWN)
  - 0.4-0.6: Neutral

### Signal Types
- **STRONG BUY**: High confidence, positive return expected
- **BUY**: Moderate bullish signal
- **HOLD**: Neutral, wait for better setup
- **SELL**: Moderate bearish signal
- **STRONG SELL**: High confidence, negative return expected

## Tips for Best Results

### 1. Stock Selection
✅ **Good**: AAPL, MSFT, GOOGL, TSLA, AMZN (liquid, high-volume)
❌ **Avoid**: Penny stocks, low-volume stocks

### 2. Signal Confirmation
- Short-term (1-5d) + Long-term (15-30d) agree? → Stronger signal
- Divergence? → Wait for clarity

### 3. Risk Management
- Never risk >2% per trade
- Use stop losses (e.g., 2x ATR below entry)
- Diversify across multiple stocks
- Paper trade first!

### 4. Model Maintenance
- Retrain monthly (markets change)
- Monitor live vs backtest performance
- Check metrics: R² >0.7, Accuracy >60%

## Common Questions

**Q: How accurate is it?**
A: Typical direction accuracy: 55-65%. R² score: 0.6-0.8. Remember: **no model is perfect**, use as one input among many.

**Q: Can I trust the predictions?**
A: Use predictions as **guidance**, not guarantees. Always combine with fundamental analysis and risk management.

**Q: How long does training take?**
A: 2-5 minutes per stock on typical hardware.

**Q: What if predictions are poor?**
A: Try retraining with more recent data, or check if the stock has sufficient history (need >2 years).

**Q: Should I use this for real trading?**
A: **Start with paper trading**. This is an educational tool - learn first, trade later (carefully).

## Next Steps

1. ✅ Train models for 3-5 different stocks
2. ✅ Compare multi-horizon predictions
3. ✅ Study model explanations (SHAP)
4. ✅ Read Learning Center concepts
5. ✅ Backtest strategies
6. ✅ Paper trade for 1 month
7. ✅ Only then consider real money (small amounts)

## Support

- 📖 Full docs: `LEARNING_GUIDE.md`
- 🐛 Issues: Check terminal logs
- 💡 Ideas: Customize learning endpoints

## ⚠️ Risk Warning

This is an **educational tool**. Markets are risky. Never invest more than you can afford to lose. Always do your own research. Past performance ≠ future results.

---

**Happy Learning! 🎓📈**
