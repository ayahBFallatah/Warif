#!/usr/bin/env python3
"""
Hybrid System Tests
"""

import sys
from pathlib import Path

# Add project root to sys path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test Imports"""
    print("1: Testing imports...")
    try:
        from src.models import config
        from src.data import data_loader
        from src.data import data_processor
        from src.features import feature_engineering
        from src.train import train_models
        print("Imports successful\n")
        return True
    except ImportError as e:
        print(f"Error: {e}\n")
        return False


def test_directories():
    """Test Directories"""
    print("2: Testing directories...")
    from src.models.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR

    directories = [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR]
    all_exist = True

    for dir_path in directories:
        exists = dir_path.exists()
        status = "OK" if exists else "MISSING"
        print(f"  [{status}] {dir_path.name}: {dir_path}")
        if not exists:
            all_exist = False

    print()
    return all_exist


def test_classes():
    """Test Classes"""
    print("3: Testing classes...")
    try:
        from src.data.data_loader import KaggleDataLoader, DataInfo
        from src.data.data_processor import DataCleaner, DataPreprocessor
        # Assuming FeatureEngineer exists, or we just skip this test if we merged them
        print("Classes imported successfully\n")
        return True
    except Exception as e:
        print(f"Error: {e}\n")
        return False


def test_config():
    """Test config module"""
    print("4: Testing configuration...")
    try:
        from src.models.config import (
            CROP_TYPE,
            CUCUMBER_RANGES,
            FORECASTING_CONFIG,
            ANOMALY_CONFIG,
            YIELD_CONFIG,
            IRRIGATION_CONFIG
        )
        print(f"  Crop: {CROP_TYPE}")
        print(f"  Ranges loaded")
        print()
        return True
    except Exception as e:
        print(f"Error: {e}\n")
        return False


def main():
    """Main function"""
    print("\n" + "="*70)
    print("Hybrid System Tests")
    print("="*70 + "\n")

    tests = [
        test_imports,
        test_directories,
        test_classes,
        test_config,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Error: {e}\n")
            results.append(False)

    print("="*70)
    print("Testing Results:")
    print("="*70)

    passed = sum(results)
    total = len(results)

    print(f"\n  Passed: {passed}/{total}")
    print(f"  Failed: {total - passed}/{total}")

    if all(results):
        print("\nAll tests passed successfully!")
        return 0
    else:
        print("\nSome tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
