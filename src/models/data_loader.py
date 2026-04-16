"""
Data Loader for Warif ML Pipeline
تحميل بيانات الخيار من Kaggle وتحضيرها
"""

import os
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحديد مجلد البيانات
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# إنشاء المجلدات إذا لم تكن موجودة
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


class KaggleDataLoader:
    """
    تحميل البيانات من Kaggle
    """

    @staticmethod
    def download_dataset(dataset_name: str, force_download: bool = False) -> bool:
        """
        تحميل dataset من Kaggle

        Args:
            dataset_name: اسم dataset (مثل: 'dataset/cucumber-growth-data')
            force_download: إذا كان True، حمّل حتى لو كان موجود

        Returns:
            bool: نجاح التحميل
        """
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()

            logger.info(f"📥 تحميل dataset: {dataset_name}")
            api.dataset_download_files(
                dataset_name,
                path=str(RAW_DATA_DIR),
                unzip=True
            )
            logger.info(f"✅ تم التحميل بنجاح إلى: {RAW_DATA_DIR}")
            return True

        except Exception as e:
            logger.error(f"❌ خطأ في التحميل: {e}")
            return False

    @staticmethod
    def list_available_files() -> list:
        """
        عرض ملفات CSV المتاحة
        """
        csv_files = list(RAW_DATA_DIR.glob("*.csv"))
        if not csv_files:
            logger.warning("⚠️ لا توجد ملفات CSV في data/raw/")
            return []

        logger.info("📋 الملفات المتاحة:")
        for f in csv_files:
            file_size = f.stat().st_size / 1024 / 1024  # MB
            logger.info(f"  ✓ {f.name} ({file_size:.2f} MB)")
        return csv_files

    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        """
        تحميل ملف CSV

        Args:
            file_path: مسار ملف CSV

        Returns:
            pd.DataFrame: البيانات
        """
        try:
            logger.info(f"📂 تحميل: {Path(file_path).name}")
            df = pd.read_csv(file_path)
            logger.info(f"✅ تم التحميل: {df.shape[0]:,} صف، {df.shape[1]} عمود")
            return df
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return None


class DataInfo:
    """
    عرض معلومات البيانات
    """

    @staticmethod
    def show_info(df: pd.DataFrame):
        """
        عرض معلومات مفصلة عن البيانات
        """
        if df is None or df.empty:
            logger.warning("⚠️ البيانات فارغة")
            return

        logger.info("\n" + "="*60)
        logger.info("📊 معلومات البيانات:")
        logger.info("="*60)

        logger.info(f"📈 عدد الصفوف: {len(df):,}")
        logger.info(f"📊 عدد الأعمدة: {len(df.columns)}")
        logger.info(f"💾 حجم الذاكرة: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        logger.info("\n📋 الأعمدة:")
        for i, col in enumerate(df.columns, 1):
            dtype = df[col].dtype
            missing = df[col].isnull().sum()
            missing_pct = (missing / len(df)) * 100
            logger.info(f"  {i}. {col:20} | {str(dtype):15} | Missing: {missing_pct:.2f}%")

        logger.info("\n📊 القيم الإحصائية:")
        logger.info(df.describe().to_string())

        logger.info("\n" + "="*60 + "\n")


def main():
    """
    مثال على الاستخدام
    """
    logger.info("🚀 Warif Data Loader")
    logger.info("="*60)

    # عرض الملفات المتاحة
    logger.info("\n1️⃣ الملفات المتاحة:")
    csv_files = KaggleDataLoader.list_available_files()

    if not csv_files:
        logger.info("""
        💡 لتحميل البيانات من Kaggle:
           python -m src.models.data_loader --download "dataset/cucumber-growth-data"

        أمثلة على Kaggle datasets:
           - dataset/cucumber-growth-data
           - dataset/greenhouse-climate-data
           - dataset/plant-yield-prediction
        """)
        return

    # اختيار أول ملف
    csv_file = csv_files[0]
    logger.info(f"\n2️⃣ تحميل ملف: {csv_file.name}")
    df = KaggleDataLoader.load_csv(str(csv_file))

    if df is not None:
        logger.info(f"\n3️⃣ عرض معلومات البيانات:")
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
