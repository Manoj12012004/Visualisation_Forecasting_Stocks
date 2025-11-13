# 📚 Stock Forecasting & Machine Learning - Complete Learning Guide

## 🎯 Overview

This project is a **comprehensive learning platform** for stock price forecasting using advanced machine learning. It combines:
- **Two-Stage CNN-BiLSTM Models** for direction & return prediction
- **Multi-Horizon Forecasting** (1, 3, 5, 7, 10, 15, 30 days)
- **Interactive Learning Center** with ML concepts & technical indicators
- **Real-time Explanations** using SHAP values
- **Backtesting Framework** to validate strategies

## 🚀 Quick Start

### Backend Setup
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```powershell
cd frontend
npm install
npm start
```

Visit `http://localhost:3000` - the learning platform is ready!

## 🧠 Core Concepts

### Two-Stage Training Architecture

Our model uses a unique **two-stage approach**:

1. **Stage 1: Direction Classifier**
   - Predicts: Will price go UP or DOWN?
   - Model: CNN-BiLSTM with sigmoid output
   - Metrics: Accuracy, Precision, Recall
   - Why: Easier to predict direction than exact price

2. **Stage 2: Return Regressor**
   - Predicts: How much % will price change?
   - Model: Fine-tuned from Stage 1 (transfer learning)
   - Metrics: R², RMSE, MAE
   - Why: Reuses learned features for precise predictions

**Benefits:**
- ✅ Better generalization (less overfitting)
- ✅ Faster convergence
- ✅ More robust predictions
- ✅ Leverages transfer learning

## 📊 API Endpoints Reference

### Training

```http
GET /stocks/{symbol}/train
```

Trains a two-stage model on historical data.

**Response includes:**
- Direction metrics (accuracy, precision, recall)
- Regression metrics (R², RMSE)
- Model paths (direction, return, scaler)
- Learning insights with plain-English explanations

**Example:**
```bash
curl http://localhost:8000/stocks/AAPL/train
```

### Multi-Horizon Predictions

```http
GET /stocks/{symbol}/predict_multi_horizon?horizons=1,3,5,7,10,15,30
```

Forecasts stock for multiple time horizons simultaneously.

**Each horizon returns:**
- `predicted_return_pct`: Expected % change
- `predicted_price`: Target price
- `signal`: BUY/SELL/HOLD recommendation
- `confidence`: 0-100 strength indicator
- `direction_probability`: Bullish/bearish likelihood

**Reading the Results:**
- **Confidence >70**: Strong signal, high conviction
- **Direction Prob >0.65**: Bullish (expect upward move)
- **Direction Prob <0.35**: Bearish (expect downward move)
- **0.4-0.6**: Neutral zone (wait for confirmation)

**Example:**
```bash
curl "http://localhost:8000/stocks/AAPL/predict_multi_horizon?horizons=1,7,30"
```

### Model Explainability

```http
GET /learning/{symbol}/explain?top_k=5
```

Shows which features drive predictions using SHAP values.

**Returns:**
- Top influential features
- SHAP importance scores
- Plain-English explanations
- Feature formulas & interpretations

**Example:**
```bash
curl http://localhost:8000/learning/AAPL/explain?top_k=5
```

### Backtesting

```http
GET /learning/{symbol}/simulate?initial_balance=10000
```

Runs historical backtest of the strategy.

**Metrics returned:**
- `profit`: Total P&L in dollars
- `return_pct`: Percentage return
- `win_rate`: % of profitable trades
- `max_drawdown`: Largest peak-to-trough decline
- `buy_and_hold_return_pct`: Benchmark comparison

**Example:**
```bash
curl "http://localhost:8000/learning/AAPL/simulate?initial_balance=10000"
```

### Learning Center

#### Get Tutorial
```http
GET /learning/tutorial/getting_started
```

Step-by-step guide for beginners.

#### List Concepts
```http
GET /learning/concepts/list
```

Returns all available learning topics:
- Technical indicators
- ML concepts
- Trading strategies

#### Explain Concept
```http
GET /learning/concepts/{concept}
```

Available concepts:
- `two_stage_training`
- `direction_vs_return`
- `transfer_learning`
- `overfitting`
- `precision_vs_recall`
- `confusion_matrix`
- `r2_score`
- `risk_management`
- `backtesting`

**Example:**
```bash
curl http://localhost:8000/learning/concepts/two_stage_training
```

#### Learn Indicators
```http
GET /learning/{indicator}/educate
```

