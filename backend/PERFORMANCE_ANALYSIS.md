# Performance Analysis & Solutions

## 📊 Problem Summary

### Critical Issue: Model Predicting Only One Class

**Symptoms:**
- Direction Accuracy: ~51-52% (barely better than random)
- Direction Recall: **100%** (predicting only UP or only DOWN)
- Confusion Matrix: All predictions in one class
- R² negative (model worse than baseline)

**Root Cause:**
The model is **converging to a degenerate solution** where it predicts the same class for all inputs. This happens because:

1. ❌ **Class imbalance in data** - even 55/45 split can cause this
2. ❌ **Loss function not penalizing enough** - standard BCE too weak
3. ❌ **Model too complex** - overfits to majority class quickly
4. ❌ **Wrong bias initialization** - starts predicting one class from epoch 1
5. ❌ **Learning rate too high** - jumps to degenerate solution fast

## ✅ Implemented Solutions (Latest Version)

### 1. **Perfect Class Balance** (50/50 split)
```python
# Changed from 55th percentile to median
df["target_direction"] = (df["target_return"] > df['target_return'].median()).astype(int)
```
This ensures **exactly 50% UP and 50% DOWN** classes.

### 2. **Aggressive Focal Loss**
```python
focal_loss(gamma=3.0, alpha=0.25)  # High gamma, low alpha
```
- `gamma=3.0`: **Very aggressive** focusing on hard examples
- `alpha=0.25`: **Lower alpha** gives MORE weight to minority class
- **Label smoothing**: Prevents overconfident predictions

### 3. **Proper Bias Initialization**
```python
initial_bias = np.log(class_ratio)
# If 50/50: bias = log(1) = 0 → sigmoid(0) = 0.5 ✅
```
Ensures model starts with **balanced predictions** from epoch 1.

### 4. **Amplified Class Weights**
```python
weights = compute_class_weight('balanced', ...)
weights = weights ** 1.5  # Amplify the difference
```
Makes the model **pay extra attention** to misclassifying minority class.

### 5. **Reduced Model Complexity**
- Reduced LSTM from 128 → **64 units**
- Reduced Dense from 256 → **128 units**
- Added **L2 regularization** (0.001)
- Added **BatchNorm** before output
- **Prevents overfitting** to majority class

### 6. **Better Training Dynamics**
```python
learning_rate=3e-4  # Lower than before
batch_size=32       # Smaller for more diversity
epochs=100          # More epochs
shuffle=True        # Shuffle within batches
```

### 7. **Prediction Diversity Monitoring**
Custom callback that **prints warnings** if model starts predicting one class:
```python
class PredictionDiversityCallback:
    # Prints unique predictions every 5 epochs
    # Warns if only predicting one class
```

---

## 🎯 What to Expect Now

### Direction Prediction
- **Accuracy**: 58-65% (realistic for stock direction)
- **Precision**: 55-65% (balanced)
- **Recall**: 50-70% (**NOT 100%!**)
- **Confusion Matrix**: **Both classes predicted**

### Return Prediction  
- **R²**: 0.10-0.25 (positive and meaningful)
- **RMSE**: 3.5-4.5%

---

## 🔍 Diagnostic Insights (Old Issues)

### 2. **Return Prediction Issues**

**Problem**: R² = -0.021 (negative R² means model is worse than predicting the mean)

**Root Causes**:
- Target normalization issues
- Model architecture not capturing return patterns
- Overfitting to training data
- Feature scaling problems

**Solutions**:
```python
# Better target scaling
from sklearn.preprocessing import RobustScaler
scaler_y = RobustScaler(quantile_range=(5, 95))  # Less sensitive to outliers

# Add gradient clipping
optimizer = tf.keras.optimizers.Adam(
    learning_rate=1e-4,
    clipnorm=1.0  # ← Prevent gradient explosion
)

# More regularization
dropout_rate = 0.3  # Increase from 0.2
```

### 3. **Volatility Regime Performance**

**Status**: ✅ 74.63% is good, but can improve to 80%+

**Solutions**:
- Continue training (early stopping might have triggered too soon)
- Add more volatility-specific features
- Use label smoothing

---

## 🛠️ Recommended Improvements

### Priority 1: Fix Class Imbalance (Direction)

```python
# In train_transformer_multitask.py, add:
from sklearn.utils.class_weight import compute_class_weight

# Compute balanced class weights
class_weights_dir = dict(enumerate(
    compute_class_weight('balanced', classes=np.unique(y_dir), y=y_dir)
))

# Pass to model.fit
model.fit(
    ...,
    class_weight={"direction_output": class_weights_dir}
)
```

