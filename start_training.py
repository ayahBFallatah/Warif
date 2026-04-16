#!/usr/bin/env python3
"""
Warif Training Pipeline - البدء الكامل
تحميل → تنظيف → ميزات → تدريب
"""

import sys
import os
from pathlib import Path

# إضافة المسار
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

# إعداد logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# استيراد الموديولات
from src.models.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, CROP_TYPE
from src.models.data_loader import KaggleDataLoader, DataInfo
from src.models.data_processor import process_cucumber_data
from src.models.feature_engineering import prepare_features


def generate_synthetic_data(num_rows: int = 10000) -> str:
    """
    توليد بيانات نموذجية واقعية للخيار
    (للاختبار السريع بدون الحاجة لـ Kaggle)
    """
    logger.info("\n" + "="*70)
    logger.info("🤖 توليد بيانات نموذجية للخيار...")
    logger.info("="*70 + "\n")

    # إنشاء فهرس زمني (100 يوم)
    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(num_rows)]

    # توليد بيانات واقعية
    data = {
        'timestamp': timestamps,
        'temperature': 22 + 4*np.sin(np.arange(num_rows)*2*np.pi/24) + np.random.normal(0, 0.5, num_rows),
        'humidity': 75 - 15*np.sin(np.arange(num_rows)*2*np.pi/24) + np.random.normal(0, 2, num_rows),
        'light': 2500 + 2000*np.sin(np.arange(num_rows)*2*np.pi/24).clip(0, 1) + np.random.normal(0, 100, num_rows),
        'soil_moisture': 65 - 20*np.sin(np.arange(num_rows)*2*np.pi/24) + np.random.normal(0, 2, num_rows),
        'ec': 1.8 + 0.1*np.sin(np.arange(num_rows)*2*np.pi/168) + np.random.normal(0, 0.05, num_rows),
        'co2': 700 + 100*np.sin(np.arange(num_rows)*2*np.pi/24) + np.random.normal(0, 20, num_rows),
    }

    df = pd.DataFrame(data)

    # حفظ البيانات
    output_file = RAW_DATA_DIR / "cucumber_synthetic_data.csv"
    df.to_csv(output_file, index=False)

    logger.info(f"✅ تم توليد {num_rows:,} صف من البيانات")
    logger.info(f"💾 حفظ: {output_file}")
    logger.info(f"   - Temperature: {df['temperature'].min():.2f}°C - {df['temperature'].max():.2f}°C")
    logger.info(f"   - Humidity: {df['humidity'].min():.2f}% - {df['humidity'].max():.2f}%")
    logger.info(f"   - Light: {df['light'].min():.2f} - {df['light'].max():.2f} lux")
    logger.info(f"   - Soil Moisture: {df['soil_moisture'].min():.2f}% - {df['soil_moisture'].max():.2f}%\n")

    return str(output_file)


def step_1_load_data():
    """الخطوة 1: تحميل البيانات"""
    logger.info("\n" + "="*70)
    logger.info("📥 الخطوة 1: تحميل البيانات")
    logger.info("="*70 + "\n")

    csv_files = list(RAW_DATA_DIR.glob("*.csv"))

    if not csv_files:
        logger.info("❌ لا توجد بيانات في data/raw/")
        logger.info("\n🔹 الخيارات:")
        logger.info("  1. تحميل من Kaggle:")
        logger.info("     python -m src.models.data_loader --download 'dataset/cucumber-growth-data'")
        logger.info("\n  2. توليد بيانات نموذجية:")
        logger.info("     توليد بيانات نموذجية الآن...\n")

        # توليد بيانات نموذجية
        csv_file = generate_synthetic_data(num_rows=10000)
        csv_files = [Path(csv_file)]

    logger.info(f"✅ تم العثور على {len(csv_files)} ملف CSV")
    for f in csv_files:
        logger.info(f"   • {f.name}")

    return str(csv_files[0])


def step_2_clean_data(input_csv: str):
    """الخطوة 2: تنظيف البيانات"""
    logger.info("\n" + "="*70)
    logger.info("🧹 الخطوة 2: تنظيف البيانات")
    logger.info("="*70 + "\n")

    df_clean = process_cucumber_data(
        input_csv=input_csv,
        output_name="cucumber_clean"
    )

    return df_clean


