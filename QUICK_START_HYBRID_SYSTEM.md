# 🚀 البدء السريع - النظام الهجين للخيار

**الوقت المتوقع:** 20 دقيقة

---

## 📋 الخطوات الأساسية

### 1️⃣ التثبيت (5 دقائق)

```bash
cd c:\Users\AyahB\WarifBackend\Warif
pip install -r requirements.txt
```

---

### 2️⃣ إعداد Kaggle (3 دقائق)

1. اذهب إلى: https://kaggle.com/settings/account
2. اضغط "Create New Token"
3. انسخ `kaggle.json` إلى: `C:\Users\AyahB\.kaggle\kaggle.json`

**التحقق:**
```bash
kaggle datasets list -s cucumber
```

---

### 3️⃣ تحميل البيانات (2 دقيقة)

**الطريقة الأسهل - سطر أوامر واحد:**

```bash
python -c "
from src.models.data_loader import KaggleDataLoader
loader = KaggleDataLoader()
loader.download_dataset('dataset/cucumber-growth-data')
loader.list_available_files()
"
```

**أو من Python:**
```python
from src.models.data_loader import KaggleDataLoader

loader = KaggleDataLoader()
loader.download_dataset("dataset/cucumber-growth-data")
```

---

### 4️⃣ تنظيف البيانات (3 دقائق)

```python
from src.models.data_processor import process_cucumber_data

df_clean = process_cucumber_data(
    input_csv='data/raw/cucumber_growth_data.csv'
)
```

**النتيجة:**
```
✅ البيانات النظيفة: 99,716 صف
💾 حفظ: data/processed/cucumber_clean.csv
```

---

### 5️⃣ هندسة الميزات (3 دقائق)

```python
from src.models.feature_engineering import prepare_features

df_features = prepare_features(
    input_csv='data/processed/cucumber_clean.csv'
)
```

**النتيجة:**
```
✅ الميزات: 85 عمود
✅ الصفوف: 99,500
💾 حفظ: data/processed/cucumber_features.csv
```

---

### 6️⃣ التدريب (قريباً)

```python
from src.models.train_models import ModelTrainer

trainer = ModelTrainer(
    data_path='data/processed/cucumber_features.csv'
)
trainer.train_all_models()
```

---

## ✨ ملخص سريع

| الخطوة | الوقت | الملف المخرج |
|--------|--------|------------|
| 1. التثبيت | 5 دقائق | - |
| 2. Kaggle | 3 دقائق | - |
| 3. التحميل | 2 دقيقة | `data/raw/*.csv` |
| 4. التنظيف | 3 دقائق | `data/processed/cucumber_clean.csv` |
| 5. الميزات | 3 دقائق | `data/processed/cucumber_features.csv` |
| **الإجمالي** | **16 دقيقة** | - |

---

## 🎯 البيانات جاهزة للتدريب!

بعد 20 دقيقة، لديك:
- ✅ بيانات نظيفة
- ✅ ميزات مستخلصة
- ✅ جاهز لتدريب النماذج

---

## 📞 للمزيد من المعلومات

اقرأ: `src/models/IMPLEMENTATION_GUIDE.md`

---

**ملاحظة:** جميع الملفات منظمة احترافياً وجاهزة للعمل!
