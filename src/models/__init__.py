"""
Warif ML Models Package
نظام النماذج الهجين لإدارة محصول الخيار
"""

__version__ = "1.0.0"
__author__ = "Warif Team"
__description__ = "Hybrid ML System for Cucumber Crop Management"

# استيراد الفئات الرئيسية
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

from .data_loader import (
    KaggleDataLoader,
    DataInfo,
)

from .data_processor import (
    DataCleaner,
    DataPreprocessor,
    process_cucumber_data,
)

from .feature_engineering import (
    FeatureEngineer,
    FeatureSelector,
    prepare_features,
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
    # Data Loading
    "KaggleDataLoader",
    "DataInfo",
    # Data Processing
    "DataCleaner",
    "DataPreprocessor",
    "process_cucumber_data",
    # Feature Engineering
    "FeatureEngineer",
    "FeatureSelector",
    "prepare_features",
]

print(f"✅ Warif ML Models v{__version__} loaded successfully")
