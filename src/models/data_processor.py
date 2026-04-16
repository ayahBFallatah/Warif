"""
Data Processor for Warif ML Pipeline
تنظيف ومعالجة بيانات الخيار
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# نطاقات قيم الخيار الآمنة
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
    تنظيف البيانات من الأخطاء والقيم غير الصحيحة
    """

    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        method: str = "interpolate",
        threshold: float = 0.15
    ) -> pd.DataFrame:
        """
        معالجة القيم الناقصة

        Args:
            df: DataFrame
            method: 'interpolate' أو 'forward_fill' أو 'drop'
            threshold: نسبة القيم الناقصة المسموح بها

        Returns:
            pd.DataFrame: بعد المعالجة
        """
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))

        if missing_pct > threshold:
            logger.warning(f"⚠️ نسبة القيم الناقصة {missing_pct*100:.2f}% عالية")

        if method == "interpolate":
            df = df.interpolate(method='linear', limit_direction='both')
        elif method == "forward_fill":
            df = df.fillna(method='ffill').fillna(method='bfill')
        elif method == "drop":
            df = df.dropna()

        remaining = df.isnull().sum().sum()
        logger.info(f"✅ معالجة القيم الناقصة (المتبقي: {remaining})")
        return df

    @staticmethod
    def remove_outliers(df: pd.DataFrame, std_threshold: float = 3) -> pd.DataFrame:
        """
        إزالة القيم الشاذة باستخدام Z-score

        Args:
            df: DataFrame
            std_threshold: عدد الانحرافات المعيارية

        Returns:
            pd.DataFrame: بدون قيم شاذة
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
        logger.info(f"✅ إزالة {removed} قيمة شاذة")
        return df

    @staticmethod
    def validate_sensor_ranges(df: pd.DataFrame) -> pd.DataFrame:
        """
        التحقق من نطاقات الحساسات المعقولة
        """
        initial_len = len(df)

        for sensor, ranges in CUCUMBER_RANGES.items():
            if sensor not in df.columns:
                continue

            min_val, max_val = ranges["min"], ranges["max"]
            df = df[(df[sensor] >= min_val) & (df[sensor] <= max_val)]

        removed = initial_len - len(df)
        logger.info(f"✅ تم التحقق من نطاقات الحساسات (إزالة {removed} صف)")
        return df

    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
        """
        إزالة الصفوف المكررة
        """
        duplicates = df.duplicated().sum()
        df = df.drop_duplicates()
        logger.info(f"✅ إزالة {duplicates} صف مكرر")
        return df

    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """
        تنظيف شامل
        """
        logger.info("\n" + "="*60)
        logger.info("🧹 بدء تنظيف البيانات")
        logger.info("="*60)
        logger.info(f"البيانات الأصلية: {len(df):,} صف × {len(df.columns)} عمود\n")

        df = DataCleaner.remove_duplicates(df)
        df = DataCleaner.handle_missing_values(df)
        df = DataCleaner.remove_outliers(df)
        df = DataCleaner.validate_sensor_ranges(df)

        logger.info(f"\n✅ البيانات النظيفة: {len(df):,} صف × {len(df.columns)} عمود")
        logger.info("="*60 + "\n")

        return df


class DataPreprocessor:
    """
    معالجة إضافية للبيانات
    """

    @staticmethod
    def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        توحيد أسماء الأعمدة
        """
        df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_")
        return df

    @staticmethod
    def add_datetime_index(df: pd.DataFrame, datetime_col: Optional[str] = None) -> pd.DataFrame:
        """
        تحويل عمود التاريخ إلى index
        """
        if datetime_col is None:
            # البحث تلقائياً
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    datetime_col = col
                    break

        if datetime_col and datetime_col in df.columns:
            df[datetime_col] = pd.to_datetime(df[datetime_col])
            df = df.sort_values(by=datetime_col)
            df.set_index(datetime_col, inplace=True)
            logger.info(f"✅ تم تعيين datetime index من: {datetime_col}")

        return df

    @staticmethod
    def save_processed(df: pd.DataFrame, filename: str):
        """
        حفظ البيانات المعالجة
        """
        output_path = PROCESSED_DATA_DIR / f"{filename}.csv"
        df.to_csv(output_path)
        logger.info(f"💾 تم الحفظ: {output_path}")
        return output_path


def process_cucumber_data(input_csv: str, output_name: str = "cucumber_processed") -> pd.DataFrame:
    """
    معالجة كاملة للبيانات من البداية للنهاية

    Args:
        input_csv: مسار ملف CSV
        output_name: اسم الملف المخرج

    Returns:
        pd.DataFrame: البيانات المعالجة
    """
    logger.info(f"📥 تحميل: {input_csv}")
    df = pd.read_csv(input_csv)

    # معالجة أساسية
    df = DataPreprocessor.standardize_columns(df)
    df = DataPreprocessor.add_datetime_index(df)

    # التنظيف
    df = DataCleaner.clean(df)

    # الحفظ
    DataPreprocessor.save_processed(df, output_name)

    return df


if __name__ == "__main__":
    # مثال على الاستخدام
    import sys
    from data_loader import KaggleDataLoader

    csv_files = KaggleDataLoader.list_available_files()
    if csv_files:
        df = process_cucumber_data(str(csv_files[0]))
