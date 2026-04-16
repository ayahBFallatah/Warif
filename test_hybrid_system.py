#!/usr/bin/env python3
"""
اختبار النظام الهجين - التحقق من أن كل شيء يعمل بشكل صحيح
"""

import sys
from pathlib import Path

# إضافة المسار
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """اختبار: هل يمكن استيراد الموديولات؟"""
    print("🧪 اختبار 1: استيراد الموديولات...")
    try:
        from src.models import (
            config,
            data_loader,
            data_processor,
            feature_engineering
        )
        print("✅ جميع الموديولات تم استيراديتها بنجاح\n")
        return True
    except ImportError as e:
        print(f"❌ خطأ في الاستيراد: {e}\n")
        return False


def test_directories():
    """اختبار: هل المجلدات موجودة؟"""
    print("🧪 اختبار 2: التحقق من المجلدات...")
    from src.models.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR

    directories = [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR]
    all_exist = True

    for dir_path in directories:
        exists = dir_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_path.name}: {dir_path}")
        if not exists:
            all_exist = False

    print()
    return all_exist


def test_classes():
    """اختبار: هل الفئات يمكن تهيئتها؟"""
    print("🧪 اختبار 3: تهيئة الفئات...")
    try:
        from src.models.data_loader import KaggleDataLoader, DataInfo
        from src.models.data_processor import DataCleaner, DataPreprocessor
        from src.models.feature_engineering import FeatureEngineer, FeatureSelector

        loader = KaggleDataLoader()
        cleaner = DataCleaner()
        selector = FeatureSelector()

        print("✅ تم تهيئة جميع الفئات بنجاح\n")
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}\n")
        return False


def test_config():
    """اختبار: هل الإعدادات محملة بشكل صحيح؟"""
    print("🧪 اختبار 4: التحقق من الإعدادات...")
    try:
        from src.models.config import (
            CROP_TYPE,
            CUCUMBER_RANGES,
            FORECASTING_CONFIG,
            ANOMALY_CONFIG,
            YIELD_CONFIG,
            IRRIGATION_CONFIG
        )

        print(f"  ✅ نوع المحصول: {CROP_TYPE}")
        print(f"  ✅ نطاقات الخيار: {len(CUCUMBER_RANGES)} حساس")
        print(f"  ✅ إعدادات Forecasting محملة")
        print(f"  ✅ إعدادات Anomaly محملة")
        print(f"  ✅ إعدادات Yield محملة")
        print(f"  ✅ إعدادات Irrigation محملة")
        print()
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}\n")
        return False


def test_sample_data():
    """اختبار: هل يمكن معالجة بيانات نموذجية؟"""
    print("🧪 اختبار 5: معالجة بيانات نموذجية...")
    try:
        import pandas as pd
        import numpy as np
        from src.models.data_processor import DataCleaner

        # إنشاء بيانات نموذجية
        df = pd.DataFrame({
            'temperature': np.random.uniform(18, 28, 100),
            'humidity': np.random.uniform(60, 85, 100),
            'light': np.random.uniform(1000, 4000, 100),
            'soil_moisture': np.random.uniform(50, 75, 100),
        })

        cleaner = DataCleaner()
        df_clean = cleaner.clean(df)

        print(f"  ✅ البيانات الأصلية: {len(df)} صف")
        print(f"  ✅ البيانات النظيفة: {len(df_clean)} صف")
        print()
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}\n")
        return False


def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*70)
    print("🧪 اختبار النظام الهجين - Warif Hybrid ML System")
    print("="*70 + "\n")

    tests = [
        test_imports,
        test_directories,
        test_classes,
        test_config,
        test_sample_data,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}\n")
            results.append(False)

    # ملخص النتائج
    print("="*70)
    print("📊 ملخص الاختبارات:")
    print("="*70)

    passed = sum(results)
    total = len(results)

    print(f"\n  ✅ اختبارات نجحت: {passed}/{total}")
    print(f"  ❌ اختبارات فشلت: {total - passed}/{total}")

    if all(results):
        print("\n" + "🎉 "*10)
        print("🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام! 🎉")
        print("🎉 "*10 + "\n")
        print("الخطوة التالية:")
        print("  1. اقرأ: QUICK_START_HYBRID_SYSTEM.md")
        print("  2. ثبّت المكتبات: pip install -r requirements.txt")
        print("  3. أعد Kaggle API")
        print("  4. ابدأ تحميل البيانات!")
        return 0
    else:
        print("\n⚠️ بعض الاختبارات فشلت. تحقق من الأخطاء أعلاه.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
