# Green Engine: Machine Learning Models & Evaluation

## Model Recommendations

### 1. Short-term Growth Forecasting (24-72h)

#### Recommended Model: Prophet + SARIMA Ensemble
**Justification**: 
- Prophet handles seasonality and trend changes well
- SARIMA captures autoregressive patterns in time series
- Ensemble approach reduces overfitting and improves robustness

**Input Features**:
- Temperature (hourly averages, rolling statistics)
- Humidity (hourly averages, rolling statistics)
- Light (daily sum, hourly averages)
- Soil moisture (hourly averages)
- Time-based features (hour, day of week, seasonality)

**Hyperparameters**:
```python
# Prophet
prophet_params = {
    'changepoint_prior_scale': 0.05,  # Flexibility of trend
    'seasonality_prior_scale': 10.0,  # Seasonality strength
    'holidays_prior_scale': 10.0,     # Holiday effects
    'seasonality_mode': 'multiplicative'
}

# SARIMA
sarima_params = {
    'order': (1, 1, 1),           # (p, d, q)
    'seasonal_order': (1, 1, 1, 24),  # (P, D, Q, s)
    'trend': 'c'                   # Constant trend
}
```

**Expected Performance**: MAE < 2°C for temperature, < 5% for humidity

### 2. Long-term Yield Forecasting

#### Recommended Model: XGBoost with Feature Engineering
**Justification**:
- Handles non-linear relationships between environmental factors and yield
- Robust to outliers and missing data
- Provides feature importance for interpretability
- Good performance on tabular data with engineered features

**Input Features**:
- Environmental averages (temperature, humidity, light, soil moisture, EC, CO₂)
- Growth stage indicators
- Crop type and variety
- Days since planting
- Historical yield data for similar conditions
- Derived features (VPD, light-temperature ratio, stress indices)

**Hyperparameters**:
```python
xgb_params = {
    'n_estimators': 200,
    'max_depth': 6,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'random_state': 42
}
```

**Expected Performance**: R² > 0.75, MAE < 15% of mean yield

### 3. Anomaly Detection on Sensor Streams

#### Recommended Model: Isolation Forest + LSTM Autoencoder
**Justification**:
- Isolation Forest: Fast, handles high-dimensional data, no assumptions about data distribution
- LSTM Autoencoder: Captures temporal patterns and sequential anomalies
- Ensemble approach improves detection accuracy

**Input Features**:
- Raw sensor values
- Rolling statistics (mean, std, min, max)
- Rate of change (first and second derivatives)
- Z-scores and threshold violations
- Time-based features

**Hyperparameters**:
```python
# Isolation Forest
if_params = {
    'contamination': 0.1,      # Expected anomaly ratio
    'n_estimators': 100,
    'max_samples': 'auto',
    'random_state': 42
}

# LSTM Autoencoder
lstm_params = {
    'sequence_length': 24,      # 24-hour sequences
    'hidden_size': 64,
    'num_layers': 2,
    'dropout': 0.2,
    'learning_rate': 0.001
}
```

**Expected Performance**: Precision > 0.8, Recall > 0.7, F1-score > 0.75

## Evaluation Metrics & Validation Strategy

### 1. Time Series Cross-Validation
```python
from sklearn.model_selection import TimeSeriesSplit

# Expanding window validation
tscv = TimeSeriesSplit(n_splits=5, test_size=168)  # 1 week test sets

for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    # Train model and evaluate
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    
    # Calculate metrics
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
```

### 2. Backtesting Windows
- **Short-term models**: 30-day training, 7-day testing, rolling window
- **Long-term models**: 90-day training, 30-day testing, expanding window
- **Anomaly detection**: 7-day training, 1-day testing, sliding window

### 3. Evaluation Metrics

