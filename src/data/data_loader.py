"""
Data Loader for Warif ML Pipeline
Loading and preparing cucumber data from Kaggle
"""

import os
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define data directories
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Create directories if they do not exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

class KaggleDataLoader:
    """
    Load Data from Kaggle
    """

    @staticmethod
    def download_dataset(dataset_name: str, force_download: bool = False) -> bool:
        """
        Download dataset from Kaggle

        Args:
            dataset_name: dataset name (e.g. 'dataset/cucumber-growth-data')
            force_download: if True, download even if exists

        Returns:
            bool: Download success status
        """
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()

            logger.info(f"Downloading dataset: {dataset_name}")
            api.dataset_download_files(
                dataset_name,
                path=str(RAW_DATA_DIR),
                unzip=True
            )
            logger.info(f"Successfully downloaded to: {RAW_DATA_DIR}")
            return True

        except Exception as e:
            logger.error(f"Download Error: {e}")
            return False

    @staticmethod
    def list_available_files() -> list:
        """
        List available CSV files
        """
        csv_files = list(RAW_DATA_DIR.glob("*.csv"))
        if not csv_files:
            logger.warning("No CSV files available in data/raw/")
            return []

        logger.info("Available Files:")
        for f in csv_files:
            file_size = f.stat().st_size / 1024 / 1024  # MB
            logger.info(f"  - {f.name} ({file_size:.2f} MB)")
        return csv_files

    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        """
        Load CSV file

        Args:
            file_path: CSV file path

        Returns:
            pd.DataFrame: Data
        """
        try:
            logger.info(f"Loading: {Path(file_path).name}")
            df = pd.read_csv(file_path)
            logger.info(f"Loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
            return df
        except Exception as e:
            logger.error(f"Error: {e}")
            return None


class DataInfo:
    """
    Display data info
    """

    @staticmethod
    def show_info(df: pd.DataFrame):
        """
        Display detailed information about the data
        """
        if df is None or df.empty:
            logger.warning("Data is empty")
            return

        logger.info("\n" + "="*60)
        logger.info("Data Information:")
        logger.info("="*60)

        logger.info(f"Row Count: {len(df):,}")
        logger.info(f"Column Count: {len(df.columns)}")
        logger.info(f"Memory Size: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        logger.info("\nColumns:")
        for i, col in enumerate(df.columns, 1):
            dtype = df[col].dtype
            missing = df[col].isnull().sum()
            missing_pct = (missing / len(df)) * 100
            logger.info(f"  {i}. {col:20} | {str(dtype):15} | Missing: {missing_pct:.2f}%")

        logger.info("\nStatistical Values:")
        logger.info(df.describe().to_string())

        logger.info("\n" + "="*60 + "\n")


def main():
    """
    Usage example
    """
    logger.info("Warif Data Loader")
    logger.info("="*60)

    # List available files
    logger.info("\n1. Available Files:")
    csv_files = KaggleDataLoader.list_available_files()

    if not csv_files:
        logger.info("""
        To download data from Kaggle:
           python -m src.data.data_loader --download "dataset/cucumber-growth-data"

        Kaggle dataset examples:
           - dataset/cucumber-growth-data
           - dataset/greenhouse-climate-data
           - dataset/plant-yield-prediction
        """)
        return

    # Select first file
    csv_file = csv_files[0]
    logger.info(f"\n2. Loading file: {csv_file.name}")
    df = KaggleDataLoader.load_csv(str(csv_file))

    if df is not None:
        logger.info(f"\n3. Data Information:")
        DataInfo.show_info(df)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Warif Data Loader")
    parser.add_argument(
        "--download",
        type=str,
        help="Download from Kaggle (format: 'dataset/name')"
    )

    args = parser.parse_args()

    if args.download:
        KaggleDataLoader.download_dataset(args.download)
    else:
        main()
