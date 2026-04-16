"""
Warif ML Models Package
"""

__version__ = "1.0.0"
__author__ = "Warif Team"
__description__ = "Hybrid ML System for Cucumber Crop Management"

from .config import (
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    MODELS_DIR,
    CUCUMBER_RANGES,
    FORECASTING_CONFIG,
    ANOMALY_CONFIG,
    YIELD_CONFIG,
    IRRIGATION_CONFIG,
)

__all__ = [
    # Configuration
    "DATA_DIR",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "MODELS_DIR",
    "CUCUMBER_RANGES",
    "FORECASTING_CONFIG",
    "ANOMALY_CONFIG",
    "YIELD_CONFIG",
    "IRRIGATION_CONFIG",
]

print(f"Warif ML Models v{__version__} loaded successfully")