#### Forecasting Models
```python
def evaluate_forecast(y_true, y_pred):
    """Comprehensive forecast evaluation"""
    metrics = {}
    
    # Point forecast metrics
    metrics['mae'] = mean_absolute_error(y_true, y_pred)
    metrics['rmse'] = np.sqrt(mean_squared_error(y_true, y_pred))
    metrics['mape'] = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    metrics['r2'] = r2_score(y_true, y_pred)
    
    # Directional accuracy
    metrics['directional_accuracy'] = np.mean(
        np.sign(np.diff(y_true)) == np.sign(np.diff(y_pred))
    )
    
    # Bias
    metrics['bias'] = np.mean(y_pred - y_true)
    
    return metrics
```

#### Anomaly Detection Models
```python
def evaluate_anomaly_detection(y_true, y_pred):
    """Anomaly detection evaluation"""
    from sklearn.metrics import precision_score, recall_score, f1_score
    
    metrics = {}
    
    # Binary classification metrics
    metrics['precision'] = precision_score(y_true, y_pred, zero_division=0)
    metrics['recall'] = recall_score(y_true, y_pred, zero_division=0)
    metrics['f1_score'] = f1_score(y_true, y_pred, zero_division=0)
    
    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0
    metrics['sensitivity'] = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    return metrics
```

### 4. Model Performance Thresholds

#### Acceptable Performance Levels
- **Short-term forecasting**: MAE < 2°C, MAPE < 10%
- **Long-term yield prediction**: R² > 0.7, MAPE < 20%
- **Anomaly detection**: Precision > 0.8, Recall > 0.7

#### Model Retraining Triggers
- Performance degradation > 20% from baseline
- Data drift detection (statistical tests)
- New sensor deployment or configuration changes
- Seasonal changes requiring model adaptation

### 5. Feature Importance Analysis
```python
def analyze_feature_importance(model, feature_names):
    """Analyze and visualize feature importance"""
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importance = np.abs(model.coef_)
    else:
        return None
    
    # Create feature importance dataframe
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    return feature_importance
```

### 6. Model Interpretability
- **SHAP values** for feature contribution analysis
- **Partial dependence plots** for feature effects
- **LIME** for local interpretability
- **Model-agnostic explanations** for complex models

## Model Deployment Strategy

### 1. Model Versioning
```python
import mlflow

# Log model with MLflow
mlflow.log_params(model_params)
mlflow.log_metrics(evaluation_metrics)
mlflow.sklearn.log_model(model, "model")
```

### 2. A/B Testing Framework
- Deploy new model alongside existing model
- Route 10% of traffic to new model
- Monitor performance metrics
- Gradual rollout based on performance

### 3. Model Monitoring
```python
def monitor_model_drift(reference_data, current_data):
    """Monitor for data drift"""
    from scipy import stats
    
    drift_metrics = {}
    
    for column in reference_data.columns:
        if reference_data[column].dtype in ['float64', 'int64']:
            # Kolmogorov-Smirnov test
            ks_stat, p_value = stats.ks_2samp(
                reference_data[column], 
                current_data[column]
            )
            drift_metrics[column] = {
                'ks_statistic': ks_stat,
                'p_value': p_value,
                'drift_detected': p_value < 0.05
            }
    
    return drift_metrics
```

### 4. Performance Tracking
- **Real-time metrics**: Prediction latency, throughput
- **Accuracy metrics**: Rolling window performance
- **Business metrics**: Impact on yield optimization
- **Alert system**: Performance degradation notifications

## Research Integration

### Key Research Areas for Feature Engineering
1. **Plant Physiology**: Photosynthesis models, stress responses
2. **Environmental Science**: Microclimate effects, CO₂ fertilization
3. **Agricultural Engineering**: Irrigation optimization, climate control
4. **Data Science**: Time series analysis, ensemble methods

### Recommended Papers
1. "Environmental Control for Greenhouse Crop Production" - Acta Horticulturae
2. "Machine Learning in Precision Agriculture" - Computers and Electronics in Agriculture
3. "Time Series Forecasting in Agricultural Systems" - Agricultural Systems
4. "Anomaly Detection in IoT Sensor Networks" - IEEE Internet of Things Journal
