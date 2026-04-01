"""
Anomaly Detection for Green Engine
Detects anomalies in sensor data streams
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import joblib
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetectionSystem:
    """Anomaly detection system for sensor data streams"""
    
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
        self.models = {}
        self.scalers = {}
        self.thresholds = {}
        
        # Define sensor-specific thresholds
        self.sensor_thresholds = {
            'temperature': {'min': 10, 'max': 35, 'std_threshold': 5},
            'humidity': {'min': 30, 'max': 90, 'std_threshold': 15},
            'light': {'min': 0, 'max': 2000, 'std_threshold': 300},
            'soil_moisture': {'min': 10, 'max': 90, 'std_threshold': 20},
            'ec': {'min': 0.5, 'max': 3.0, 'std_threshold': 0.5},
            'co2': {'min': 300, 'max': 2000, 'std_threshold': 200}
        }
    
    def load_sensor_data(self, location: str, sensor_type: str, hours_back: int = 168) -> pd.DataFrame:
        """Load sensor data for anomaly detection"""
        query = f"""
        SELECT timestamp, value, unit
        FROM sensor_readings
        WHERE location = '{location}'
        AND sensor_type = '{sensor_type}'
        AND timestamp >= NOW() - INTERVAL '{hours_back} hours'
        ORDER BY timestamp
        """
        
        try:
            df = pd.read_sql(query, self.db_connection_string)
            logger.info(f"Loaded {len(df)} {sensor_type} readings for {location}")
            return df
        except Exception as e:
            logger.error(f"Error loading sensor data: {e}")
            return pd.DataFrame()
    
    def create_features(self, df: pd.DataFrame, sensor_type: str) -> pd.DataFrame:
        """Create features for anomaly detection"""
        if df.empty:
            return df
        
        # Basic statistical features
        df['value_rolling_mean_1h'] = df['value'].rolling(window=4, min_periods=1).mean()
        df['value_rolling_std_1h'] = df['value'].rolling(window=4, min_periods=1).std()
        df['value_rolling_mean_24h'] = df['value'].rolling(window=96, min_periods=1).mean()
        df['value_rolling_std_24h'] = df['value'].rolling(window=96, min_periods=1).std()
        
        # Rate of change
        df['value_diff'] = df['value'].diff()
        df['value_diff_abs'] = df['value_diff'].abs()
        
        # Z-score
        df['z_score'] = (df['value'] - df['value_rolling_mean_24h']) / (df['value_rolling_std_24h'] + 1e-6)
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_daytime'] = ((df['hour'] >= 6) & (df['hour'] <= 18)).astype(int)
        
        # Threshold violations
        thresholds = self.sensor_thresholds.get(sensor_type, {})
        if thresholds:
            df['below_min'] = (df['value'] < thresholds['min']).astype(int)
            df['above_max'] = (df['value'] > thresholds['max']).astype(int)
            df['threshold_violation'] = df['below_min'] | df['above_max']
        
        return df
    
    def train_isolation_forest(self, location: str, sensor_type: str) -> Dict:
        """Train Isolation Forest model for anomaly detection"""
        logger.info(f"Training Isolation Forest for {sensor_type} at {location}")
        
        # Load data
        df = self.load_sensor_data(location, sensor_type, hours_back=168)  # 1 week
        
        if df.empty:
            logger.error("No data available for training")
            return {}
        
        # Create features
        df = self.create_features(df, sensor_type)
        
        # Select feature columns
        feature_columns = [
            'value', 'value_rolling_mean_1h', 'value_rolling_std_1h',
            'value_rolling_mean_24h', 'value_rolling_std_24h',
            'value_diff', 'value_diff_abs', 'z_score',
            'hour', 'day_of_week', 'is_daytime'
        ]
        
        # Add threshold features if available
        if 'threshold_violation' in df.columns:
            feature_columns.append('threshold_violation')
        
        # Prepare features
        X = df[feature_columns].fillna(0)
        
        if len(X) < 100:
            logger.warning("Insufficient data for training")
            return {}
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train Isolation Forest
        model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )
        
        model.fit(X_scaled)
        
        # Calculate anomaly scores
        anomaly_scores = model.decision_function(X_scaled)
        
        # Set threshold based on scores
        threshold = np.percentile(anomaly_scores, 10)  # Bottom 10% are anomalies
        
        # Save model and scaler
        model_key = f"{location}_{sensor_type}_isolation_forest"
        self.models[model_key] = model
        self.scalers[model_key] = scaler
        self.thresholds[model_key] = threshold
        
        # Save to disk
        joblib.dump(model, f"data/models/{model_key}_model.pkl")
        joblib.dump(scaler, f"data/models/{model_key}_scaler.pkl")
        joblib.dump(threshold, f"data/models/{model_key}_threshold.pkl")
        
        logger.info(f"Isolation Forest trained for {model_key}")
        
        return {
            'model_type': 'isolation_forest',
            'threshold': threshold,
            'training_samples': len(X),
            'feature_columns': feature_columns
        }
    
    def train_local_outlier_factor(self, location: str, sensor_type: str) -> Dict:
        """Train Local Outlier Factor model for anomaly detection"""
        logger.info(f"Training LOF for {sensor_type} at {location}")
        
        # Load data
        df = self.load_sensor_data(location, sensor_type, hours_back=168)
        
        if df.empty:
            logger.error("No data available for training")
            return {}
        
        # Create features
        df = self.create_features(df, sensor_type)
        
        # Select feature columns
        feature_columns = [
            'value', 'value_rolling_mean_1h', 'value_rolling_std_1h',
            'value_rolling_mean_24h', 'value_rolling_std_24h',
            'value_diff', 'value_diff_abs', 'z_score',
            'hour', 'day_of_week', 'is_daytime'
        ]
        
        # Prepare features
        X = df[feature_columns].fillna(0)
        
        if len(X) < 100:
            logger.warning("Insufficient data for training")
            return {}
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train LOF
        model = LocalOutlierFactor(
            contamination=0.1,
            n_neighbors=20,
            novelty=True
        )
        
        model.fit(X_scaled)
        
        # Save model and scaler
        model_key = f"{location}_{sensor_type}_lof"
        self.models[model_key] = model
        self.scalers[model_key] = scaler
        
        # Save to disk
        joblib.dump(model, f"data/models/{model_key}_model.pkl")
        joblib.dump(scaler, f"data/models/{model_key}_scaler.pkl")
        
        logger.info(f"LOF trained for {model_key}")
        
        return {
            'model_type': 'local_outlier_factor',
            'training_samples': len(X),
            'feature_columns': feature_columns
        }
    
    def detect_anomalies(self, location: str, sensor_type: str, hours_back: int = 24) -> pd.DataFrame:
        """Detect anomalies in recent sensor data"""
        logger.info(f"Detecting anomalies for {sensor_type} at {location}")
        
        # Load recent data
        df = self.load_sensor_data(location, sensor_type, hours_back)
        
        if df.empty:
            logger.error("No data available for anomaly detection")
            return pd.DataFrame()
        
        # Create features
        df = self.create_features(df, sensor_type)
        
        # Try different models
        anomaly_results = []
        
        # Isolation Forest
        model_key_if = f"{location}_{sensor_type}_isolation_forest"
        if model_key_if in self.models:
            try:
                feature_columns = [
                    'value', 'value_rolling_mean_1h', 'value_rolling_std_1h',
                    'value_rolling_mean_24h', 'value_rolling_std_24h',
                    'value_diff', 'value_diff_abs', 'z_score',
                    'hour', 'day_of_week', 'is_daytime'
                ]
                
                X = df[feature_columns].fillna(0)
                scaler = self.scalers[model_key_if]
                X_scaled = scaler.transform(X)
                
                model = self.models[model_key_if]
                scores = model.decision_function(X_scaled)
                threshold = self.thresholds[model_key_if]
                
                df['if_anomaly_score'] = scores
                df['if_is_anomaly'] = scores < threshold
                anomaly_results.append('isolation_forest')
                
            except Exception as e:
                logger.error(f"Error with Isolation Forest: {e}")
        
        # Local Outlier Factor
        model_key_lof = f"{location}_{sensor_type}_lof"
        if model_key_lof in self.models:
            try:
                feature_columns = [
                    'value', 'value_rolling_mean_1h', 'value_rolling_std_1h',
                    'value_rolling_mean_24h', 'value_rolling_std_24h',
                    'value_diff', 'value_diff_abs', 'z_score',
                    'hour', 'day_of_week', 'is_daytime'
                ]
                
                X = df[feature_columns].fillna(0)
                scaler = self.scalers[model_key_lof]
                X_scaled = scaler.transform(X)
                
                model = self.models[model_key_lof]
                predictions = model.predict(X_scaled)
                
                df['lof_is_anomaly'] = predictions == -1
                anomaly_results.append('local_outlier_factor')
                
            except Exception as e:
                logger.error(f"Error with LOF: {e}")
        
        # Rule-based anomaly detection
        thresholds = self.sensor_thresholds.get(sensor_type, {})
        if thresholds:
            df['rule_based_anomaly'] = (
                (df['value'] < thresholds['min']) | 
                (df['value'] > thresholds['max']) |
                (df['z_score'].abs() > 3)  # 3-sigma rule
            )
            anomaly_results.append('rule_based')
        
        # Combined anomaly score
        anomaly_columns = [col for col in df.columns if 'anomaly' in col and col != 'rule_based_anomaly']
        if anomaly_columns:
            df['combined_anomaly_score'] = df[anomaly_columns].sum(axis=1)
            df['is_anomaly'] = df['combined_anomaly_score'] >= 1
        
        logger.info(f"Anomaly detection completed using: {anomaly_results}")
        
        return df
    
    def store_anomaly_results(self, df: pd.DataFrame, location: str, sensor_type: str):
        """Store anomaly detection results in database"""
        if df.empty:
            return
        
        try:
            # Prepare data for storage
            anomaly_data = df[['timestamp', 'value', 'is_anomaly']].copy()
            anomaly_data['location'] = location
            anomaly_data['sensor_type'] = sensor_type
            anomaly_data['anomaly_score'] = df.get('combined_anomaly_score', 0)
            
            # Store in database (simplified - would need proper table structure)
            logger.info(f"Stored {len(anomaly_data)} anomaly results for {sensor_type} at {location}")
            
        except Exception as e:
            logger.error(f"Error storing anomaly results: {e}")
    
    def generate_anomaly_alerts(self, df: pd.DataFrame, location: str, sensor_type: str) -> List[Dict]:
        """Generate alerts for detected anomalies"""
        alerts = []
        
        if df.empty:
            return alerts
        
        # Find anomalies
        anomalies = df[df['is_anomaly'] == True]
        
        for _, row in anomalies.iterrows():
            alert = {
                'timestamp': row['timestamp'],
                'location': location,
                'sensor_type': sensor_type,
                'alert_type': 'anomaly',
                'severity': 'medium',
                'title': f'Anomaly detected in {sensor_type}',
                'description': f'Unusual {sensor_type} reading: {row["value"]} at {row["timestamp"]}',
                'sensor_id': f'{sensor_type}_001',
                'threshold_value': None,
                'actual_value': row['value']
            }
            alerts.append(alert)
        
        return alerts

# Example usage
if __name__ == "__main__":
    # Initialize anomaly detection system
    db_connection = "postgresql://green_user:password@localhost:5432/green_engine"
    anomaly_system = AnomalyDetectionSystem(db_connection)
    
    # Train models for different sensors
    sensors = ['temperature', 'humidity', 'light', 'soil_moisture']
    
    for sensor in sensors:
        # Train Isolation Forest
        if_result = anomaly_system.train_isolation_forest("greenhouse_a", sensor)
        print(f"Isolation Forest for {sensor}: {if_result}")
        
        # Train LOF
        lof_result = anomaly_system.train_local_outlier_factor("greenhouse_a", sensor)
        print(f"LOF for {sensor}: {lof_result}")
    
    # Detect anomalies
    for sensor in sensors:
        anomalies = anomaly_system.detect_anomalies("greenhouse_a", sensor, hours_back=24)
        if not anomalies.empty:
            anomaly_count = anomalies['is_anomaly'].sum()
            print(f"Detected {anomaly_count} anomalies in {sensor}")
            
            # Generate alerts
            alerts = anomaly_system.generate_anomaly_alerts(anomalies, "greenhouse_a", sensor)
            print(f"Generated {len(alerts)} alerts for {sensor}")
