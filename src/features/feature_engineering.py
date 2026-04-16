"""
Feature Engineering for Warif ML Pipeline
 Features    Cucumber
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"


class FeatureEngineer:
    """
        
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_shape = df.shape
        logger.info("   Feature Engineer")

    def add_temporal_features(self) -> pd.DataFrame:
        """
            datetime index
        """
        logger.info("  Features ...")

        if isinstance(self.df.index, pd.DatetimeIndex):
            self.df['hour'] = self.df.index.hour
            self.df['day_of_week'] = self.df.index.dayofweek
            self.df['day_of_year'] = self.df.index.dayofyear
            self.df['month'] = self.df.index.month

            #  
            self.df['hour_sin'] = np.sin(2 * np.pi * self.df['hour'] / 24)
            self.df['hour_cos'] = np.cos(2 * np.pi * self.df['hour'] / 24)

            logger.info("   Features ")

        return self.df

    def add_lagged_features(self, windows: list = [1, 6, 24]) -> pd.DataFrame:
        """
           (Lagged Features)
        """
        logger.info(f"   ...")

        numeric_cols = self.df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            for window in windows:
                self.df[f'{col}_lag_{window}h'] = self.df[col].shift(window)

        logger.info(f"    ")
        return self.df

    def add_rolling_features(self, windows: list = [6, 24]) -> pd.DataFrame:
        """
           (Rolling Features)
        """
        logger.info(f"   ...")

        numeric_cols = self.df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            for window in windows:
                self.df[f'{col}_rolling_mean_{window}h'] = (
                    self.df[col].rolling(window=window, min_periods=1).mean()
                )
                self.df[f'{col}_rolling_std_{window}h'] = (
                    self.df[col].rolling(window=window, min_periods=1).std()
                )

        logger.info(f"    ")
        return self.df

    def add_interaction_features(self) -> pd.DataFrame:
        """
           (Interaction Features)
        """
        logger.info("   ...")

        #   
        if 'temperature' in self.df.columns and 'humidity' in self.df.columns:
            self.df['temp_humidity'] = (
                self.df['temperature'] * self.df['humidity'] / 100
            )

        if 'light' in self.df.columns and 'temperature' in self.df.columns:
            self.df['light_temp'] = (
                self.df['light'] * self.df['temperature'] / 100
            )

        if 'temperature' in self.df.columns and 'humidity' in self.df.columns:
            # VPD Indicator (  )
            self.df['vpd'] = self.df['temperature'] / (self.df['humidity'] + 1)

        logger.info("    ")
        return self.df

    def engineer_features(self) -> pd.DataFrame:
        """
          Features
        """
        logger.info("\n" + "="*60)
        logger.info("  Feature Engineering")
        logger.info("="*60 + "\n")

        self.add_temporal_features()
        self.add_lagged_features(windows=[1, 6, 24])
        self.add_rolling_features(windows=[6, 24])
        self.add_interaction_features()

        #      lagged features
        self.df = self.df.fillna(0)

        logger.info(f"\n  : {self.original_shape[1]}")
        logger.info(f"  : {self.df.shape[1]}")
        logger.info(f"  : {self.df.shape[0]:,}")
        logger.info(f"  Features : {self.df.shape[1] - self.original_shape[1]}\n")

        return self.df


class FeatureSelector:
    """
    Select  Features
    """

    @staticmethod
    def get_sensor_features() -> list:
        """
            
        """
        return [
            'temperature', 'humidity', 'light', 'soil_moisture', 'ec', 'co2'
        ]

    @staticmethod
    def get_temporal_features() -> list:
        """
          Features 
        """
        return ['hour', 'day_of_week', 'month', 'hour_sin', 'hour_cos']

    @staticmethod
    def correlate_with_target(
        df: pd.DataFrame,
        target_col: str,
        top_n: int = 15
    ) -> pd.DataFrame:
        """
          Features   target
        """
        if target_col not in df.columns:
            logger.warning(f"  {target_col}  ")
            return None

        correlations = df.corr()[target_col].sort_values(ascending=False)
        top_features = correlations.head(top_n + 1)[1:]  #    

        logger.info(f"\n  {top_n}    {target_col}:")
        for feat, corr in top_features.items():
            logger.info(f"   {feat:25}: {corr:7.4f}")

        return top_features


def prepare_features(input_csv: str, output_name: str = "cucumber_features") -> pd.DataFrame:
    """
     Features   

    Args:
        input_csv:    
        output_name:   

    Returns:
        pd.DataFrame:   Features
    """
    logger.info(f" : {input_csv}")
    df = pd.read_csv(input_csv, index_col=0, parse_dates=True)

    #  Features
    engineer = FeatureEngineer(df)
    df_features = engineer.engineer_features()

    # Save 
    output_path = PROCESSED_DATA_DIR / f"{output_name}.csv"
    df_features.to_csv(output_path)
    logger.info(f"  Save: {output_path}\n")

    return df_features


if __name__ == "__main__":
    from data_loader import KaggleDataLoader

    # 
    csv_files = KaggleDataLoader.list_available_files()
    if csv_files:
        #      
        processed_file = PROCESSED_DATA_DIR / "cucumber_processed.csv"
        if processed_file.exists():
            df = prepare_features(str(processed_file))
