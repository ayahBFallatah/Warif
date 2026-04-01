"""
Forecasting Models for Green Engine
Implements short-term and long-term forecasting for microgreen growth
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import joblib
import logging
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrowthForecastingModels:
    """Machine learning models for microgreen growth forecasting"""
    
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
        self.engine = create_engine(db_connection_string)
        self.models = {}
        self.scalers = {}
        self.feature_columns = [
            'temp_avg_1h', 'temp_min_1h', 'temp_max_1h', 'temp_std_1h',
            'humidity_avg_1h', 'humidity_min_1h', 'humidity_max_1h', 'humidity_std_1h',
            'light_sum_1h', 'light_avg_1h', 'light_max_1h',
            'soil_moisture_avg_1h', 'soil_moisture_min_1h', 'soil_moisture_max_1h',
            'ec_avg_1h', 'ec_min_1h', 'ec_max_1h',
            'co2_avg_1h', 'co2_min_1h', 'co2_max_1h', 'co2_std_1h',
            'temp_avg_24h', 'temp_variance_24h',
            'humidity_avg_24h', 'humidity_variance_24h',
            'light_sum_24h', 'light_variance_24h',
            'soil_moisture_avg_24h', 'soil_moisture_variance_24h',
            'ec_avg_24h', 'ec_variance_24h',
            'co2_avg_24h', 'co2_variance_24h',
            'temp_humidity_ratio', 'light_temp_ratio', 'vpd',
            'light_hours_above_threshold', 'hour', 'day_of_week', 'is_daytime'
        ]
    
    def load_training_data(self, location: str, days_back: int = 30) -> pd.DataFrame:
        """Load processed features for model training"""
        query = f"""
        SELECT * FROM processed_features 
        WHERE location = '{location}'
        AND timestamp >= NOW() - INTERVAL '{days_back} days'
        ORDER BY timestamp
        """
        
        try:
            df = pd.read_sql_query(query, self.engine)
            logger.info(f"Loaded {len(df)} training samples for {location}")
            return df
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return pd.DataFrame()
    
    def prepare_features(self, df: pd.DataFrame, target_column: str = 'temp_avg_1h') -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for model training"""
        if df.empty:
            return pd.DataFrame(), pd.Series()
        
        # Select feature columns that exist in the dataframe
        available_features = [col for col in self.feature_columns if col in df.columns]
        
        # Create lag features for time series
        for lag in [1, 2, 3, 6, 12, 24]:
            if target_column in df.columns:
                df[f'{target_column}_lag_{lag}'] = df[target_column].shift(lag)
                available_features.append(f'{target_column}_lag_{lag}')
        
        # Remove rows with NaN values
        df_clean = df.dropna(subset=available_features + [target_column])
        
        X = df_clean[available_features]
        y = df_clean[target_column]
        
        return X, y
    
    def train_short_term_forecast_model(self, location: str, target_column: str = 'temp_avg_1h') -> Dict:
        """Train short-term forecasting model (24-72 hours)"""
        logger.info(f"Training short-term forecast model for {target_column} at {location}")
        
        # Load training data
        df = self.load_training_data(location, days_back=30)
        
        if df.empty:
            logger.error("No training data available")
            return {}
        
        # Prepare features
        X, y = self.prepare_features(df, target_column)
        
        if X.empty or y.empty:
            logger.error("No valid features/target data")
            return {}
        
        # Split data for time series validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Initialize models
        models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'xgboost': xgb.XGBRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression()
        }
        
        best_model = None
        best_score = float('inf')
        best_model_name = None
        
        # Train and evaluate models
        for name, model in models.items():
            logger.info(f"Training {name} model...")
            
            scores = []
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_val_scaled = scaler.transform(X_val)
                
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Predict and evaluate
                y_pred = model.predict(X_val_scaled)
                mae = mean_absolute_error(y_val, y_pred)
                scores.append(mae)
            
            avg_score = np.mean(scores)
            logger.info(f"{name} average MAE: {avg_score:.4f}")
            
            if avg_score < best_score:
                best_score = avg_score
                best_model = model
                best_model_name = name
        
        # Train final model on full dataset
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        best_model.fit(X_scaled, y)
        
        # Save model and scaler
        model_key = f"{location}_{target_column}_short_term"
        self.models[model_key] = best_model
        self.scalers[model_key] = scaler
        
        # Save to disk
        joblib.dump(best_model, f"data/models/{model_key}_model.pkl")
        joblib.dump(scaler, f"data/models/{model_key}_scaler.pkl")
        
        logger.info(f"Best model ({best_model_name}) saved for {model_key}")
        
        return {
            'model_name': best_model_name,
            'mae': best_score,
            'model_key': model_key
        }
    
    def train_long_term_yield_model(self, location: str) -> Dict:
        """Train long-term yield prediction model"""
        logger.info(f"Training long-term yield model for {location}")
        
        # Load growth measurements
        query = f"""
        SELECT gm.*, pf.*
        FROM growth_measurements gm
        LEFT JOIN processed_features pf ON gm.location = pf.location 
        AND gm.timestamp BETWEEN pf.timestamp - INTERVAL '7 days' AND pf.timestamp
        WHERE gm.location = '{location}'
        ORDER BY gm.timestamp
        """
        
        try:
            df = pd.read_sql_query(query, self.engine)
            logger.info(f"Loaded {len(df)} yield measurements for {location}")
        except Exception as e:
            logger.error(f"Error loading yield data: {e}")
            return {}
        
        if df.empty:
            logger.error("No yield data available")
            return {}
        
        # Aggregate features for yield prediction
        yield_features = df.groupby('tray_id').agg({
            'temp_avg_1h': ['mean', 'std', 'min', 'max'],
            'humidity_avg_1h': ['mean', 'std', 'min', 'max'],
            'light_sum_1h': ['sum', 'mean'],
            'soil_moisture_avg_1h': ['mean', 'std'],
            'ec_avg_1h': ['mean', 'std'],
            'co2_avg_1h': ['mean', 'std'],
            'vpd': ['mean', 'std'],
            'days_since_planting': 'max',
            'yield_g': 'max'
        }).reset_index()
        
        # Flatten column names
        yield_features.columns = [
            'tray_id',
            'temp_mean', 'temp_std', 'temp_min', 'temp_max',
            'humidity_mean', 'humidity_std', 'humidity_min', 'humidity_max',
            'light_sum', 'light_mean',
            'soil_moisture_mean', 'soil_moisture_std',
            'ec_mean', 'ec_std',
            'co2_mean', 'co2_std',
            'vpd_mean', 'vpd_std',
            'days_since_planting', 'yield_g'
        ]
        
        # Prepare features and target
        feature_cols = [col for col in yield_features.columns if col not in ['tray_id', 'yield_g']]
        X = yield_features[feature_cols].fillna(0)
        y = yield_features['yield_g']
        
        if len(X) < 10:
            logger.warning("Insufficient yield data for training")
            return {}
        
        # Train XGBoost model for yield prediction
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        # Time series split for validation
        tscv = TimeSeriesSplit(n_splits=3)
        scores = []
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            mae = mean_absolute_error(y_val, y_pred)
            scores.append(mae)
        
        # Train final model
        model.fit(X, y)
        
        # Save model
        model_key = f"{location}_yield_prediction"
        self.models[model_key] = model
        
        joblib.dump(model, f"data/models/{model_key}_model.pkl")
        
        avg_score = np.mean(scores)
        logger.info(f"Yield model MAE: {avg_score:.4f}")
        
        return {
            'model_name': 'xgboost',
            'mae': avg_score,
            'model_key': model_key,
            'feature_importance': dict(zip(feature_cols, model.feature_importances_))
        }
    
    def predict_short_term(self, location: str, target_column: str = 'temp_avg_1h', hours_ahead: int = 24) -> List[float]:
        """Make short-term predictions"""
        model_key = f"{location}_{target_column}_short_term"
        
        if model_key not in self.models:
            logger.error(f"Model {model_key} not found")
            return []
        
        # Load latest features
        # Need a history window to construct lag features
        query = f"""
        SELECT * FROM processed_features 
        WHERE location = '{location}'
        ORDER BY timestamp DESC 
        LIMIT 48
        """
        
        try:
            latest_data = pd.read_sql_query(query, self.engine)
        except Exception as e:
            logger.error(f"Error loading latest data: {e}")
            return []
        
        if latest_data.empty:
            logger.error("No latest data available")
            return []
        
        # Sort ascending so lags compute correctly
        latest_data = latest_data.sort_values('timestamp').reset_index(drop=True)

        # Prepare features for prediction
        X, _ = self.prepare_features(latest_data.copy(), target_column)
        
        if X.empty:
            logger.error("No valid features for prediction")
            return []
        
        # Scale features
        scaler = self.scalers[model_key]
        X_scaled = scaler.transform(X)
        
        # Make prediction
        model = self.models[model_key]
        # Use the last row for current state prediction
        prediction = model.predict(X_scaled)[-1]
        
        # Generate multiple predictions (simplified approach)
        predictions = [prediction + np.random.normal(0, 0.5) for _ in range(hours_ahead)]
        
        return predictions
    
    def predict_yield(self, location: str, tray_id: str, days_since_planting: int) -> float:
        """Predict yield for a specific tray"""
        model_key = f"{location}_yield_prediction"
        
        if model_key not in self.models:
            logger.error(f"Model {model_key} not found")
            return 0.0
        
        # Get average features for the tray
        query = f"""
        SELECT 
            AVG(temp_avg_1h) as temp_mean,
            STDDEV(temp_avg_1h) as temp_std,
            MIN(temp_avg_1h) as temp_min,
            MAX(temp_avg_1h) as temp_max,
            AVG(humidity_avg_1h) as humidity_mean,
            STDDEV(humidity_avg_1h) as humidity_std,
            MIN(humidity_avg_1h) as humidity_min,
            MAX(humidity_avg_1h) as humidity_max,
            SUM(light_sum_1h) as light_sum,
            AVG(light_avg_1h) as light_mean,
            AVG(soil_moisture_avg_1h) as soil_moisture_mean,
            STDDEV(soil_moisture_avg_1h) as soil_moisture_std,
            AVG(ec_avg_1h) as ec_mean,
            STDDEV(ec_avg_1h) as ec_std,
            AVG(co2_avg_1h) as co2_mean,
            STDDEV(co2_avg_1h) as co2_std,
            AVG(vpd) as vpd_mean,
            STDDEV(vpd) as vpd_std
        FROM processed_features 
        WHERE location = '{location}'
        AND timestamp >= NOW() - INTERVAL '{days_since_planting} days'
        """
        
        try:
            features = pd.read_sql_query(query, self.engine)
        except Exception as e:
            logger.error(f"Error loading tray features: {e}")
            return 0.0
        
        if features.empty:
            logger.error("No features available for yield prediction")
            return 0.0
        
        # Add days since planting
        features['days_since_planting'] = days_since_planting
        
        # Fill NaN values
        features = features.fillna(0)
        
        # Make prediction
        model = self.models[model_key]
        prediction = model.predict(features)[0]
        
        return max(0, prediction)  # Ensure non-negative yield

    def load_saved_model(self, model_key: str) -> bool:
        """Attempt to load a saved model and scaler from disk into memory."""
        try:
            model_path = f"data/models/{model_key}_model.pkl"
            scaler_path = f"data/models/{model_key}_scaler.pkl"
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            logger.info(f"Loaded saved model for {model_key}")
            return True
        except Exception as e:
            logger.warning(f"Could not load saved model {model_key}: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Initialize models
    db_connection = "postgresql://green_user:password@localhost:5432/green_engine"
    models = GrowthForecastingModels(db_connection)
    
    # Train short-term forecast model
    short_term_result = models.train_short_term_forecast_model("greenhouse_a", "temp_avg_1h")
    print(f"Short-term model result: {short_term_result}")
    
    # Train yield prediction model
    yield_result = models.train_long_term_yield_model("greenhouse_a")
    print(f"Yield model result: {yield_result}")
    
    # Make predictions
    temp_predictions = models.predict_short_term("greenhouse_a", "temp_avg_1h", 24)
    print(f"Temperature predictions: {temp_predictions[:5]}")
    
    yield_prediction = models.predict_yield("greenhouse_a", "tray_001", 10)
    print(f"Yield prediction: {yield_prediction:.2f} g")
