"""
Configuration for Warif ML Models
الإعدادات المركزية للنماذج
"""

from pathlib import Path
import os

# ================== Project Paths ==================
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"

# Create directories
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ================== Crop Configuration ==================
CROP_TYPE = "cucumber"

# نطاقات القيم الآمنة للخيار
CUCUMBER_RANGES = {
    "temperature": {"min": 15, "max": 30, "optimal": (20, 25)},
    "humidity": {"min": 40, "max": 90, "optimal": (70, 80)},
    "light": {"min": 500, "max": 5000, "optimal": (2000, 5000)},
    "soil_moisture": {"min": 20, "max": 85, "optimal": (60, 70)},
    "ec": {"min": 1.0, "max": 3.5, "optimal": (1.5, 2.0)},
    "co2": {"min": 300, "max": 1200, "optimal": (600, 800)},
}

# ================== ML Models Configuration ==================

# Forecasting Model (التنبؤ بـ 72 ساعة قادمة)
FORECASTING_CONFIG = {
    "model_type": "xgboost",
    "forecast_horizon": 72,  # ساعة
    "window_size": 168,  # 7 أيام lookback
    "hyperparameters": {
        "n_estimators": 100,
        "max_depth": 5,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },
}

# Anomaly Detection Model (كشف الشذوذ)
ANOMALY_CONFIG = {
    "model_type": "isolation_forest",
    "hyperparameters": {
        "contamination": 0.05,
        "n_estimators": 100,
    },
}

# Yield Prediction Model (التنبؤ بالإنتاجية)
YIELD_CONFIG = {
    "model_type": "random_forest",
    "hyperparameters": {
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 5,
    },
}

# Irrigation Optimizer (تحسين الري)
IRRIGATION_CONFIG = {
    "model_type": "gradient_boosting",
    "hyperparameters": {
        "n_estimators": 100,
        "learning_rate": 0.05,
        "max_depth": 4,
    },
}

# ================== Training Configuration ==================
TRAINING_CONFIG = {
    "test_size": 0.2,
    "validation_size": 0.1,
    "random_state": 42,
    "epochs": 50,
    "batch_size": 32,
    "verbose": 1,
}

# ================== Data Processing ==================
MISSING_VALUE_THRESHOLD = 0.15  # 15% max
OUTLIER_STD_THRESHOLD = 3

# Feature columns
SENSOR_FEATURES = [
    "temperature", "humidity", "light", "soil_moisture", "ec", "co2"
]

TEMPORAL_FEATURES = [
    "hour", "day_of_week", "month", "hour_sin", "hour_cos"
]

# ================== Database Configuration ==================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "warif"),
    "user": os.getenv("DB_USER", "warif_user"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": os.getenv("DB_PORT", "5432"),
}

# ================== Logging ==================
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

print("✅ Configuration loaded successfully")
