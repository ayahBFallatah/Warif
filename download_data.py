#!/usr/bin/env python3
"""
Warif Data Initializer (Deep Learning Twin)

STRICT PROTOCOL: Generative and synthetic datasets are banned from the Digital Twin.
Please insert your downloaded external dataset into the `data/raw/` directory.

Supported External Data Sources (Cucumber Focus):
1. Wageningen University Dataset (Highly Recommended)
   - https://data.4tu.nl/articles/dataset/Autonomous_Greenhouse_Challenge_Second_Edition_2019_/12764777
2. Kaggle IoT Agritech
   - https://www.kaggle.com/datasets/moezali/greenhouse-crop-yields-iot-agritech

Place the root .csv file inside `WarifBackend/Warif/data/raw/`
"""

import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).parent / "data" / "raw"

def setup_directories():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Target raw directory verified: {RAW_DATA_DIR}")

def verify_real_data_exists():
    csv_files = list(RAW_DATA_DIR.glob("*.csv"))
    if not csv_files:
        logger.error(f"CRITICAL: No authentic data found in {RAW_DATA_DIR}")
        logger.error("Please manually download the Greenhouse Cucumber dataset from Kaggle or 4TU and place the .csv here.")
        return False
    
    logger.info(f"Found {len(csv_files)} authentic datasets ready for Deep Learning ingestion.")
    for f in csv_files:
        logger.info(f"  - {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
    return True

if __name__ == "__main__":
    logger.info("Warif Deep Learning Data Authenticator")
    setup_directories()
    
    if verify_real_data_exists():
        logger.info("Environment ready. You may proceed with `start_training.py`.")
    else:
        logger.info("Training is blocked until real data is supplied.")
