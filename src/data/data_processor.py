"""
Data Processor for Warif ML Pipeline
   Cucumber
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

#   Cucumber 
CUCUMBER_RANGES = {
    "temperature": {"min": 15, "max": 30},
    "humidity": {"min": 40, "max": 90},
    "light": {"min": 500, "max": 5000},
    "soil_moisture": {"min": 20, "max": 85},
    "ec": {"min": 1.0, "max": 3.5},
    "co2": {"min": 300, "max": 1200},
}

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


class DataCleaner:
    """
    Clean Data     
    """

    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        method: str = "interpolate",
        threshold: float = 0.15
    ) -> pd.DataFrame:
        """
          

        Args:
            df: DataFrame
            method: 'interpolate'  'forward_fill'  'drop'
            threshold:     

        Returns:
            pd.DataFrame:  
        """
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))

        if missing_pct > threshold:
            logger.warning(f"    {missing_pct*100:.2f}% ")

        if method == "interpolate":
            df = df.interpolate(method='linear', limit_direction='both')
        elif method == "forward_fill":
            df = df.fillna(method='ffill').fillna(method='bfill')
        elif method == "drop":
            df = df.dropna()

        remaining = df.isnull().sum().sum()
        logger.info(f"    (: {remaining})")
        return df

    @staticmethod
    def remove_outliers(df: pd.DataFrame, std_threshold: float = 3) -> pd.DataFrame:
        """
            Z-score

        Args:
            df: DataFrame
            std_threshold:   

        Returns:
            pd.DataFrame:   
        """
        initial_len = len(df)
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()

            if std == 0:
                continue

            z_scores = np.abs((df[col] - mean) / std)
            df = df[z_scores <= std_threshold]

        removed = initial_len - len(df)
        logger.info(f"  {removed}  ")
        return df

    @staticmethod
    def validate_sensor_ranges(df: pd.DataFrame) -> pd.DataFrame:
        """
            
        """
        initial_len = len(df)

        for sensor, ranges in CUCUMBER_RANGES.items():
            if sensor not in df.columns:
                continue

            min_val, max_val = ranges["min"], ranges["max"]
            df = df[(df[sensor] >= min_val) & (df[sensor] <= max_val)]

        removed = initial_len - len(df)
        logger.info(f"      ( {removed} )")
        return df

    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
        """
          
        """
        duplicates = df.duplicated().sum()
        df = df.drop_duplicates()
        logger.info(f"  {duplicates}  ")
        return df

    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """
         
        """
        logger.info("\n" + "="*60)
        logger.info("  Clean Data")
        logger.info("="*60)
        logger.info(f" : {len(df):,}   {len(df.columns)} \n")

        df = DataCleaner.remove_duplicates(df)
        df = DataCleaner.handle_missing_values(df)

        logger.info(f"\n  : {len(df):,}   {len(df.columns)} ")
        logger.info("="*60 + "\n")

        return df


class DataPreprocessor:
    """
      
    """

    @staticmethod
    def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
          
        """
        df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_")
        return df

    @staticmethod
    def add_datetime_index(df: pd.DataFrame, datetime_col: Optional[str] = None) -> pd.DataFrame:
        """
            index
        """
        if datetime_col is None:
            #  
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    datetime_col = col
                    break

        if datetime_col and datetime_col in df.columns:
            df[datetime_col] = pd.to_datetime(df[datetime_col])
            df = df.sort_values(by=datetime_col)
            df.set_index(datetime_col, inplace=True)
            logger.info(f"   datetime index : {datetime_col}")

        return df

    @staticmethod
    def save_processed(df: pd.DataFrame, filename: str):
        """
        Save  
        """
        output_path = PROCESSED_DATA_DIR / f"{filename}.csv"
        df.to_csv(output_path)
        logger.info(f"  Save: {output_path}")
        return output_path


def process_cucumber_data(input_csv: str, output_name: str = "cucumber_processed") -> pd.DataFrame:
    """
    Process cucumber dataset
    """
    logger.info(f"Loading data from: {input_csv}")
    df = pd.read_csv(input_csv, low_memory=False)

    # Coerce all columns except time/date to numeric, replacing strings with NaN
    for col in df.columns:
        if 'time' not in col.lower() and 'date' not in col.lower():
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Column standardization
    df = DataPreprocessor.standardize_columns(df)
    df = DataPreprocessor.add_datetime_index(df)

    # Clean data operations
    df = DataCleaner.clean(df)

    # Save
    DataPreprocessor.save_processed(df, output_name)

    return df


if __name__ == "__main__":
    #   
    import sys
    from data_loader import KaggleDataLoader

    csv_files = KaggleDataLoader.list_available_files()
    if csv_files:
        df = process_cucumber_data(str(csv_files[0]))
