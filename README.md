# Ryko-AI

**منصة ذكاء اصطناعي عربية متكاملة للبرمجة والتواصل — FastAPI Platform + Arabic AI Model Pipeline**

[![CI Status](https://img.shields.io/github/actions/workflow/status/tibatechapp-ship-it/ryko-ai/ci.yml?branch=main&label=CI&logo=github)](https://github.com/tibatechapp-ship-it/ryko-ai/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-MVP%20Ready-success)](https://github.com/tibatechapp-ship-it/ryko-ai)

---

## نظرة عامة (Overview)

**Ryko-AI** هي منصة FastAPI متطورة، مخصصة للبرمجة والتواصل باللغة العربية، مع دعم كامل للذاكرة السياقية (RAG). يجمع المشروع بين طبقة Backend عالية الأداء (AsyncIO + SSE) ومسار تدريب مخصص لنموذج عربي متخصص في مهام البرمجة (Code Generation, Explanation, Completion, Debugging)، مع قابلية التبديل السلس بين مزودي الاستدلال السحابي والنماذج المحلية.

تم إنجاز المشروع عبر 4 مراحل متكاملة:
- **المرحلة 1 — التأسيس (Bootstrap):** هيكلة المستودع، المتطلبات، ومتغيرات البيئة.
- **المرحلة 2 — منصة MVP (Platform):** واجهات الدردشة والبث والذاكرة والخدمات الأساسية.
- **المرحلة 3 — مسار النموذج (Model Training):** تجهيز البيانات، تدريب LoRA، وتصدير GGUF.
- **المرحلة 4 — الدمج والجودة (Integration & QA):** اختبارات `pytest`، توثيق، و CI/CD عبر GitHub Actions.

---

## ✨ الميزات الرئيسية (Key Features)

- **محرك API فائق السرعة (FastAPI + AsyncIO):** نقاط وصول معيارية (`/chat`, `/stream`, `/models`, `/health`) مع أداء غير متزامن.
- **بث مباشر (Server-Sent Events - SSE):** تجربة محادثة لحظية عبر `POST /api/v1/stream`.
- **ذاكرة سياقية متقدمة (RAG):** خدمة ذاكرة مبنية على **ChromaDB** لحفظ واسترجاع سياق المحادثات وحقنه في الطلبات.
- **بنية مرنة لمزود النموذج:** تكامل MVP مع **DeepSeek API**، مع نقطة دمج جاهزة للتبديل إلى النموذج المحلي/المدرب (`LOCAL_MODEL_PATH`).
- **مسار تدريب مدمج للنموذج العربي:** سكربتات لمعالجة البيانات، التدريب بتقنية **LoRA** (مع دعم 4-bit)، والتصدير لصيغة **GGUF** للتشغيل على موارد محدودة.
- **أمان وإعدادات قابلة للتهيئة:** تحميل الأسرار والإعدادات عبر `.env` باستخدام `pydantic-settings` مع دعم حماية API Key.
- **جودة مستمرة (CI/CD):** اختبارات تلقائية وتشغيل مسار التدريب عبر GitHub Actions.

---

## 🏗️ البنية المعمارية (Architecture)

```text
┌──────────────┐
│    Client    │  (Web / Mobile / CLI)
└──────┬───────┘
       │  HTTP / SSE
       ▼
┌──────────────────────────────────────────────────────┐
│               FastAPI API Router (v1)                │
│  /chat | /stream | /models | /health | /agent/*      │
└──────┬───────────────────────────────────┬───────────┘
       │                                   │
       ▼                                   ▼
┌──────────────────────┐        ┌──────────────────────────┐
│      AI Service      │◄──────►│   Model Provider Layer   │
│  (app/services/      │        │  - DeepSeek API (MVP)    │
│   ai_service.py)     │        │  - Local / GGUF Model    │
└──────┬───────────────┘        └──────────────────────────┘
       │
       │ retrieve/store context (RAG)
       ▼
┌──────────────────────┐
│    Memory Service    │
│ (ChromaDB Vector DB) │
└──────────────────────┘

┌──────────────────────────────────────────────────────┐
│            نظام الوكلاء (Agentic Layer)               │
│  Orchestrator → Planner → Coder → Reviewer           │
│  + Context من MemoryService (Shared Context)         │
└──────────────────────────────────────────────────────┘
```

**مكونات أساسية:**
- `app/main.py`: تهيئة FastAPI ودورة حياة الخدمات (`lifespan`)
- `app/api/v1/routes/chat.py`: مسارات الدردشة، البث، النماذج، والصحة
- `app/api/v1/routes/agents.py`: مسارات نظام الوكلاء (`/agent/execute`, `/agent/stream`)
- `app/services/ai_service.py`: طبقة الاستدلال وتوحيد مزودي النماذج
- `app/services/memory.py`: تخزين واسترجاع السياق عبر ChromaDB
- `app/agents/`: طبقة الوكلاء (`base`, `planner`, `coder`, `reviewer`, `orchestrator`, `tools`)

---

## 🚀 التشغيل السريع (Quick Start)

> مناسب للتشغيل المحلي أو عبر **GitHub Codespaces**.

### 1) استنساخ المستودع وتثبيت المتطلبات
```bash
git clone https://github.com/tibatechapp-ship-it/ryko-ai.git
cd ryko-ai

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2) إعداد متغيرات البيئة
```bash
cp .env.example .env
# حدّث القيم المطلوبة داخل .env
```

أهم المتغيرات:
- `DEEPSEEK_API_KEY`: لتفعيل مزود الاستدلال الافتراضي (MVP)
- `API_KEY`: (اختياري) لحماية نقاط الوصول عبر Header `X-API-Key`
- `DATABASE_URL`: مسار تخزين ChromaDB (افتراضي: `./data/chroma`)
- `LOCAL_MODEL_PATH`: مسار النموذج المحلي/المدرب (للتكامل المستقبلي)

### 3) تشغيل الخادم
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) تجربة واجهات API
- **Health:** `GET http://localhost:8000/api/v1/health`
- **Models:** `GET http://localhost:8000/api/v1/models`
- **Chat:** `POST http://localhost:8000/api/v1/chat`
- **Stream (SSE):** `POST http://localhost:8000/api/v1/stream`
- **تنفيذ الوكلاء:** `POST http://localhost:8000/api/v1/agent/execute`
- **بث خطوات الوكلاء (SSE):** `POST http://localhost:8000/api/v1/agent/stream`

### استخدام نظام الوكلاء (Multi-Agent)

مثال: تنفيذ مهمة معقدة عبر المنسق (تخطيط → برمجة → مراجعة):

```bash
curl -X POST http://localhost:8000/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY_IF_ENABLED>" \
  -d '{
    "task": "أنشئ endpoint جديد في FastAPI لإرجاع قائمة منتجات وهمية مع اختبار pytest",
    "session_id": "agents-demo"
  }'
```

الاستجابة تتضمن: `plan`, `code_output`, `review_output`, `final_output`, و`steps`.

لبث الخطوات الحية (SSE):

```bash
curl -N -X POST http://localhost:8000/api/v1/agent/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY_IF_ENABLED>" \
  -d '{"task":"حسّن رسالة الخطأ في chat.py","session_id":"agents-demo"}'
```

الأحداث المتوقعة: `step`, `step_done`, `plan`, `code`, `review`, `final`, `done`.

مثال طلب دردشة:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY_IF_ENABLED>" \
  -d '{
    "message": "اشرح لي ما هو FastAPI باختصار",
    "session_id": "demo-session",
    "use_memory": true
  }'
```

---

## 🧠 مسار التدريب (Training Pipeline)

يوفر المشروع مسار تدريب متكامل للنموذج العربي داخل مجلد `training/`:

| المرحلة | السكربت | الوظيفة |
|---|---|---|
| Data Preparation | `training/prepare_data.py` | تنظيف وتجهيز البيانات (مثل CIDAR / Arabic-Coding-ChatML) وتحويلها لصيغة ChatML (JSONL) |
| Fine-Tuning (LoRA) | `training/train_lora.py` | تدريب نموذج أساسي (مثل Qwen2.5-Coder / Gemma) باستخدام **LoRA** مع دعم **4-bit** لتقليل استهلاك الذاكرة |
| Quantization & Export | `training/quantize.py` | تحويل النموذج إلى صيغة **GGUF** للتشغيل عبر `llama.cpp` على موارد محدودة |

### أوامر تشغيل نموذجية
```bash
# 1) تجهيز البيانات
python training/prepare_data.py \
  --dataset arbml/CIDAR \
  --out data/processed/train_chatml.jsonl \
  --limit 20000 \
  --shuffle

# 2) تدريب LoRA
python training/train_lora.py \
  --base-model Qwen/Qwen2.5-Coder-7B-Instruct \
  --data-path data/processed/train_chatml.jsonl \
  --output-dir outputs/ryko-ar-lora \
  --epochs 1

# 3) التصدير إلى GGUF
python training/quantize.py \
  --hf-model-dir outputs/ryko-ar-lora \
  --outfile outputs/ryko-ar-q4_k_m.gguf \
  --llama-cpp-dir ./llama.cpp \
  --quant-type Q4_K_M
```

**GitHub Actions (Training Workflow):**  
يتوفر Workflow يدوي للتدريب التجريبي عبر `.github/workflows/train.yml` (`workflow_dispatch`) لتشغيل خطوات تجهيز البيانات والتدريب ورفع الـ artifacts.

---

## 🛡️ الأمان والاختبارات (Security & CI/CD)

### الأمان (Security)
- **إدارة الأسرار:** جميع المفاتيح والإعدادات الحساسة تُدار عبر `.env` (ولا تُخزن في الكود).
- **حماية نقاط الوصول:** دعم `API_KEY` عبر Header `X-API-Key` لمسارات API المحمية.
- **جاهزية JWT:** تهيئة `JWT_SECRET` ضمن الإعدادات لدعم مصادقة JWT في المراحل القادمة.
- **عزل الإعدادات:** استخدام `pydantic-settings` لتحميل وتهيئة الإعدادات بشكل آمن ومنتظم.

### الاختبارات والجودة (Testing & CI)
- **اختبارات آلية (`pytest`)** تغطي: الصحة، النماذج، الدردشة، وسلوك خدمة الذاكرة.
- **CI عبر GitHub Actions:** تشغيل الاختبارات تلقائياً عند `push` و `pull_request` من خلال `.github/workflows/ci.yml`.
- **Training Automation:** تشغيل يدوي لمسار التدريب التجريبي عبر `.github/workflows/train.yml`.

تشغيل الاختبارات محلياً:
```bash
PYTHONPATH=. pytest -q
```

---

## 🗺️ خارطة الطريق (Roadmap)

- [x] **Phase 1:** التأسيس وهيكلة المشروع
- [x] **Phase 2:** منصة MVP (FastAPI + Chat/Stream + Memory + DeepSeek Integration)
- [x] **Phase 3:** مسار التدريب (Prepare Data + LoRA + GGUF Export + Training Workflow)
- [x] **Phase 4:** الاختبارات، التوثيق، و CI/CD
- [ ] **Next:** استبدال مزود الاستدلال السحابي بالنموذج العربي المحلي (**Local Inference**) بعد اكتمال التدريب والتقييم
- [ ] تحسينات لاحقة: مصادقة JWT كاملة، تقييم جودة النموذج (Benchmarking)، وتحسينات الأداء والتوسع (Scaling/Observability)

---

## الترخيص (License)

هذا المشروع مرخص تحت رخصة **Apache-2.0**. راجع ملف [LICENSE](LICENSE) للمزيد من التفاصيل.