Available indicators: RSI, MACD, BB, ATR, ADX, EMA, Volume, OBV

**Example:**
```bash
curl http://localhost:8000/learning/RSI/educate
```

## 🎓 Technical Indicators Explained

### RSI (Relative Strength Index)
- **What**: Momentum oscillator (0-100)
- **Interpretation**: 
  - 0-30: Oversold (potential buy)
  - 70-100: Overbought (potential sell)
  - 30-70: Neutral
- **Formula**: `RSI = 100 - (100 / (1 + (Avg Gain / Avg Loss)))`
- **Use**: Identify mean-reversion opportunities

### MACD (Moving Average Convergence Divergence)
- **What**: Trend-following momentum indicator
- **Interpretation**:
  - MACD > Signal: Bullish
  - MACD < Signal: Bearish
- **Formula**: `MACD = EMA(12) - EMA(26), Signal = EMA(9) of MACD`
- **Use**: Confirm trend direction and strength

### Bollinger Bands (BB)
- **What**: Volatility bands around moving average
- **Interpretation**:
  - Price at lower band: Oversold
  - Price at upper band: Overbought
  - Band squeeze: Breakout coming
- **Formula**: `Middle = SMA(20), Upper/Lower = Middle ± (2 × StdDev)`
- **Use**: Identify overbought/oversold + volatility

### ATR (Average True Range)
- **What**: Volatility measure
- **Interpretation**:
  - High ATR: High volatility/risk
  - Low ATR: Consolidation
- **Use**: Set stop-loss distances (e.g., 2x ATR)

### ADX (Average Directional Index)
- **What**: Trend strength indicator
- **Interpretation**:
  - 0-25: Weak trend
  - 25-50: Strong trend
  - 50-75: Very strong trend
- **Use**: Confirm if trend is worth following

## 📈 Machine Learning Metrics

### Classification Metrics (Direction Model)

**Accuracy**: % of correct predictions
- Good: >60%
- Excellent: >70%

**Precision**: When model says "BUY", how often is it right?
- High precision = fewer false signals
- Trade-off: May miss opportunities

**Recall**: Of all actual UP moves, how many did we catch?
- High recall = catch more opportunities
- Trade-off: More false signals

**Confusion Matrix**:
```
                Predicted
              UP    DOWN
Actual  UP   [TP]   [FN]
       DOWN  [FP]   [TN]
```
- TP (True Positive): Correctly predicted UP ✅
- FP (False Positive): Predicted UP but went DOWN ❌
- TN (True Negative): Correctly predicted DOWN ✅
- FN (False Negative): Predicted DOWN but went UP ⚠️

### Regression Metrics (Return Model)

**R² Score**: How well model explains variance
- 1.0: Perfect fit
- 0.7-0.9: Good
- 0.5-0.7: Moderate
- <0.5: Poor

**RMSE** (Root Mean Squared Error): Average prediction error
- Lower is better
- Units: same as target (% return)

**MAE** (Mean Absolute Error): Average absolute error
- More robust to outliers than RMSE

## 💡 Best Practices

### Model Training
1. **Start with liquid stocks**: AAPL, MSFT, GOOGL, TSLA
2. **Monitor metrics**: Check R² >0.7 and accuracy >60%
3. **Retrain periodically**: Markets change, models need updates
4. **Validate on unseen data**: Don't trust training metrics alone

### Using Predictions
1. **Multi-horizon confirmation**: 
   - Short (1-5d) + Long (15-30d) agree? → Strong signal
   - Divergence? → Wait for clarity
2. **Check confidence**: 
   - >70: High conviction
   - 50-70: Moderate
   - <50: Weak signal, avoid
3. **Compare to fundamentals**: 
   - ML signals + fundamental analysis = better decisions

### Risk Management
1. **Position sizing**: Risk 1-2% per trade max
2. **Stop losses**: Use 2x ATR below entry
3. **Diversification**: Don't put all capital in one stock
4. **Track performance**: Compare backtest vs live results

### Avoiding Pitfalls
1. **Overfitting**: Train accuracy >> Test accuracy? Simplify model
2. **Look-ahead bias**: Never use future data in training
3. **Curve fitting**: Don't over-optimize to past data
4. **Ignoring costs**: Factor in fees & slippage

## 🔬 Advanced Topics

### Transfer Learning
- Stage 1 learns general market patterns
- Stage 2 reuses these features for specific predictions
- Result: Better performance with less data