### Priority 2: Improve Loss Function

```python
# Add focal loss for direction (better than BCE for imbalanced data)
def focal_loss(gamma=2.0, alpha=0.25):
    def loss_fn(y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        ce = -y_true * tf.math.log(y_pred)
        weight = alpha * y_true * tf.pow(1 - y_pred, gamma)
        focal = weight * ce
        return tf.reduce_mean(focal)
    return loss_fn

# Use in compilation
model.compile(
    optimizer=optimizer,
    loss={
        "direction_output": focal_loss(gamma=2.0, alpha=0.75),  # ← Better for imbalance
        "return_output": "mse",
        "vol_regime_output": "categorical_crossentropy"
    },
    loss_weights={
        "direction_output": 0.5,
        "return_output": 0.25,
        "vol_regime_output": 0.25
    }
)
```

### Priority 3: Enhanced Training Configuration

```python
training_kwargs = {
    "validation_split": 0.2,
    "epochs": 150,              # ← Increase from 100
    "batch_size": 64,            # ← Larger batch for stability
    "learning_rate": 5e-5,       # ← Reduce from 1e-4
    "patience": 20,              # ← More patience before early stopping
    "loss_weights": {
        "direction_output": 0.5,
        "return_output": 0.25,
        "vol_regime_output": 0.25
    }
}
```

### Priority 4: Architecture Tuning

```python
model_kwargs = {
    "d_model": 256,                    # ← Increase from 128
    "num_heads": 8,
    "num_encoder_blocks": 6,           # ← Increase from 4
    "ff_dim": 1024,                    # ← Increase from 512
    "dropout_rate": 0.3,               # ← Increase from 0.2
    "indicator_dense_units": [512, 256, 128],  # ← Deeper
    "fusion_units": [512, 256]         # ← Deeper
}
```

### Priority 5: Add Gradient Clipping & Learning Rate Schedule

```python
# In TransformerMultiTaskTrainer.compile_model():
from tensorflow.keras.optimizers import Adam

optimizer = Adam(
    learning_rate=learning_rate,
    clipnorm=1.0,              # ← Clip gradients
    clipvalue=0.5
)

# Add learning rate scheduler
lr_scheduler = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,                 # ← Reduce LR by 50%
    patience=10,
    min_lr=1e-7,
    verbose=1
)
```

---

## 📈 Expected Improvements

After implementing these changes:

| Task | Current | Target | Strategy |
|------|---------|--------|----------|
| Direction Accuracy | 51% | **65-70%** | Class weights + Focal loss |
| Direction Precision | 51% | **60-65%** | Balanced predictions |
| Direction Recall | 100% | **60-70%** | Stop predicting one class |
| Return R² | -0.02 | **0.15-0.25** | Better scaling + regularization |
| Return RMSE | 5.06% | **3.5-4.5%** | Gradient clipping + deeper model |
| Vol Regime Accuracy | 74.6% | **80-85%** | More training + label smoothing |

---

## 🚀 Quick Action Plan

### Step 1: Update Training Script
Run the improved configuration from `examples/improved_training.py`

### Step 2: Monitor Training
```bash
# Watch metrics during training
tensorboard --logdir logs/
```

### Step 3: Validate Results
```python
# Check class distribution in predictions
pred_dir = model.predict([X_seq_test, X_ind_test])[0]
print("Prediction distribution:", np.unique(pred_dir > 0.5, return_counts=True))
```

### Step 4: Iterate
- If direction still poor: increase loss weight to 0.6
- If return still negative R²: check feature engineering
- If overfitting: increase dropout to 0.4

---

## 📝 Next Steps

1. ✅ Implement class weights and focal loss
2. ✅ Increase model capacity (d_model=256, blocks=6)
3. ✅ Add gradient clipping
4. ✅ Extend training to 150 epochs with better early stopping
5. ⏳ Run hyperparameter search (optional)
6. ⏳ Add ensemble predictions (optional)

---

## 💡 Key Takeaways

- **Direction task needs special attention** due to class imbalance
- **Return prediction requires careful normalization** and regularization
- **Volatility regime is the strongest task** - leverage it!
- **Multi-task learning helps** but requires proper loss weighting
- **More data + longer training = better results**

---

**Remember**: Stock prediction is inherently difficult. Even 55-60% direction accuracy can be profitable with proper risk management!