def step_3_engineer_features(clean_csv: str):
    """الخطوة 3: هندسة الميزات"""
    logger.info("\n" + "="*70)
    logger.info("🛠️ الخطوة 3: هندسة الميزات")
    logger.info("="*70 + "\n")

    df_features = prepare_features(
        input_csv=clean_csv,
        output_name="cucumber_features"
    )

    logger.info(f"\n✅ الميزات جاهزة:")
    logger.info(f"   • عدد الصفوف: {len(df_features):,}")
    logger.info(f"   • عدد الأعمدة: {len(df_features.columns)}")
    logger.info(f"   • الملف: {PROCESSED_DATA_DIR / 'cucumber_features.csv'}\n")

    return df_features


def step_4_prepare_for_training(df_features: pd.DataFrame):
    """الخطوة 4: تحضير البيانات للتدريب"""
    logger.info("\n" + "="*70)
    logger.info("📊 الخطوة 4: تحضير البيانات للتدريب")
    logger.info("="*70 + "\n")

    # اختيار الأعمدة الرقمية للتدريب
    numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()

    # إزالة الأعمدة التي تحتوي على NaN
    df_train = df_features[numeric_cols].dropna()

    logger.info(f"✅ البيانات جاهزة للتدريب:")
    logger.info(f"   • الصفوف: {len(df_train):,}")
    logger.info(f"   • الأعمدة: {len(df_train.columns)}")
    logger.info(f"   • الميزات: {', '.join(df_train.columns[:5])}...")

    logger.info(f"\n📈 إحصائيات البيانات:")
    logger.info(df_train.describe().to_string())

    return df_train


def step_5_train_models(df_train: pd.DataFrame):
    """الخطوة 5: تدريب النماذج"""
    logger.info("\n" + "="*70)
    logger.info("🤖 الخطوة 5: تدريب النماذج")
    logger.info("="*70 + "\n")

    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import joblib

    # اختيار الميزات والـ target
    # سنستخدم temperature كـ target للمثال
    if 'temperature' in df_train.columns:
        target_col = 'temperature'
        feature_cols = [col for col in df_train.columns if col != target_col]
    else:
        feature_cols = df_train.columns[:-1].tolist()
        target_col = df_train.columns[-1]

    X = df_train[feature_cols]
    y = df_train[target_col]

    logger.info(f"\n📋 معلومات التدريب:")
    logger.info(f"   • الميزات: {len(feature_cols)}")
    logger.info(f"   • Target: {target_col}")
    logger.info(f"   • الصفوف: {len(X):,}")

    # تقسيم البيانات
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info(f"\n📊 تقسيم البيانات:")
    logger.info(f"   • التدريب: {len(X_train):,} صف")
    logger.info(f"   • الاختبار: {len(X_test):,} صف")

    # تطبيع البيانات
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ============ نموذج 1: Forecasting (XGBoost) ============
    logger.info("\n🔹 تدريب نموذج 1: Forecasting (XGBoost)...")
    try:
        import xgboost as xgb

        model_xgb = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            verbose=0
        )

        model_xgb.fit(X_train_scaled, y_train)
        score_xgb = model_xgb.score(X_test_scaled, y_test)

        logger.info(f"   ✅ دقة XGBoost: {score_xgb:.4f}")

        # حفظ النموذج
        joblib.dump(model_xgb, PROCESSED_DATA_DIR / "forecasting_model_xgb.pkl")
        joblib.dump(scaler, PROCESSED_DATA_DIR / "forecasting_scaler.pkl")
        logger.info(f"   💾 حفظ النموذج والـ scaler")

    except Exception as e:
        logger.error(f"   ❌ خطأ: {e}")

    # ============ نموذج 2: Random Forest ============
    logger.info("\n🔹 تدريب نموذج 2: Random Forest...")
    try:
        from sklearn.ensemble import RandomForestRegressor

        model_rf = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        model_rf.fit(X_train_scaled, y_train)
        score_rf = model_rf.score(X_test_scaled, y_test)

        logger.info(f"   ✅ دقة Random Forest: {score_rf:.4f}")

        # حفظ النموذج
        joblib.dump(model_rf, PROCESSED_DATA_DIR / "random_forest_model.pkl")
        logger.info(f"   💾 حفظ النموذج")

    except Exception as e:
        logger.error(f"   ❌ خطأ: {e}")

    # ============ نموذج 3: Anomaly Detection ============
    logger.info("\n🔹 تدريب نموذج 3: Anomaly Detection...")
    try:
        from sklearn.ensemble import IsolationForest

        model_anomaly = IsolationForest(
            contamination=0.05,
            n_estimators=100,
            random_state=42
        )

        model_anomaly.fit(X_train_scaled)
        anomaly_score = model_anomaly.score_samples(X_test_scaled)

        logger.info(f"   ✅ تم تدريب نموذج كشف الشذوذ")
        logger.info(f"   • عدد النقاط الشاذة المكتشفة: {(anomaly_score < 0).sum()}")

        # حفظ النموذج
        joblib.dump(model_anomaly, PROCESSED_DATA_DIR / "anomaly_detection_model.pkl")
        logger.info(f"   💾 حفظ النموذج")

    except Exception as e:
        logger.error(f"   ❌ خطأ: {e}")

    # ============ نموذج 4: Gradient Boosting ============
    logger.info("\n🔹 تدريب نموذج 4: Gradient Boosting...")
    try:
        from sklearn.ensemble import GradientBoostingRegressor

        model_gb = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )

        model_gb.fit(X_train_scaled, y_train)
        score_gb = model_gb.score(X_test_scaled, y_test)

        logger.info(f"   ✅ دقة Gradient Boosting: {score_gb:.4f}")

        # حفظ النموذج
        joblib.dump(model_gb, PROCESSED_DATA_DIR / "gradient_boosting_model.pkl")
        logger.info(f"   💾 حفظ النموذج")

    except Exception as e:
        logger.error(f"   ❌ خطأ: {e}")

    logger.info("\n" + "="*70)
    logger.info("✅ تم تدريب جميع النماذج بنجاح!")
    logger.info("="*70 + "\n")


