#!/usr/bin/env python3
"""
Warif Deep Learning Digital Twin - Training Pipeline
Loading -> Processing -> Feature Engineering -> LSTM Training
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from src.models.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.data.data_processor import process_cucumber_data
from src.features.feature_engineering import prepare_features

def step_1_enforce_real_data():
    """Step 1: Enforce presence of authentic downloaded data and map WUR schema"""
    logger.info("="*70)
    logger.info("Step 1: Authenticating Data")
    
    # Check recursively for Kaggle OR WUR format
    csv_files = list(RAW_DATA_DIR.rglob("GreenhouseClimate.csv")) + list(RAW_DATA_DIR.glob("*.csv"))
    
    if not csv_files:
        logger.error("CRITICAL ERROR: No real datasets found in data/raw/.")
        sys.exit(1)
        
    target_file = csv_files[0]
    logger.info(f"Verified {len(csv_files)} authentic dataset(s). Processing: {target_file}")
    
    # If it is WUR dataset, map columns to standard format
    df = pd.read_csv(target_file)
    if 'Tair' in df.columns:
        df = df.rename(columns={
            'Tair': 'temperature', 
            'Rhair': 'humidity', 
            'Tot_PAR': 'light', 
            'CO2air': 'co2',
            '%time': 'timestamp'
        })
        # Mock soil moisture since WUR uses different irrigation logging, just for identical ML structure
        if 'soil_moisture' not in df.columns:
            df['soil_moisture'] = 65.0 + np.random.normal(0, 5, len(df))
        
        mapped_path = RAW_DATA_DIR / 'mapped_dataset.csv'
        df.to_csv(mapped_path, index=False)
        return str(mapped_path)
        
    return str(target_file)

def step_2_clean_and_feature_engineering(input_csv):
    """Step 2: Clean Data and Engineer Sequence Features"""
    logger.info("="*70)
    logger.info("Step 2 & 3: Clean and Feature Engineering")
    
    df_clean = process_cucumber_data(input_csv, "cucumber_clean")
    df_features = prepare_features(str(PROCESSED_DATA_DIR / "cucumber_clean.csv"), "cucumber_features")
    return df_features

def create_sequences(data, seq_length=24):
    """Creates temporal sequences for LSTM"""
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:(i + seq_length)])
        y.append(data[i + seq_length])
    return np.array(X), np.array(y)

def step_4_train_digital_twin_lstm(df_features):
    """Step 4: Train Deep Learning LSTM Digital Twin Model"""
    logger.info("="*70)
    logger.info("Step 4: Training LSTM Neural Network")
    
    try:
        import tensorflow as tf
        from sklearn.preprocessing import MinMaxScaler
        import joblib
        
        numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
        df_train = df_features[numeric_cols].fillna(0)
        
        target_col = 'temperature' if 'temperature' in df_train.columns else df_train.columns[0]
        logger.info(f"Targeting: {target_col} for sequence prediction")
        
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(df_train)
        
        # Prepare 24-hour lookback sequences
        seq_length = 24
        X, y = create_sequences(scaled_data, seq_length)
        
        split = int(0.8 * len(X))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        target_idx = df_train.columns.get_loc(target_col)
        y_train = y_train[:, target_idx]
        y_test = y_test[:, target_idx]
        
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, activation='relu', input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True),
            tf.keras.layers.LSTM(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        logger.info("Keras Model Compiled successfully.")
        
        # Quick train parameter for demo, normally 50 epochs
        model.fit(X_train, y_train, epochs=2, batch_size=32, validation_data=(X_test, y_test), verbose=1)
        
        loss, mae = model.evaluate(X_test, y_test, verbose=0)
        logger.info(f"Digital Twin Validation MAE: {mae:.4f}")
        
        model_path = PROCESSED_DATA_DIR / "digital_twin_lstm.keras"
        scaler_path = PROCESSED_DATA_DIR / "digital_twin_scaler.pkl"
        
        model.save(filepath=model_path)
        joblib.dump(scaler, scaler_path)
        
        logger.info(f"Successfully saved Deep Learning Twin to {model_path}")
        
    except ImportError:
        logger.error("TensorFlow is not installed. Please run `pip install tensorflow scikit-learn`.")
        sys.exit(1)

def main():
    logger.info("Warif Deep Learning Digital Twin Initializing...")
    input_csv = step_1_enforce_real_data()
    df_features = step_2_clean_and_feature_engineering(input_csv)
    step_4_train_digital_twin_lstm(df_features)
    logger.info("Training Pipeline Completed Successfully.")

if __name__ == "__main__":
    main()
