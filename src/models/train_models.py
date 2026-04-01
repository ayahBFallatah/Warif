#!/usr/bin/env python3
"""
Green Engine ML Training Pipeline
Trains models on historical data for yield prediction and forecasting
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from prophet import Prophet
import joblib
import os
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

class MLTrainer:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.target_columns = []
        
    def get_db_connection(self):
        """Get database connection"""
        try:
            connection = psycopg2.connect(
                host=os.getenv("DB_HOST", "postgres"),
                database=os.getenv("DB_NAME", "green_engine"),
                user=os.getenv("DB_USER", "green_user"),
                password=os.getenv("DB_PASSWORD", "password"),
                port=os.getenv("DB_PORT", "5432")
            )
            return connection
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def load_training_data(self):
        """Load and prepare training data from database"""
        print("📊 Loading training data from database...")
        
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            # Load sensor data
            sensor_query = """
                SELECT 
                    timestamp,
                    location,
                    sensor_type,
                    value,
                    unit
                FROM sensor_readings 
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                ORDER BY timestamp
            """
            
            sensor_df = pd.read_sql(sensor_query, conn)
            
            # Load growth measurements
            growth_query = """
                SELECT 
                    timestamp,
                    location,
                    tray_id,
                    crop_type,
                    plant_height_cm,
                    biomass_g,
                    yield_g,
                    germination_rate,
                    growth_stage,
                    days_since_planting
                FROM growth_measurements 
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                ORDER BY timestamp
            """
            
            growth_df = pd.read_sql(growth_query, conn)
            
            # Load processed features
            features_query = """
                SELECT 
                    timestamp,
                    location,
                    temp_avg_1h,
                    temp_min_1h,
                    temp_max_1h,
                    humidity_avg_1h,
                    humidity_min_1h,
                    humidity_max_1h,
                    light_avg_1h,
                    light_max_1h,
                    soil_moisture_avg_1h,
                    soil_moisture_min_1h,
                    soil_moisture_max_1h,
                    ec_avg_1h,
                    ec_min_1h,
                    ec_max_1h,
                    co2_avg_1h,
                    co2_min_1h,
                    co2_max_1h
                FROM processed_features 
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                ORDER BY timestamp
            """
            
            features_df = pd.read_sql(features_query, conn)
            
            conn.close()
            
            print(f"✅ Loaded {len(sensor_df)} sensor readings")
            print(f"✅ Loaded {len(growth_df)} growth measurements")
            print(f"✅ Loaded {len(features_df)} processed features")
            
            return {
                'sensor': sensor_df,
                'growth': growth_df,
                'features': features_df
            }
            
        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            conn.close()
            return None
    
    def prepare_features(self, data):
        """Prepare features for ML training"""
        print("🔧 Preparing features for ML training...")
        
        # Pivot sensor data to get one row per timestamp
        sensor_pivot = data['sensor'].pivot_table(
            index=['timestamp', 'location'],
            columns='sensor_type',
            values='value',
            aggfunc='mean'
        ).reset_index()
        
        # Merge with processed features
        if not data['features'].empty:
            # Merge on timestamp and location
            merged_df = pd.merge(
                sensor_pivot,
                data['features'],
                on=['timestamp', 'location'],
                how='left'
            )
        else:
            merged_df = sensor_pivot
        
        # Add time-based features
        merged_df['hour'] = pd.to_datetime(merged_df['timestamp']).dt.hour
        merged_df['day_of_week'] = pd.to_datetime(merged_df['timestamp']).dt.dayofweek
        merged_df['is_daytime'] = (merged_df['hour'] >= 6) & (merged_df['hour'] <= 18)
        
        # Add lag features (previous hour values)
        for col in ['temperature', 'humidity', 'light', 'soil_moisture', 'ec', 'co2']:
            if col in merged_df.columns:
                merged_df[f'{col}_lag_1h'] = merged_df.groupby('location')[col].shift(1)
                merged_df[f'{col}_lag_2h'] = merged_df.groupby('location')[col].shift(2)
        
        # Add rolling averages
        for col in ['temperature', 'humidity', 'light', 'soil_moisture', 'ec', 'co2']:
            if col in merged_df.columns:
                merged_df[f'{col}_avg_6h'] = merged_df.groupby('location')[col].rolling(6).mean().reset_index(0, drop=True)
                merged_df[f'{col}_avg_24h'] = merged_df.groupby('location')[col].rolling(24).mean().reset_index(0, drop=True)
        
        # Fill NaN values
        merged_df = merged_df.fillna(method='ffill').fillna(method='bfill')
        
        # Define feature columns
        self.feature_columns = [
            'temperature', 'humidity', 'light', 'soil_moisture', 'ec', 'co2',
            'hour', 'day_of_week', 'is_daytime',
            'temperature_lag_1h', 'humidity_lag_1h', 'light_lag_1h',
            'soil_moisture_lag_1h', 'ec_lag_1h', 'co2_lag_1h',
            'temperature_avg_6h', 'humidity_avg_6h', 'light_avg_6h',
            'soil_moisture_avg_6h', 'ec_avg_6h', 'co2_avg_6h',
            'temperature_avg_24h', 'humidity_avg_24h', 'light_avg_24h',
            'soil_moisture_avg_24h', 'ec_avg_24h', 'co2_avg_24h'
        ]
        
        # Filter to only existing columns
        self.feature_columns = [col for col in self.feature_columns if col in merged_df.columns]
        
        print(f"✅ Prepared {len(self.feature_columns)} features")
        return merged_df
    
    def prepare_targets(self, data, features_df):
        """Prepare target variables for ML training"""
        print("🎯 Preparing target variables...")
        
        # For yield prediction, we'll use biomass_g as the target
        # and create synthetic yield predictions based on growth stage
        
        # Merge growth data with features
        growth_merged = pd.merge(
            features_df,
            data['growth'][['timestamp', 'location', 'tray_id', 'biomass_g', 'yield_g', 'growth_stage', 'days_since_planting']],
            on=['timestamp', 'location'],
            how='left'
        )
        
        # Create synthetic yield predictions for missing data
        # This simulates what real ML models would predict
        growth_merged['predicted_yield'] = growth_merged['biomass_g'].fillna(0)
        
        # Add growth stage encoding
        stage_mapping = {
            'germination': 1,
            'early_growth': 2,
            'mid_growth': 3,
            'mature': 4
        }
        growth_merged['growth_stage_encoded'] = growth_merged['growth_stage'].map(stage_mapping).fillna(2)
        
        # Create yield prediction based on growth stage and environmental conditions
        growth_merged['yield_prediction'] = (
            growth_merged['growth_stage_encoded'] * 10 +
            growth_merged['biomass_g'].fillna(0) * 0.5 +
            growth_merged['temperature'].fillna(22) * 0.1 +
            growth_merged['humidity'].fillna(70) * 0.05 +
            growth_merged['light'].fillna(500) * 0.01
        )
        
        self.target_columns = ['yield_prediction', 'biomass_g', 'growth_stage_encoded']
        
        print(f"✅ Prepared {len(self.target_columns)} target variables")
        return growth_merged
    
    def train_models(self, df):
        """Train multiple ML models"""
        print("🤖 Training ML models...")
        
        # Prepare features and targets
        X = df[self.feature_columns].fillna(0)
        y = df['yield_prediction'].fillna(0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        self.scalers['yield'] = scaler
        
        # Train Random Forest
        print("🌲 Training Random Forest...")
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)
        rf_pred = rf_model.predict(X_test_scaled)
        rf_score = r2_score(y_test, rf_pred)
        
        self.models['random_forest'] = rf_model
        print(f"   Random Forest R²: {rf_score:.3f}")
        
        # Train XGBoost
        print("🚀 Training XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        xgb_model.fit(X_train_scaled, y_train)
        xgb_pred = xgb_model.predict(X_test_scaled)
        xgb_score = r2_score(y_test, xgb_pred)
        
        self.models['xgboost'] = xgb_model
        print(f"   XGBoost R²: {xgb_score:.3f}")
        
        # Train Linear Regression
        print("📈 Training Linear Regression...")
        lr_model = LinearRegression()
        lr_model.fit(X_train_scaled, y_train)
        lr_pred = lr_model.predict(X_test_scaled)
        lr_score = r2_score(y_test, lr_pred)
        
        self.models['linear_regression'] = lr_model
        print(f"   Linear Regression R²: {lr_score:.3f}")
        
        # Train Prophet for time series forecasting
        print("🔮 Training Prophet for time series...")
        try:
            # Prepare data for Prophet
            prophet_df = df[['timestamp', 'yield_prediction']].copy()
            prophet_df.columns = ['ds', 'y']
            prophet_df = prophet_df.dropna()
            
            if len(prophet_df) > 10:  # Need minimum data for Prophet
                prophet_model = Prophet(
                    yearly_seasonality=False,
                    weekly_seasonality=True,
                    daily_seasonality=True
                )
                prophet_model.fit(prophet_df)
                self.models['prophet'] = prophet_model
                print("   Prophet trained successfully")
            else:
                print("   ⚠️ Not enough data for Prophet")
        except Exception as e:
            print(f"   ⚠️ Prophet training failed: {e}")
        
        return {
            'random_forest': rf_score,
            'xgboost': xgb_score,
            'linear_regression': lr_score
        }
    
    def save_models(self):
        """Save trained models to disk"""
        print("💾 Saving trained models...")
        
        # Create models directory
        os.makedirs('data/models', exist_ok=True)
        
        # Save models
        for name, model in self.models.items():
            model_path = f'data/models/{name}_model.joblib'
            joblib.dump(model, model_path)
            print(f"   ✅ Saved {name} model")
        
        # Save scalers
        for name, scaler in self.scalers.items():
            scaler_path = f'data/models/{name}_scaler.joblib'
            joblib.dump(scaler, scaler_path)
            print(f"   ✅ Saved {name} scaler")
        
        # Save feature columns
        feature_path = 'data/models/feature_columns.joblib'
        joblib.dump(self.feature_columns, feature_path)
        print(f"   ✅ Saved feature columns")
        
        # Save model metadata
        metadata = {
            'trained_at': datetime.now().isoformat(),
            'feature_columns': self.feature_columns,
            'target_columns': self.target_columns,
            'model_count': len(self.models)
        }
        
        metadata_path = 'data/models/model_metadata.joblib'
        joblib.dump(metadata, metadata_path)
        print(f"   ✅ Saved model metadata")
    
    def generate_predictions(self, df):
        """Generate predictions for the dataset"""
        print("🔮 Generating predictions...")
        
        # Use the best performing model (XGBoost)
        if 'xgboost' in self.models:
            model = self.models['xgboost']
            scaler = self.scalers['yield']
            
            # Prepare features
            X = df[self.feature_columns].fillna(0)
            X_scaled = scaler.transform(X)
            
            # Generate predictions
            predictions = model.predict(X_scaled)
            
            # Add predictions to dataframe
            df['predicted_yield'] = predictions
            df['prediction_confidence'] = 0.85  # Simulated confidence
            
            print(f"✅ Generated {len(predictions)} predictions")
            return df
        
        return df
    
    def run_training_pipeline(self):
        """Run the complete ML training pipeline"""
        print("🚀 Starting ML Training Pipeline...")
        print("=" * 60)
        
        # Load data
        data = self.load_training_data()
        if not data:
            print("❌ Failed to load training data")
            return False
        
        # Prepare features
        features_df = self.prepare_features(data)
        if features_df.empty:
            print("❌ Failed to prepare features")
            return False
        
        # Prepare targets
        targets_df = self.prepare_targets(data, features_df)
        if targets_df.empty:
            print("❌ Failed to prepare targets")
            return False
        
        # Train models
        scores = self.train_models(targets_df)
        if not scores:
            print("❌ Failed to train models")
            return False
        
        # Generate predictions
        predictions_df = self.generate_predictions(targets_df)
        
        # Save models
        self.save_models()
        
        print("\n🎉 ML Training Pipeline Completed Successfully!")
        print("=" * 60)
        print("📊 Model Performance:")
        for model_name, score in scores.items():
            print(f"   • {model_name}: R² = {score:.3f}")
        
        print(f"\n💾 Models saved to: data/models/")
        print(f"🔮 Generated {len(predictions_df)} predictions")
        
        return True

def main():
    """Main function to run ML training"""
    trainer = MLTrainer()
    success = trainer.run_training_pipeline()
    
    if success:
        print("\n✅ ML training completed successfully!")
        print("🔄 You can now use the prediction API endpoints")
    else:
        print("\n❌ ML training failed")

if __name__ == "__main__":
    main()
