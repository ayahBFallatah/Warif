# 📋 دليل التنفيذ - النظام الهجين للخيار

**المسؤول:** Ayah Badr Fallatah  
**التاريخ:** 2026-04-16  
**الحالة:** جاري التطوير

---

## 🎯 الملفات المضافة

```
src/models/
├── config.py              ✅ جديد: إعدادات مركزية
├── data_loader.py         ✅ جديد: تحميل من Kaggle
├── data_processor.py      ✅ جديد: تنظيف البيانات
├── feature_engineering.py ✅ جديد: استخلاص الميزات
│
├── train_models.py        ✅ موجود: تدريب النماذج
├── prediction_service.py  ✅ موجود: خدمة التنبؤ
├── forecasting_models.py  ✅ موجود: نماذج التنبؤ
└── anomaly_detection.py   ✅ موجود: كشف الشذوذ
```

---

## 🚀 خطوات التنفيذ

### الخطوة الأولى: التثبيت (5 دقائق)

```bash
# 1. انتقل للمجلد الرئيسي
cd c:\Users\AyahB\WarifBackend\Warif

# 2. ثبّت المكتبات الإضافية
pip install -r requirements.txt

# 3. تحقق من التثبيت
python -c "import kaggle; print('✅ Kaggle installed')"
```

---

### الخطوة الثانية: إعداد Kaggle API (3 دقائق)

```bash
# 1. اذهب إلى: https://kaggle.com/settings/account
# 2. اضغط: "Create New Token"
# 3. حمّل kaggle.json
# 4. انسخه إلى: C:\Users\AyahB\.kaggle\kaggle.json
# 5. تحقق:

kaggle datasets list -s cucumber
```

**المتوقع:**
```
ref                                      title                          size    lastUpdated  downloadCount
-----------------------------------------  ---------------------------  ------  ----------   --
dataset/cucumber-growth-data              Cucumber Growth Data          15 MB   2024-01-15   5432
dataset/greenhouse-climate-data           Greenhouse Climate Data       100 MB  2024-03-20   8234
```

---

### الخطوة الثالثة: تحميل البيانات (2 دقائق)

#### أ) من داخل Python:
```python
from src.models.data_loader import KaggleDataLoader

# تحميل dataset
loader = KaggleDataLoader()
loader.download_dataset("dataset/cucumber-growth-data")

# عرض الملفات المتاحة
files = loader.list_available_files()
```

#### ب) من سطر الأوامر:
```bash
python -m src.models.data_loader --download "dataset/cucumber-growth-data"
```

#### ج) عرض الملفات:
```bash
python -m src.models.data_loader --list
```

**المتوقع:**
```
✅ تم التحميل بنجاح إلى: data/raw/
📋 الملفات المتاحة:
  ✓ cucumber_growth_data.csv (25.5 MB)
  ✓ greenhouse_climate_data.csv (85.3 MB)
```

---

### الخطوة الرابعة: تنظيف البيانات (5 دقائق)

#### من داخل Python:
```python
from src.models.data_processor import process_cucumber_data

# معالجة شاملة
df_clean = process_cucumber_data(
    input_csv='data/raw/cucumber_growth_data.csv',
    output_name='cucumber_clean'
)

print(df_clean.head())
```

#### النتيجة المتوقعة:
```
🧹 بدء تنظيف البيانات
================================================== ==

البيانات الأصلية: 100,000 صف × 15 عمود

✅ إزالة 150 صف مكرر
✅ معالجة القيم الناقصة (المتبقي: 0)
✅ إزالة 89 قيمة شاذة
✅ تم التحقق من نطاقات الحساسات (إزالة 45 صف)

✅ البيانات النظيفة: 99,716 صف × 15 عمود

💾 تم الحفظ: data/processed/cucumber_clean.csv
```

---

### الخطوة الخامسة: هندسة الميزات (3 دقائق)

