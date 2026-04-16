"""
Feature Engineering Pipeline for Warif
Processes raw sensor data into ML-ready features
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureEngineeringPipeline:
    """Feature engineering pipeline for microgreen growth data"""
    
    def __init__(self):
        self.db_engine = create_engine(
            f"postgresql://{os.getenv('DB_USER', 'warif_user')}:"
            f"{os.getenv('DB_PASSWORD', 'password')}@"
            f"{os.getenv('DB_HOST', 'postgres')}:"
            f"{os.getenv('DB_PORT', '5432')}/"
            f"{os.getenv('DB_NAME', 'warif')}"
        )
    
    def get_raw_sensor_data(self, location: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Retrieve raw sensor data from database"""
        query = """
        SELECT timestamp, sensor_id, location, sensor_type, value, unit
        FROM sensor_readings
        WHERE location = %s 
        AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp
        """
        
        try:
            df = pd.read_sql_query(
                query, 
                self.db_engine, 
                params=(location, start_time, end_time)
            )
            logger.info(f"Retrieved {len(df)} sensor readings for {location}")
            return df
        except Exception as e:
            logger.error(f"Error retrieving sensor data: {e}")
            return pd.DataFrame()
    
    def pivot_sensor_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pivot sensor data to wide format with columns for each sensor type"""
        if df.empty:
            return df
        
        # Pivot the data
        pivoted = df.pivot_table(
            index=['timestamp', 'location'],
            columns='sensor_type',
            values='value',
            aggfunc='mean'
        ).reset_index()
        
        # Rename columns to be more descriptive
        pivoted.columns.name = None
        pivoted = pivoted.rename(columns={
            'temperature': 'temp',
            'humidity': 'humidity',
            'light': 'light',
            'soil_moisture': 'soil_moisture',
            'ec': 'ec',
            'co2': 'co2'
        })
        
        return pivoted
    
    def calculate_hourly_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate hourly aggregated features"""
        if df.empty:
            return df
        
        # Set timestamp as index for resampling
        df = df.set_index('timestamp')
        
        # Resample to hourly and calculate statistics
        hourly_features = df.resample('1H').agg({
            'temp': ['mean', 'min', 'max', 'std'],
            'humidity': ['mean', 'min', 'max', 'std'],
            'light': ['sum', 'mean', 'max'],
            'soil_moisture': ['mean', 'min', 'max'],
            'ec': ['mean', 'min', 'max'],
            'co2': ['mean', 'min', 'max', 'std']
        }).reset_index()
        
        # Flatten column names
        hourly_features.columns = [
            'timestamp',
            'temp_avg_1h', 'temp_min_1h', 'temp_max_1h', 'temp_std_1h',
            'humidity_avg_1h', 'humidity_min_1h', 'humidity_max_1h', 'humidity_std_1h',
            'light_sum_1h', 'light_avg_1h', 'light_max_1h',
            'soil_moisture_avg_1h', 'soil_moisture_min_1h', 'soil_moisture_max_1h',
            'ec_avg_1h', 'ec_min_1h', 'ec_max_1h',
            'co2_avg_1h', 'co2_min_1h', 'co2_max_1h', 'co2_std_1h'
        ]
        
        return hourly_features
    
    def calculate_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate rolling window features"""
        if df.empty:
            return df
        
        # 24-hour rolling features
        rolling_24h = df.rolling(window=24, min_periods=1).agg({
            'temp_avg_1h': ['mean', 'std'],
            'humidity_avg_1h': ['mean', 'std'],
            'light_sum_1h': ['sum', 'std'],
            'soil_moisture_avg_1h': ['mean', 'std'],
            'ec_avg_1h': ['mean', 'std'],
            'co2_avg_1h': ['mean', 'std']
        })
        
        # Flatten column names
        rolling_24h.columns = [
            'temp_avg_24h', 'temp_variance_24h',
            'humidity_avg_24h', 'humidity_variance_24h',
            'light_sum_24h', 'light_variance_24h',
            'soil_moisture_avg_24h', 'soil_moisture_variance_24h',
            'ec_avg_24h', 'ec_variance_24h',
            'co2_avg_24h', 'co2_variance_24h'
        ]
        
        return rolling_24h.reset_index()
    
    def calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived features for ML models"""
        if df.empty:
            return df
        
        # Temperature-Humidity ratio
        df['temp_humidity_ratio'] = df['temp_avg_1h'] / (df['humidity_avg_1h'] + 1e-6)
        
        # Light-Temperature ratio
        df['light_temp_ratio'] = df['light_avg_1h'] / (df['temp_avg_1h'] + 1e-6)
        
        # Vapor Pressure Deficit (VPD) - simplified calculation
        # VPD = (1 - RH/100) * SVP, where SVP is saturated vapor pressure
        def calculate_vpd(temp, humidity):
            # Magnus formula for saturated vapor pressure (simplified)
            svp = 6.112 * np.exp((17.67 * temp) / (temp + 243.5))
            vpd = (1 - humidity/100) * svp
            return vpd
        
        df['vpd'] = calculate_vpd(df['temp_avg_1h'], df['humidity_avg_1h'])
        
        # Light hours above threshold (assuming 200 lux threshold)
        df['light_hours_above_threshold'] = (df['light_avg_1h'] > 200).astype(int)
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_daytime'] = ((df['hour'] >= 6) & (df['hour'] <= 18)).astype(int)
        
        return df
    
    def store_processed_features(self, df: pd.DataFrame, location: str):
        """Store processed features in database"""
        if df.empty:
            logger.warning("No features to store")
            return
        
        try:
            # Add location column
            df['location'] = location
            
            # Store in database
            df.to_sql(
                'processed_features', 
                self.db_engine, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            
            logger.info(f"Stored {len(df)} processed features for {location}")
            
        except Exception as e:
            logger.error(f"Error storing processed features: {e}")
    
    def run_feature_engineering(self, location: str, hours_back: int = 24):
        """Run complete feature engineering pipeline"""
        logger.info(f"Starting feature engineering for {location}")
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Get raw sensor data
        raw_data = self.get_raw_sensor_data(location, start_time, end_time)
        
        if raw_data.empty:
            logger.warning(f"No raw data found for {location}")
            return
        
        # Pivot data
        pivoted_data = self.pivot_sensor_data(raw_data)
        
        # Calculate hourly features
        hourly_features = self.calculate_hourly_features(pivoted_data)
        
        # Calculate rolling features
        rolling_features = self.calculate_rolling_features(hourly_features)
        
        # Merge features
        all_features = hourly_features.merge(rolling_features, on='timestamp', how='left')
        
        # Calculate derived features
        final_features = self.calculate_derived_features(all_features)
        
        # Store processed features
        self.store_processed_features(final_features, location)
        
        logger.info(f"Feature engineering completed for {location}")
        
        return final_features

# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = FeatureEngineeringPipeline()
    
    # Run feature engineering for a specific location
    features = pipeline.run_feature_engineering("greenhouse_a", hours_back=48)
    
    print(f"Generated {len(features)} feature rows")
    print(f"Feature columns: {list(features.columns)}")