### SHAP Values
- **What**: SHapley Additive exPlanations
- **Why**: Shows feature importance for each prediction
- **How**: Measures impact of each feature on output
- **Use**: Understand why model made a prediction

### Sequence Modeling
- **CNN layers**: Extract local patterns
- **BiLSTM layers**: Capture temporal dependencies
- **Attention**: Focus on relevant time steps
- **Indicators**: Add domain knowledge

## 📱 Frontend Features

### 1. Predictions & Analysis Tab
- Train models
- Multi-horizon forecasts (1-30 days)
- Model explainability (SHAP)
- Backtesting results
- Performance metrics

### 2. Learning Center Tab
- **ML Concepts**: Two-stage training, transfer learning, overfitting
- **Technical Indicators**: RSI, MACD, BB, ATR, ADX, EMA
- **Trading Concepts**: Risk management, backtesting

### 3. Tutorial Tab
- Step-by-step guide
- Best practices
- Risk warnings
- API examples

## 🎯 Example Workflow

### Complete Beginner Flow

1. **Start Tutorial Tab**: Read getting started guide
2. **Train a Model**: Select AAPL, click "Train Model"
3. **Get Predictions**: Click "Multi-Horizon Forecast"
4. **Understand Results**: 
   - Check 1d, 7d, 30d predictions
   - Compare signals across horizons
   - Note confidence levels
5. **Learn Why**: Click "Explain" to see feature importance
6. **Backtest**: Click "Backtest" to see historical performance
7. **Deep Dive**: Go to Learning Center
   - Read "Two-Stage Training"
   - Learn top indicator (e.g., RSI)
   - Understand "Precision vs Recall"

### Advanced User Flow

1. Train multiple stocks
2. Compare multi-horizon forecasts
3. Analyze SHAP explanations
4. Identify common patterns
5. Backtest strategies
6. Optimize parameters
7. Monitor live performance

## 🛠️ Customization

### Add New Indicators
Edit `backend/src/routers/learning.py`:
```python
INDICATOR_EXPLANATIONS = {
    "YOUR_INDICATOR": {
        "short": "Brief description",
        "long": "Detailed explanation",
        "example": "Usage example",
        "formula": "Mathematical formula",
        "interpretation": "How to read values"
    }
}
```

### Add New Concepts
Edit `get_concept_explanation` function:
```python
concepts_db = {
    "your_concept": {
        "title": "Concept Title",
        "summary": "One-line summary",
        "explanation": "Detailed explanation",
        "benefits": ["Benefit 1", "Benefit 2"]
    }
}
```

### Modify Forecast Horizons
Change default in API call:
```javascript
predictMultiHorizon(symbol, '1,2,3,5,10,20,60')
```

## 🔍 Troubleshooting

### Model Training Fails
- **Issue**: Insufficient data
- **Solution**: Use stocks with >2 years of history

### Poor Predictions
- **Issue**: Market regime change
- **Solution**: Retrain model on recent data

### Low Accuracy
- **Issue**: Overfitting or underfitting
- **Solution**: Check train vs validation metrics

### SHAP Errors
- **Issue**: Memory or computation limits
- **Solution**: Reduce background sample size

## 📊 Performance Benchmarks

**Typical Results** (well-trained model on liquid stocks):
- Direction Accuracy: 55-65%
- R² Score: 0.6-0.8
- Win Rate (backtest): 50-60%
- Sharpe Ratio: 0.5-1.5

**Note**: Past performance ≠ future results!

## ⚠️ Disclaimer

This is an **educational tool** for learning ML in finance. 

- **Not financial advice**: Always do your own research
- **No guarantees**: Markets are unpredictable
- **Risk warning**: Never invest more than you can afford to lose
- **Testing only**: Paper trade before using real money

## 🤝 Contributing

Want to improve the learning platform?
1. Add more indicators
2. Expand concept explanations
3. Create video tutorials
4. Improve model architecture
5. Add more visualization

## 📚 Further Reading

- [Deep Learning for Finance](https://www.manning.com/books/deep-learning-for-finance)
- [Technical Analysis Explained](https://www.amazon.com/Technical-Analysis-Explained-Fifth-Successful/dp/0071825177)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [Keras Documentation](https://keras.io/)
- [TA-Lib Documentation](https://mrjbq7.github.io/ta-lib/)

---

**Happy Learning! 🚀📈**

Built with ❤️ for educational purposes