#### من داخل Python:
```python
from src.models.feature_engineering import prepare_features

# تحضير الميزات
df_features = prepare_features(
    input_csv='data/processed/cucumber_clean.csv',
    output_name='cucumber_features'
)

print(f"عدد الميزات: {df_features.shape[1]}")
print(f"عدد الصفوف: {df_features.shape[0]:,}")
```

#### النتيجة المتوقعة:
```
🛠️ بدء هندسة الميزات

⏰ إضافة الميزات الزمنية...
✅ تم إضافة الميزات الزمنية

🔄 إضافة ميزات متأخرة...
✅ تم إضافة ميزات متأخرة

📊 إضافة ميزات متحركة...
✅ تم إضافة ميزات متحركة

🔗 إضافة ميزات التفاعل...
✅ تم إضافة ميزات التفاعل

📊 الأعمدة الأصلية: 15
📊 الأعمدة الجديدة: 85
📊 الصفوف المتبقية: 99,500
📊 إجمالي الميزات المستخلصة: 70

💾 تم الحفظ: data/processed/cucumber_features.csv
```

---

### الخطوة السادسة: التدريب (قريباً)

بعد تحضير الميزات، سيتم التدريب على النماذج الأربعة:

```python
from src.models.train_models import ModelTrainer

trainer = ModelTrainer(
    data_path='data/processed/cucumber_features.csv'
)

# تدريب Forecasting Model
trainer.train_forecasting_model()

# تدريب Anomaly Detection
trainer.train_anomaly_detection()

# تدريب Yield Predictor
trainer.train_yield_predictor()

# تدريب Irrigation Optimizer
trainer.train_irrigation_optimizer()

# حفظ جميع النماذج
trainer.save_all_models()
```

---

## 📊 ملخص البيانات المتوقعة

| المرحلة | الحالة | الملف | الصفوف | الأعمدة |
|--------|--------|-------|--------|--------|
| 1. خام | ✅ | `data/raw/*.csv` | 100K+ | 15-20 |
| 2. نظيف | ✅ | `data/processed/cucumber_clean.csv` | 99K+ | 15-20 |
| 3. ميزات | ✅ | `data/processed/cucumber_features.csv` | 99K+ | 80-90 |
| 4. تدريب | ⏳ | `data/models/*.pkl` | - | - |

---

## 🔧 حل المشاكل الشائعة

### المشكلة: "No module named 'kaggle'"
```bash
pip install kaggle
```

### المشكلة: "Authentication failed"
```bash
# تأكد من وجود الملف:
# C:\Users\AyahB\.kaggle\kaggle.json

# تحقق من الصلاحيات (Windows):
icacls C:\Users\AyahB\.kaggle\kaggle.json /grant:r "%USERNAME%":F
```

### المشكلة: "No CSV files found"
```bash
# تأكد من وجود البيانات في:
# c:\Users\AyahB\WarifBackend\Warif\data\raw\

# أو حمّل يدوياً من:
# https://kaggle.com/datasets
```

### المشكلة: Memory Error
```python
# قراءة الملفات الكبيرة بأجزاء:
for chunk in pd.read_csv('file.csv', chunksize=10000):
    # معالجة كل chunk
    pass
```

---

## ✅ قائمة التحقق

```
□ تثبيت المكتبات (requirements.txt)
□ إعداد Kaggle API
□ تحميل البيانات من Kaggle
□ تنظيف البيانات (cucumber_clean.csv)
□ هندسة الميزات (cucumber_features.csv)
□ التدريب على النماذج
□ حفظ النماذج
□ اختبار على بيانات جديدة
```

---

## 📞 الخطوة التالية

بعد اكتمال الخطوات الخمس الأولى:
1. ✅ تحميل البيانات
2. ✅ تنظيف البيانات
3. ✅ هندسة الميزات
4. ⏳ **التدريب** (Forecasting, Anomaly, Yield, Irrigation)
5. ⏳ التقييم والتحسين

---

**تم الإعداد بواسطة:** Claude Code  
**التاريخ:** 2026-04-16
