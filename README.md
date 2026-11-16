# Ryko-AI — منصة ونموذج ذكاء اصطناعي عربي

مشروع **Ryko-AI** يهدف إلى بناء:
1. **منصة خلفية (Backend Platform)** باستخدام FastAPI لخدمة الدردشة والبث والذاكرة.
2. **نموذج ذكاء اصطناعي عربي** متخصص في البرمجة والتواصل مع مسار تدريب LoRA وتصدير GGUF.

> هذا المستودع يحتوي على منصة MVP تعمل حالياً عبر **DeepSeek API** كبوابة استدلال أولية، مع بنية جاهزة للربط بالنموذج المحلي/المدرب لاحقاً.

---

## المزايا الحالية (Platform MVP)

- **FastAPI + AsyncIO** مع تهيئة الخدمات عبر `lifespan`
- نقاط وصول:
  - `POST /api/v1/chat` — دردشة مع ذاكرة سياقية
  - `POST /api/v1/stream` — بث حي عبر SSE
  - `GET /api/v1/models` — النماذج المتاحة
  - `GET /api/v1/health` — فحص الجاهزية
- **خدمة ذاكرة** (`services/memory.py`) باستخدام **ChromaDB** لحفظ واسترجاع السياق
- **خدمة ذكاء اصطناعي** (`services/ai_service.py`) تتصل بـ DeepSeek API (قابلة للتبديل لنموذج محلي)
- إعدادات آمنة عبر `.env` باستخدام `pydantic-settings`
- اختبارات `pytest` و CI عبر GitHub Actions

---

## هيكل المشروع

```text
.
├── app/
│   ├── main.py
│   ├── core/
│   │   └── config.py
│   ├── api/
│   │   └── v1/routes/chat.py
│   ├── schemas/
│   │   └── chat.py
│   └── services/
│       ├── ai_service.py
│       └── memory.py
├── training/
│   ├── prepare_data.py
│   ├── train_lora.py
│   └── quantize.py
├── tests/
│   ├── test_chat.py
│   ├── test_health.py
│   └── test_memory.py
├── .github/workflows/
│   ├── ci.yml
│   └── train.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## التشغيل السريع (محلي أو GitHub Codespaces)

### 1) تثبيت المتطلبات
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> في بيئات محدودة (مثل Termux) قد تتطلب حزم التدريب (`torch/transformers/peft`) إعداداً خاصاً. منصة الـ API نفسها تعمل بمتطلبات أخف.

### 2) إعداد المتغيرات البيئية
```bash
cp .env.example .env
# عدّل .env وأضف DEEPSEEK_API_KEY لتفعيل الردود الفعلية
```

### 3) تشغيل الخادم
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) تجربة نقاط الوصول
- الصحة: `GET http://localhost:8000/api/v1/health`
- النماذج: `GET http://localhost:8000/api/v1/models`
- دردشة:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"اشرح لي ما هو FastAPI","session_id":"demo"}'
```
- البث (SSE): `POST /api/v1/stream`

---

## الذاكرة السياقية (RAG / Vector Memory)

- التنفيذ الحالي يستخدم **ChromaDB PersistentClient** في المسار `DATABASE_URL` (افتراضي `./data/chroma`).
- عند تفعيل `use_memory=true`:
  - يتم حفظ رسالة المستخدم والرد
  - يتم استرجاع أقرب 3 سياقات مرتبطة بالاستعلام وحقنها في طلب النموذج

---

## مسار تدريب النموذج العربي

### 1) تحضير البيانات
يدعم السكربت تحميل مجموعات مثل CIDAR أو قراءة JSONL محلي وتحويلها لصيغة ChatML:
```bash
python training/prepare_data.py \
  --dataset arbml/CIDAR \
  --out data/processed/train_chatml.jsonl \
  --limit 20000 \
  --shuffle
```

### 2) التدريب بـ LoRA
```bash
python training/train_lora.py \
  --base-model Qwen/Qwen2.5-Coder-7B-Instruct \
  --data-path data/processed/train_chatml.jsonl \
  --output-dir outputs/ryko-ar-lora \
  --epochs 1
```
يدعم 4-bit (عند توفر البيئة) لتقليل استهلاك الذاكرة.

### 3) التصدير إلى GGUF
```bash
python training/quantize.py \
  --hf-model-dir outputs/ryko-ar-lora \
  --outfile outputs/ryko-ar-q4_k_m.gguf \
  --llama-cpp-dir ./llama.cpp \
  --quant-type Q4_K_M
```

### 4) الدمج مع المنصة
- بعد توفير نموذج محلي/خادم استدلال محلي، عيّن `LOCAL_MODEL_PATH` في `.env`
- نقطة الدمج الأساسية موجودة في `app/services/ai_service.py` (يمكن توجيه الاستدلال للمحلي بدل DeepSeek API)

---

## الاختبارات و CI

تشغيل الاختبارات محلياً:
```bash
PYTHONPATH=. pytest -q
```

GitHub Actions:
- `.github/workflows/ci.yml` يشغل اختبارات المنصة
- `.github/workflows/train.yml` يوفر تشغيلاً يدوياً (workflow_dispatch) لمسار إعداد البيانات والتدريب (smoke config)

---

## الأمان والملاحظات

- لا تضع مفاتيح سرية داخل الكود أو المستودع؛ استخدم `.env`
- `API_KEY` اختياري لحماية نقاط الوصول (Header: `X-API-Key`)
- `JWT_SECRET` مُجهز في الإعدادات للتوسعة المستقبلية نحو JWT كامل
- DeepSeek API مستخدم كمرحلة MVP لتشغيل المنصة فوراً قبل اكتمال التدريب/النشر المحلي للنموذج

---

## الحالة

- ✅ المرحلة 1: التأسيس (requirements, env example, هيكل)
- ✅ المرحلة 2: منصة MVP (FastAPI, chat/stream/health/models, memory, ai service)
- ✅ المرحلة 3: سكربتات التدريب (prepare/train_lora/quantize) + workflow تدريب
- ✅ المرحلة 4: اختبارات وتوثيق و CI

المشروع جاهز للتطوير التدريجي نحو استبدال مزود الاستدلال بالنموذج العربي المدرب محلياً.