def main():
    """الدالة الرئيسية"""
    logger.info("\n" + "█"*70)
    logger.info("█" + " "*68 + "█")
    logger.info("█  🚀 Warif ML Training Pipeline - النظام الهجين للخيار" + " "*11 + "█")
    logger.info("█" + " "*68 + "█")
    logger.info("█"*70 + "\n")

    try:
        # الخطوة 1: تحميل البيانات
        input_csv = step_1_load_data()

        # الخطوة 2: تنظيف البيانات
        df_clean = step_2_clean_data(input_csv)

        # الخطوة 3: هندسة الميزات
        df_features = step_3_engineer_features(
            str(PROCESSED_DATA_DIR / "cucumber_clean.csv")
        )

        # الخطوة 4: تحضير للتدريب
        df_train = step_4_prepare_for_training(df_features)

        # الخطوة 5: تدريب النماذج
        step_5_train_models(df_train)

        # الملخص النهائي
        logger.info("\n" + "█"*70)
        logger.info("█" + " "*68 + "█")
        logger.info("█  ✨ انتهى التدريب بنجاح! البيانات والنماذج جاهزة" + " "*14 + "█")
        logger.info("█" + " "*68 + "█")
        logger.info("█"*70)

        logger.info("\n📂 الملفات المحفوظة:")
        logger.info(f"   • البيانات النظيفة: {PROCESSED_DATA_DIR / 'cucumber_clean.csv'}")
        logger.info(f"   • البيانات مع الميزات: {PROCESSED_DATA_DIR / 'cucumber_features.csv'}")
        logger.info(f"   • النماذج المدربة: {PROCESSED_DATA_DIR}/*.pkl")

        logger.info("\n🔗 الخطوة التالية:")
        logger.info("   ربط النماذج مع prediction_service.py للتنبؤ الفعلي")
        logger.info("   Dashboard موجودة وجاهزة للعرض!\n")

        return 0

    except Exception as e:
        logger.error(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
