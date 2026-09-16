# 🛡️ Rewind Bot — Telegram Chat Automation & Message Archiving System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-2CA5E0.svg)](https://aiogram.dev)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-orange.svg)](https://alembic.sqlalchemy.org/)
[![Telegram Stars](https://img.shields.io/badge/Stars-50%20%E2%AD%90-yellow.svg)](https://core.telegram.org/bots/payments-stars)

Professional Telegram Business / Connected Bot for tracking, archiving, and retrieving deleted/edited messages and media in private chats.

---

## 🌟 Imkoniyatlar (Key Features)

* **🌐 Ko‘p Tillilik (i18n):** O‘zbekcha (🇺🇿), Ruscha (🇷🇺) va Inglizcha (🇬🇧) tillarini to‘liq qo‘llab-quvvatlash. Avtomatik aniqlash va `/lang` orqali bir zumda o‘zgartirish.
* **✨ Zamonaviy Interfeys & Tipografiya:** Telegram HTML blockquote kartalari (`<blockquote>`), zamonaviy indikatorlar (`🟢`, `🔴`, `✦`), monospace teglari va chiroyli tugmalar.
* **🗑️ O‘chirilgan Xabarlarni Qaytarish:** Suhbatdosh xabarni o'chirgan zahoti bot uning asl matni yoki media faylini sizning shaxsiy bot chattingizga yuboradi.
* **📷 Media Arxivlash:** Rasmlar, videolar, ovozli xabarlar (*voice*), video xabarlar (*video note*), hujjatlar va audiolarni avtomatik yuklab oladi va xavfsiz saqlaydi.
* **✏️ Ko'p Bosqichli Tahrir Tarixi (Versioning):** Xabar necha marta tahrirlansa ham uning har bir versiyasi saqlanadi va eski/yangi taqqoslashi ko'rsatiladi.
* **🎁 72 Soatlik Bepul PRO Trial:** Bot Telegram Business-ga ulanganda darhol avtomatik faollashadi.
* **⭐ Telegram Stars Monetizatsiyasi:** 50 ⭐ / 30 kunlik to'liq avtomatlashtirilgan obuna.
* **🔒 Shaxsiy Xavfsizlik & GDPR:** Barcha ma'lumotlar foydalanuvchi hisobiga izolyatsiya qilingan. `/delete_my_data` orqali butun arxivni bir zumda tozalash mumkin.

---

## 🏗️ Arxitektura (System Architecture)

```
              TELEGRAM CLOUD
                    │
                    │ Business Connection Updates
                    ▼
           ┌─────────────────┐
           │ Telegram Bot API│
           └────────┬────────┘
                    │ HTTPS Webhook / Long Polling
                    ▼
           ┌─────────────────┐
           │     FastAPI     │
           │ Webhook Gateway │
           └────────┬────────┘
                    │
                    ▼
               ┌─────────┐
               │  Redis  │ (Deduplication, Queue, Distributed Locks)
               └────┬────┘
                    │
           ┌────────┴────────┐
           ▼                 ▼
    Message Worker      Media Worker
           │                 │
           ▼                 ▼
      PostgreSQL        S3 / Local Storage
           │
           ▼
   Notification Engine
           │
           ▼
      Telegram Bot ───► USER
```

---

## 🚀 O'rnatish va Ishga Tushirish (Quick Start)

### 1. Talablar
* Python 3.12+
* PostgreSQL 16+ (yoki lokal test uchun SQLite)
* Redis 7+

### 2. O'rnatish

```bash
# Virtual muhitni faollashtirish
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt

# Konfiguratsiyani sozlash
cp .env.example .env
```

### 3. `.env` faylini sozlang:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_SECRET=your-secure-webhook-token
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rewind_db
REDIS_URL=redis://localhost:6379/0
```

---

## 💻 CLI Boshqaruvi (`run.py`)

Loyiha barcha komponentlarni boshqarish uchun yagona CLI interfeysiga ega:

| Buyruq | Tavsif |
|---|---|
| `python run.py --mode polling` | Mahalliy dasturlash uchun Polling rejimida botni ishga tushirish |
| `python run.py --mode api` | Production FastAPI Webhook serverini ishga tushirish |
| `python run.py --mode worker` | Media fayllarni asinxron yuklab oluvchi worker |
| `python run.py --mode scheduler` | Obunalar va ma'lumotlarni tozalash cron scheduler |
| `python run.py --mode migrate` | Alembic ma'lumotlar bazasi migratsiyalarini bajarish |
| `python run.py --mode init-db` | Barcha SQL jadvallarini avtomatik yaratish |
| `python run.py --mode inspect-db` | Ma'lumotlar bazasi statistikasi va jadvallar holatini ko'rish |

---

## 🗄️ Ma'lumotlar Bazasi Migratsiyalari (Alembic)

```bash
# Yangi migratsiya yaratish
alembic revision --autogenerate -m "migration_name"

# Migratsiyalarni qo'llash
alembic upgrade head
```

---

## 🐳 Docker Compose orqali ishga tushirish

Barcha servislarni (FastAPI, PostgreSQL, Redis, Worker, Scheduler) bitta buyruq bilan ko'tarish:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

---

## 🧪 Testlarni Ishga Tushirish

```bash
pytest tests/ -v
```

---

## 📱 Telegram Business Botni Sozlash (@BotFather)

1. [@BotFather](https://t.me/BotFather) ga kiring va botingizni tanlang.
2. **Bot Settings** -> **Business Mode** -> **Turn On** qiling.
3. Telegram ilovangizda **Sozlamalar (Settings)** -> **Telegram Business** -> **Chat Automation** bo‘limiga kirib, botingizni ulang.
4. Ulanish bilan darhol 72 soatlik bepul PRO tarif ishga tushadi! 🎉

---

## 📄 Litsenziya

Ushbu loyiha [MIT Litsenziyasi](LICENSE) ostida tarqatiladi.
