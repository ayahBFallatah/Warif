#!/usr/bin/env python3
"""
Deep Learning Digital Twin Models
Contains core neural network logic (LSTM Autoencoders, TCNs) 
for the greenhouse digital twin simulation and anomaly detection.
"""

import tensorflow as tf
from tensorflow.keras import layers, models, Model # type: ignore
import numpy as np

def build_lstm_forecaster(seq_length: int, num_features: int) -> Model:
    """
    Builds the core LSTM network for Deep Learning Time-Series forecasting.
    """
    model = models.Sequential([
        layers.LSTM(64, activation='relu', input_shape=(seq_length, num_features), return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(32, activation='relu'),
        layers.Dense(16, activation='relu'),
        layers.Dense(1) # Predicts 1 target (e.g. Temperature or Soil Moisture)
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def build_autoencoder_anomaly_detector(seq_length: int, num_features: int) -> Model:
    """
    Builds an LSTM-Autoencoder to learn the 'normal' state of the biological greenhouse.
    High reconstruction error indicates anomalies (e.g. broken sensor, leakage).
    """
    inputs = layers.Input(shape=(seq_length, num_features))
    
    # Encoder
    encoded = layers.LSTM(32, activation='relu', return_sequences=False)(inputs)
    encoded = layers.RepeatVector(seq_length)(encoded)
    
    # Decoder
    decoded = layers.LSTM(32, activation='relu', return_sequences=True)(encoded)
    outputs = layers.TimeDistributed(layers.Dense(num_features))(decoded)
    
    autoencoder = models.Model(inputs, outputs)
    autoencoder.compile(optimizer='adam', loss='mse')
    return autoencoder
