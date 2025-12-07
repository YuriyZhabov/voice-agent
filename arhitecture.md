# Voice Agent Platform - Полная Архитектура (v2.0)
## Enterprise-Ready Design вдохновленный VAPI & RetellAI

---

## 📋 ОГЛАВЛЕНИЕ
1. [Обзор системы](#обзор-системы)
2. [Архитектурные слои](#архитектурные-слои)
3. [Ключевые компоненты](#ключевые-компоненты)
4. [Детальные диаграммы](#детальные-диаграммы)
5. [Примеры кода](#примеры-кода)
6. [Развертывание](#развертывание)
7. [Мониторинг и наблюдаемость](#мониторинг-и-наблюдаемость)
8. [Дорожная карта](#дорожная-карта)

---

## 🎯 ОБЗОР СИСТЕМЫ

### Что мы строим?

**Voice Agent Platform** — это enterprise-grade решение для создания и управления AI-powered голосовыми агентами, которые:

- 🤖 **Ведут естественные разговоры** через телефон или SIP-канал
- 🧠 **Используют LLM** (OpenAI, Claude, Gemini) для интеллектуальных ответов
- 🔧 **Интегрируются с внешними системами** (CRM, базы данных, API) через инструменты
- 💰 **Монетизируются** через минуточную биллинговую систему
- 📊 **Аналитика в реальном времени** с расшифровками и записями
- 🚀 **Масштабируются** от одного агента до тысяч параллельных звонков

### Архитектурные принципы

```
┌─────────────────────────────────────────────────────────────┐
│ 1. EVENT-DRIVEN ARCHITECTURE                                │
│    Асинхронная коммуникация между сервисами через Kafka     │
│    - Развязка сервисов (loosely coupled)                    │
│    - Масштабируемость без синхронных блокировок             │
│    - Replay-able audit trail                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 2. REAL-TIME STREAMING PIPELINE                             │
│    Параллельная обработка: ASR → NLP → LLM → TTS            │
│    - Начинаем TTS пока пользователь ещё говорит            │
│    - Streaming tokens из LLM прямо в TTS                    │
│    - Целевая латентность: <300ms end-to-end                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 3. MULTI-TENANT FIRST                                       │
│    Изоляция данных организаций на всех слоях                │
│    - Безопасность на уровне базы данных (RLS)              │
│    - Финансовая изоляция платежей                           │
│    - Шифрование данных звонков                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 4. GRACEFUL DEGRADATION                                     │
│    Система работает даже при отказе компонентов             │
│    - Fallback для LLM моделей                               │
│    - Local TTS backup если облачный недоступен             │
│    - Circuit breaker для внешних сервисов                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ АРХИТЕКТУРНЫЕ СЛОИ

### Слой 1: PRESENTATION LAYER (Next.js 15 + React 19)

**Назначение**: Веб-интерфейс для управления агентами, мониторинга звонков, биллинга

```
┌────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Dashboard   │  │ Call Monitor  │  │  Billing    │         │
│  │  Real-time   │  │  (LiveKit Web)│  │ Dashboard   │         │
│  │  updates     │  │  - Wave forms │  │ (YooKassa)  │         │
│  │  (WebSocket) │  │  - Transcript │  │             │         │
│  │  SID tokens  │  │  - Recording  │  │             │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Agent       │  │  Prompt       │  │  Settings   │         │
│  │  Builder     │  │  Editor       │  │  Multi-org  │         │
│  │  - UI        │  │  - Syntax     │  │  API Keys   │         │
│  │  - LLM Model │  │  - Testing    │  │  Webhooks   │         │
│  │  - Tools     │  │  - Versioning │  │             │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │            SHARED AUTHENTICATION LAYER              │     │
│  │  BetterAuth + NextAuth.js + JWT tokens              │     │
│  │  - OAuth 2.0 (Google, GitHub)                       │     │
│  │  - Email/password с подтверждением                 │     │
│  │  - Session tokens (30 дней)                         │     │
│  │  - API key + secret для интеграций                 │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Ключевые компоненты**:

- **Real-time Dashboard**: WebSocket соединение для обновлений статуса звонков
- **Agent Builder**: Drag-and-drop конструктор с превью
- **Call Monitor**: Live waveforms, текущие разговоры, бревиары
- **Billing Console**: История платежей, использование минут, инвойсы

### Слой 2: API GATEWAY & ROUTING

**Назначение**: Entry point для всех запросов, аутентификация, rate limiting, логирование

```
┌────────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                           │
│              (Express.js / FastAPI middleware)                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  REQUEST PIPELINE                                       │  │
│  │  1. TLS Termination (HTTPS only)                        │  │
│  │  2. CORS validation (whitelist origins)                 │  │
│  │  3. Authentication (JWT token verify)                  │  │
│  │  4. Authorization (RBAC - Role Based Access Control)    │  │
│  │  5. Rate limiting (200 req/min per user)                │  │
│  │  6. Request logging (Structured JSON logs)              │  │
│  │  7. Router -> Service                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  /auth/*     │  │ /agents/*    │  │  /calls/*    │         │
│  │  BetterAuth  │  │ Agent CRUD   │  │ Call events  │         │
│  │  endpoints   │  │ + Config     │  │ + History    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  /billing/*  │  │ /livekit/*   │  │  /tools/*    │         │
│  │  YooKassa    │  │ Token gen    │  │  MCP Proxy   │         │
│  │  webhooks    │  │ + Stats      │  │  + Store     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  SECURITY LAYER                                         │ │
│  │  - PII scrubbing на логах                              │ │
│  │  - CORS headers                                        │ │
│  │  - X-API-Key validation                                │ │
│  │  - DDoS protection (fail2ban)                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Слой 3: BUSINESS LOGIC SERVICES (Микросервисная архитектура)

**Назначение**: Основная бизнес-логика системы

```
┌────────────────────────────────────────────────────────────────┐
│           BUSINESS LOGIC SERVICES LAYER                        │
│              (Node.js + Python microservices)                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ SERVICE 1: CALL MANAGEMENT SERVICE (Node.js)           │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Задачи:                                                │  │
│  │ - Прием входящих/исходящих SIP вызовов                │  │
│  │ - Управление состоянием звонка (init→active→ended)   │  │
│  │ - Переправка аудио в Agent Service                    │  │
│  │ - Детектирование молчания (VAD)                       │  │
│  │ - Interrupt handling (пользователь кричит)            │  │
│  │ - Запись и сохранение аудио в S3                      │  │
│  │                                                        │  │
│  │ Публикует события в Kafka:                            │  │
│  │ ✓ call.initiated (с номерами телефонов)              │  │
│  │ ✓ call.agent_assigned (agentId)                       │  │
│  │ ✓ call.user_spoke (speaker: user, duration)          │  │
│  │ ✓ call.agent_responded (text, duration)              │  │
│  │ ✓ call.ended (duration, recording_url)               │  │
│  │ ✓ call.interrupted (timestamp)                        │  │
│  │                                                        │  │
│  │ Технологии:                                           │  │
│  │ - LiveKit SDK (управление пирами)                    │  │
│  │ - pjsua2 (SIP стек для MTS Exolve)                   │  │
│  │ - Web Audio API (VAD локально)                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ SERVICE 2: AGENT ORCHESTRATION ENGINE (Python)         │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Задачи:                                                │  │
│  │ - Обработка входящего аудио (streaming ASR)            │  │
│  │ - Управление состоянием разговора (context window)     │  │
│  │ - Вызов LLM с системным промптом                       │  │
│  │ - Потоковая обработка токенов                          │  │
│  │ - Динамический выбор инструментов (tool calling)       │  │
│  │ - Sentiment анализ в реальном времени                  │  │
│  │ - Interrupt handling (прерывание генерации)            │  │
│  │                                                        │  │
│  │ Подсистемы:                                           │  │
│  │ ┌─────────────────────────────────────────────────┐   │  │
│  │ │ Intent Classification (RAG over context)         │   │  │
│  │ │ - Определяет тип запроса юзера                 │   │  │
│  │ │ - Направляет на нужный workflow                │   │  │
│  │ └─────────────────────────────────────────────────┘   │  │
│  │ ┌─────────────────────────────────────────────────┐   │  │
│  │ │ Context Manager (Hierarchical Memory)            │   │  │
│  │ │ - Call-level: текущий разговор (краткий контекст) │   │  │
│  │ │ - Session-level: история разговора (longer)     │   │  │
│  │ │ - User-level: профиль юзера (долгосроч)        │   │  │
│  │ │ - Семантический поиск: similarity search        │   │  │
│  │ └─────────────────────────────────────────────────┘   │  │
│  │ ┌─────────────────────────────────────────────────┐   │  │
│  │ │ Multi-Model LLM Routing                          │   │  │
│  │ │ - Primary: OpenAI GPT-4o-mini                   │   │  │
│  │ │ - Secondary: Claude 3.5 Sonnet (fallback)       │   │  │
│  │ │ - Tertiary: open-source Llama (на edge)        │   │  │
│  │ │ - Cost optimization: выбор по токенам/скорости  │   │  │
│  │ └─────────────────────────────────────────────────┘   │  │
│  │                                                        │  │
│  │ Подписывается на события из Kafka:                   │  │
│  │ ← call.initiated (начинает прослушивание)             │  │
│  │ ← call.user_spoke (новое сообщение)                   │  │
│  │ ← call.interrupted (прерывает генерацию)              │  │
│  │ ← tool.completed (результат инструмента)              │  │
│  │                                                        │  │
│  │ Публикует события:                                    │  │
│  │ ✓ agent.processing (status: thinking)                │  │
│  │ ✓ agent.calling_tool (tool_name, params)             │  │
│  │ ✓ agent.response_ready (text, audio_url)             │  │
│  │ ✓ agent.sentiment (positive/neutral/negative)         │  │
│  │ ✓ agent.escalation_triggered (reason)                │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ SERVICE 3: TOOL EXECUTOR (Python + MCP Protocol)       │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Задачи:                                                │  │
│  │ - Парсинг tool_call из LLM (JSON)                     │  │
│  │ - Валидация параметров (schema validation)             │  │
│  │ - Выполнение инструментов в параллель (до 5)           │  │
│  │ - Обработка ошибок (timeout, validation error)         │  │
│  │ - Форматирование результатов для LLM                   │  │
│  │                                                        │  │
│  │ Типы инструментов:                                    │  │
│  │ 1. HTTP API calls (e.g. CRM lookup)                   │  │
│  │ 2. Database queries (e.g. customer info)              │  │
│  │ 3. n8n workflows (e.g. email send)                    │  │
│  │ 4. External services (calendar, Slack)                │  │
│  │ 5. Custom Python functions                            │  │
│  │                                                        │  │
│  │ Пример: customer_lookup({phone: "+71234567890"})      │  │
│  │ → Запрашивает CRM API → Возвращает JSON результат    │  │
│  │                                                        │  │
│  │ Публикует события:                                    │  │
│  │ ✓ tool.started (tool_name)                            │  │
│  │ ✓ tool.completed (result)                             │  │
│  │ ✓ tool.failed (error, retry_count)                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ SERVICE 4: BILLING SERVICE (Node.js)                   │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Задачи:                                                │  │
│  │ - Трекинг использования (минуты звонков)               │  │
│  │ - Начисление платежей (в реальном времени)             │  │
│  │ - Интеграция с YooKassa (платежи)                      │  │
│  │ - Управление подписками (тарифные планы)               │  │
│  │ - Контроль кредитов (stop если баланс <0)              │  │
│  │                                                        │  │
│  │ Отслеживает события:                                  │  │
│  │ ← call.ended (длительность)                            │  │
│  │ ← payment.webhook (подтверждение от YooKassa)          │  │
│  │                                                        │  │
│  │ Публикует события:                                    │  │
│  │ ✓ billing.minutes_deducted (amount)                   │  │
│  │ ✓ billing.balance_low (threshold: 10 min)             │  │
│  │ ✓ billing.payment_received (amount)                   │  │
│  │ ✓ billing.call_rejected (reason: no_balance)          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ SERVICE 5: ANALYTICS SERVICE (Python)                  │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Задачи:                                                │  │
│  │ - Агрегация метрик (volume, duration, sentiment)        │  │
│  │ - Вычисление KPI (success rate, avg duration)           │  │
│  │ - Генерация отчетов (ежедневные, еженедельные)          │  │
│  │ - Обнаружение аномалий (spike detection)                │  │
│  │                                                        │  │
│  │ Отслеживает события:                                  │  │
│  │ ← call.ended                                           │  │
│  │ ← agent.sentiment                                      │  │
│  │ ← agent.escalation_triggered                           │  │
│  │                                                        │  │
│  │ Сохраняет в TimescaleDB / ClickHouse                  │  │
│  │ для быстрого анализа временных рядов                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Слой 4: DATA LAYER (Базы данных и хранилище)

**Назначение**: Персистентное хранилище всех данных системы

```
┌────────────────────────────────────────────────────────────────┐
│              DATA LAYER (Persistence)                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PRIMARY DATABASE: PostgreSQL (Neon.tech)               │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Таблицы:                                               │  │
│  │                                                        │  │
│  │ organizations                                          │  │
│  │  ├── id (UUID, PRIMARY KEY)                           │  │
│  │  ├── name (VARCHAR)                                   │  │
│  │  ├── owner_id (FK -> users)                           │  │
│  │  ├── plan (VARCHAR: 'pro', 'enterprise')              │  │
│  │  ├── created_at (TIMESTAMP)                           │  │
│  │  └── metadata (JSONB: features, limits)               │  │
│  │                                                        │  │
│  │ users                                                  │  │
│  │  ├── id (UUID, PK)                                    │  │
│  │  ├── email (VARCHAR, UNIQUE)                          │  │
│  │  ├── name (VARCHAR)                                   │  │
│  │  ├── password_hash (VARCHAR)                          │  │
│  │  ├── org_id (FK -> organizations)                     │  │
│  │  ├── role (VARCHAR: 'admin', 'agent', 'viewer')       │  │
│  │  ├── last_login (TIMESTAMP)                           │  │
│  │  └── email_verified (BOOLEAN)                         │  │
│  │                                                        │  │
│  │ agents                                                 │  │
│  │  ├── id (UUID, PK)                                    │  │
│  │  ├── org_id (FK)                                      │  │
│  │  ├── name (VARCHAR)                                   │  │
│  │  ├── description (TEXT)                               │  │
│  │  ├── system_prompt (TEXT: инструкция для LLM)         │  │
│  │  ├── status (VARCHAR: 'draft', 'active', 'paused')    │  │
│  │  ├── llm_model (VARCHAR: 'gpt-4o-mini')               │  │
│  │  ├── voice_id (VARCHAR: ElevenLabs voice)             │  │
│  │  ├── temperature (FLOAT: 0-1, для разнообразия)      │  │
│  │  ├── max_tokens (INT: лимит ответа)                  │  │
│  │  ├── webhook_url (VARCHAR: для внешних интеграций)    │  │
│  │  ├── metadata (JSONB: custom fields)                  │  │
│  │  └── created_at, updated_at                           │  │
│  │                                                        │  │
│  │ phone_numbers                                          │  │
│  │  ├── id (UUID, PK)                                    │  │
│  │  ├── org_id (FK)                                      │  │
│  │  ├── number (VARCHAR: '+71234567890')                │  │
│  │  ├── agent_id (FK -> agents)                          │  │
│  │  ├── sip_trunk_id (VARCHAR: MTS Exolve ID)            │  │
│  │  ├── status (VARCHAR: 'active', 'inactive')           │  │
│  │  └── created_at                                       │  │
│  │                                                        │  │
│  │ calls (ключевая таблица для аналитики)                │  │
│  │  ├── id (UUID, PK)                                    │  │
│  │  ├── org_id (FK)                                      │  │
│  │  ├── agent_id (FK)                                    │  │
│  │  ├── from_number (VARCHAR: звонящий)                 │  │
│  │  ├── to_number (VARCHAR: принимающий)                │  │
│  │  ├── direction (VARCHAR: 'inbound', 'outbound')       │  │
│  │  ├── status (VARCHAR: 'ringing', 'connected', 'ended')│  │
│  │  ├── started_at (TIMESTAMP WITH TZ)                  │  │
│  │  ├── ended_at (TIMESTAMP WITH TZ)                    │  │
│  │  ├── duration (INT: в секундах)                      │  │
│  │  ├── billing_seconds (INT: для тарификации)          │  │
│  │  ├── recording_url (VARCHAR: ссылка на S3)            │  │
│  │  ├── transcript (TEXT: полный текст разговора)        │  │
│  │  ├── cost (NUMERIC: в копейках)                       │  │
│  │  ├── sentiment (VARCHAR: pos/neg/neutral)             │  │
│  │  ├── escalated_to (VARCHAR: email оператора)          │  │
│  │  └── metadata (JSONB: custom tracking)                │  │
│  │                                                        │  │
│  │ agent_tools (many-to-many: какие инструменты у агента)│  │
│  │  ├── agent_id (FK)                                    │  │
│  │  ├── tool_id (FK -> tools)                            │  │
│  │  ├── config (JSONB: специфичные параметры)            │  │
│  │  └── enabled (BOOLEAN)                                │  │
│  │                                                        │  │
│  │ conversations (история разговоров для RAG)             │  │
│  │  ├── id (UUID, PK)                                    │  │
│  │  ├── call_id (FK)                                     │  │
│  │  ├── speaker (VARCHAR: 'user', 'agent')               │  │
│  │  ├── text (TEXT: что было сказано)                    │  │
│  │  ├── timestamp (TIMESTAMP: когда)                     │  │
│  │  ├── embedding (VECTOR: для семантического поиска)    │  │
│  │  └── metadata (JSONB: tts_audio_url, etc)            │  │
│  │                                                        │  │
│  │ billing_transactions                                   │  │
│  │  ├── id (UUID, PK)                                    │  │
│  │  ├── org_id (FK)                                      │  │
│  │  ├── amount (NUMERIC: в копейках)                     │  │
│  │  ├── type (VARCHAR: 'debit', 'credit', 'refund')      │  │
│  │  ├── status (VARCHAR: 'pending', 'completed', 'failed')│  │
│  │  ├── call_id (FK, nullable)                           │  │
│  │  ├── payment_id (VARCHAR: YooKassa ID)                │  │
│  │  └── created_at                                       │  │
│  │                                                        │  │
│  │ Индексы для производительности:                       │  │
│  │ - calls(org_id, agent_id) для быстрого фильтра      │  │
│  │ - calls(created_at DESC) для сортировки              │  │
│  │ - conversations(call_id) для получения текста         │  │
│  │ - conversations(embedding) GiST для семпоиска         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ CACHE LAYER: Redis (in-memory store)                   │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Использование:                                         │  │
│  │ - Активные сессии (socket.io для real-time updates)    │  │
│  │ - Кэш балансов юзеров (читается часто)                │  │
│  │ - Rate limiting (sliding window)                       │  │
│  │ - Сессии долгоживущие инструментов (execution state)   │  │
│  │ - Message queue для асинхронных задач                 │  │
│  │                                                        │  │
│  │ Примеры ключей:                                       │  │
│  │ - user:123:balance (быстрый доступ к балансу)         │  │
│  │ - call:uuid:active (текущий статус звонка)            │  │
│  │ - ratelimit:ip:requests (для DDoS protection)          │  │
│  │ - session:token (JWT refresh tokens)                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ MESSAGE QUEUE: Apache Kafka (event streaming)          │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Topics (event streams):                                │  │
│  │                                                        │  │
│  │ call-events                                            │  │
│  │  ├── call.initiated                                    │  │
│  │  ├── call.agent_assigned                               │  │
│  │  ├── call.user_spoke                                   │  │
│  │  ├── call.agent_responded                              │  │
│  │  ├── call.ended                                        │  │
│  │  └── call.interrupted                                  │  │
│  │  Partition by: org_id (все события одной компании →   │  │
│  │                одна партиция для гарантии порядка)     │  │
│  │                                                        │  │
│  │ agent-events                                           │  │
│  │  ├── agent.processing                                  │  │
│  │  ├── agent.calling_tool                                │  │
│  │  ├── agent.response_ready                              │  │
│  │  ├── agent.sentiment                                   │  │
│  │  └── agent.escalation_triggered                        │  │
│  │  Partition by: call_id                                 │  │
│  │                                                        │  │
│  │ tool-events                                            │  │
│  │  ├── tool.started                                      │  │
│  │  ├── tool.completed                                    │  │
│  │  └── tool.failed                                       │  │
│  │  Partition by: agent_id                                │  │
│  │                                                        │  │
│  │ billing-events                                         │  │
│  │  ├── billing.minutes_deducted                          │  │
│  │  ├── billing.balance_low                               │  │
│  │  ├── billing.payment_received                          │  │
│  │  └── billing.call_rejected                             │  │
│  │  Partition by: org_id                                  │  │
│  │                                                        │  │
│  │ Retention: 7 дней (для отладки)                       │  │
│  │ Replication: 3 (отказоустойчивость)                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ OBJECT STORAGE: AWS S3 (аудио и документы)            │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Структура бакета:                                      │  │
│  │ s3://voice-agent-platform/                             │  │
│  │  ├── recordings/                                       │  │
│  │  │   ├── {org_id}/{call_id}.wav                        │  │
│  │  │   └── {org_id}/{call_id}-user.wav                   │  │
│  │  ├── transcripts/                                      │  │
│  │  │   └── {org_id}/{call_id}.json                       │  │
│  │  └── backups/                                          │  │
│  │      └── {date}/                                       │  │
│  │                                                        │  │
│  │ Настройки:                                            │  │
│  │ - Encryption: AES-256 (SSE-S3)                        │  │
│  │ - Versioning: enabled (восстановление)                │  │
│  │ - Lifecycle: delete after 90 days (экономия)          │  │
│  │ - Public access: blocked (безопасность)               │  │
│  │ - CloudFront CDN: для быстрого доступа (США/EU)       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ ANALYTICS DATABASE: TimescaleDB / ClickHouse           │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ (специализирована для временных рядов и аналитики)     │  │
│  │ Таблицы:                                               │  │
│  │ - call_metrics (volume, duration, cost по дням)        │  │
│  │ - agent_performance (success rate, sentiment)          │  │
│  │ - billing_hourly (трекинг доходов в реальном времени)  │  │
│  │                                                        │  │
│  │ Используется для:                                      │  │
│  │ - Быстрого построения dashboards                       │  │
│  │ - Агрегации метрик (1M+ записей/день)                 │  │
│  │ - Обнаружения аномалий (spike detection)               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ VECTOR DATABASE: Pinecone / Weaviate (для RAG)         │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Использование:                                         │  │
│  │ - Семантический поиск в истории разговоров            │  │
│  │ - Контекст для новых звонков (похожие прошлые)         │  │
│  │ - Embedding'и последних 1000 разговоров                │  │
│  │                                                        │  │
│  │ Процесс:                                               │  │
│  │ 1. Новое сообщение в разговоре                         │  │
│  │ 2. Encode в embedding (OpenAI text-embedding-3-small)  │  │
│  │ 3. Semantic search в Pinecone                          │  │
│  │ 4. Top-3 похожих фрагмента → в контекст LLM           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Слой 5: EXTERNAL INTEGRATIONS

```
┌────────────────────────────────────────────────────────────────┐
│          EXTERNAL INTEGRATIONS & 3RD PARTY SERVICES           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ VOICE INFRASTRUCTURE                                    │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │ LiveKit Cloud (WebRTC infrastructure)                   │ │
│  │ ├── Room management (create/delete rooms)               │ │
│  │ ├── Peer connections (user ↔ agent audio)               │ │
│  │ ├── Recording & playback                                │ │
│  │ └── Token generation (signed JWT для доступа)           │ │
│  │ API: https://api.livekit.io                             │ │
│  │                                                          │ │
│  │ MTS Exolve (SIP trunk provider в России)                │ │
│  │ ├── DID management (+7 номера)                          │ │
│  │ ├── SIP Termination (маршрутизация входящих звонков)    │ │
│  │ ├── Origination (исходящие звонки)                      │ │
│  │ └── CDR (call detail records для биллинга)              │ │
│  │ Integration: SIP трафик, TLS шифрование                 │ │
│  │                                                          │ │
│  │ Deepgram (Speech-to-Text)                               │ │
│  │ ├── Streaming ASR (real-time transcription)             │ │
│  │ ├── Confidence scores (для качества)                    │ │
│  │ ├── Speaker diarization (кто говорит)                   │ │
│  │ └── Punctuation & capitalization                        │ │
│  │ API: WebSocket streaming для низкой латентности         │ │
│  │                                                          │ │
│  │ ElevenLabs (Text-to-Speech)                             │ │
│  │ ├── Natural voice synthesis (не робот-звучащие голоса)  │ │
│  │ ├── Streaming audio (начинаем воспроизведение сразу)    │ │
│  │ ├── Multiple languages (русский в том числе)            │ │
│  │ ├── Voice cloning (возможность использовать свой голос) │ │
│  │ └── Stability & similarity (настройка характера голоса) │ │
│  │ API: async generation или streaming playback            │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ AI MODELS                                                │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │ OpenAI GPT-4o-mini                                       │ │
│  │ ├── Model: gpt-4o-mini (дешевле, быстрее, чем gpt-4o)   │ │
│  │ ├── Rate: ~$0.00015 / 1K input tokens                   │ │
│  │ ├── Features: vision, function calling                  │ │
│  │ ├── Latency: 200-500ms для токена (в среднем)           │ │
│  │ └── Fallback: если rate limited → Claude 3.5 Sonnet     │ │
│  │                                                          │ │
│  │ Anthropic Claude 3.5 Sonnet                             │ │
│  │ ├── Model: claude-3-5-sonnet                            │ │
│  │ ├── Rate: ~$0.003 / 1K input tokens (дороже)            │ │
│  │ ├── Features: tool use, vision, long context (200K)     │ │
│  │ ├── Latency: 100-300ms                                  │ │
│  │ └── Use case: complex reasoning + backup                │ │
│  │                                                          │ │
│  │ Open Source Llama 2 / 3.1 (on-device)                   │ │
│  │ ├── Deploy: на edge GPU (latency <50ms)                 │ │
│  │ ├── Features: tool calling через структурированный JSON │ │
│  │ ├── Cost: $0 (только инфраструктура)                    │ │
│  │ └── Use case: fallback когда облачные недоступны        │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ PAYMENTS                                                 │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │ YooKassa (платежный агрегатор)                           │ │
│  │ ├── Payment methods:                                    │ │
│  │ │   ├── Карты Visa/Mastercard                          │ │
│  │ │   ├── Яндекс.Касса                                   │ │
│  │ │   ├── СБП (System for Payments)                       │ │
│  │ │   ├── Альфа-Клик                                     │ │
│  │ │   └── WebMoney                                       │ │
│  │ ├── Webhook: https://webhook.yookassa.ru (подтверждение)│ │
│  │ ├── Commission: 2% + 50 руб / транзакция                │ │
│  │ └── Settlement: T+2 дня на расчетный счет               │ │
│  │                                                          │ │
│  │ Stripe (для международных платежей)                      │ │
│  │ ├── Готов на будущее (если расширимся глобально)        │ │
│  │ └── Webhook для подтверждения платежей                  │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ CRM & INTEGRATIONS                                       │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │ n8n Automation Platform (workflow engine)                │ │
│  │ ├── Доступны 400+ интеграций                            │ │
│  │ ├── Примеры:                                            │ │
│  │ │   ├── Slack: отправить уведомление при escalation     │ │
│  │ │   ├── Google Sheets: логировать все звонки            │ │
│  │ │   ├── Zapier: транспортировать данные в CRM           │ │
│  │ │   ├── PostgreSQL: сохранить данные в своей БД         │ │
│  │ │   └── Telegram: боты уведомлений                      │ │
│  │ ├── Протокол: MCP (Model Context Protocol)              │ │
│  │ └── Выполнение: параллельно на 5 инструментов           │ │
│  │                                                          │ │
│  │ Webhooks (callback system)                              │ │
│  │ ├── Agent может отправить event на custom URL           │ │
│  │ ├── Example: https://customer.com/voice-webhook         │ │
│  │ ├── Payload: call_id, duration, recording_url, etc      │ │
│  │ ├── Retry: 3 попытки с exponential backoff              │ │
│  │ └── Security: HMAC-SHA256 signature для валидации        │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔑 КЛЮЧЕВЫЕ КОМПОНЕНТЫ (С КОДОМ)

### 1. Event-Driven Call Flow

Последовательность событий при одном звонке:

```
┌─────────────────────────────────────────────────────────────┐
│                    CALL FLOW (Event-Driven)                 │
└─────────────────────────────────────────────────────────────┘

1️⃣ INCOMING CALL
   User dials: +71234567890
   ↓
   MTS Exolve → LiveKit (SIP bridge)
   ↓
   [call.initiated event published]
   {
     "call_id": "uuid-123",
     "org_id": "org-456",
     "from_number": "+79998887766",
     "to_number": "+71234567890",
     "timestamp": "2025-12-07T22:45:00Z",
     "direction": "inbound"
   }

2️⃣ CALL MANAGEMENT SERVICE processes event
   - Creates room in LiveKit
   - Fetches agent config from DB
   - Generates SID token
   - Connects user to room
   ↓
   [call.agent_assigned event]
   {
     "call_id": "uuid-123",
     "agent_id": "agent-789",
     "livekit_room": "call-uuid-123"
   }

3️⃣ AGENT ORCHESTRATION SERVICE subscribes
   - Initializes conversation context
   - Loads system prompt for agent
   - Starts listening to audio stream
   - Begins STT processing
   ↓
   Audio stream flows: User → Deepgram (async ASR)

4️⃣ STREAMING ASR (Deepgram)
   User says: "Здравствуйте, у меня проблема с счетом"
   ↓
   Deepgram streams partial results:
   - "Здравствуйте" (confidence: 0.98)
   - "Здравствуйте, у меня" (confidence: 0.97)
   - "Здравствуйте, у меня проблема" (confidence: 0.96)
   - "Здравствуйте, у меня проблема с счетом" (confidence: 0.95)
   ↓
   [call.user_spoke event]
   {
     "call_id": "uuid-123",
     "speaker": "user",
     "text": "Здравствуйте, у меня проблема с счетом",
     "confidence": 0.95,
     "timestamp": "2025-12-07T22:45:05Z"
   }

5️⃣ AGENT ORCHESTRATION ENGINE processes
   - Receive user text from Kafka
   - Check: Is this a valid user utterance? (VAD passed)
   - Interrupt check: Did user interrupt previous response?
   - Load conversation context (previous 10 messages from Redis/DB)
   - Create prompt:
     System: "Ты — агент поддержки клиентов..."
     Context: "Клиент: [previous messages]"
     Current: "User: Здравствуйте, у меня проблема с счетом"
   - Call LLM (OpenAI GPT-4o-mini)
   ↓
   [agent.processing event]
   {
     "call_id": "uuid-123",
     "status": "thinking",
     "timestamp": "2025-12-07T22:45:06Z"
   }

6️⃣ LLM PROCESSES & RESPONDS
   GPT-4o-mini analyzes:
   - Intent: customer_issue (проблема с счетом)
   - Required tool: lookup_account({phone: "+79998887766"})
   - Response: "Сейчас я проверю ваш счет..."
   ↓
   Streaming tokens: "Сейчас" → "я" → "проверю" → ...
   ↓
   [agent.calling_tool event]
   {
     "call_id": "uuid-123",
     "tool_name": "lookup_account",
     "parameters": {
       "phone": "+79998887766"
     }
   }

7️⃣ TOOL EXECUTION (Parallel)
   Tool Executor Service calls CRM API:
   - Validates parameters (phone format)
   - Calls: POST https://api.crm.example.com/lookup
   - Response: {account_id, balance, last_payment, ...}
   ↓
   [tool.completed event]
   {
     "call_id": "uuid-123",
     "tool_name": "lookup_account",
     "result": {
       "account_id": "ACC123",
       "balance": 5000,
       "status": "active"
     }
   }

8️⃣ AGENT CONTINUES with tool result
   LLM now knows: Account balance is 5000 rubles
   Generates: "Ваш счет активен, текущий баланс: 5000 рублей..."
   ↓
   LLM streams full response to TTS
   ↓
   [agent.response_ready event]
   {
     "call_id": "uuid-123",
     "text": "Ваш счет активен, текущий баланс: 5000 рублей...",
     "audio_url": "s3://bucket/audio/call-uuid-123-response-1.mp3"
   }

9️⃣ TEXT-TO-SPEECH (ElevenLabs)
   Converts response text → natural sounding audio
   - Voice ID: "alex" (pre-configured for this agent)
   - Language: Russian
   - Streaming: starts audio while still generating
   ↓
   Audio streams to user through LiveKit

🔟 USER HEARS RESPONSE
   Natural conversation happens...
   Agent responds to follow-up questions
   
1️⃣1️⃣ CONVERSATION CONTINUES
    Until user says: "Спасибо, до свидания"
    Agent detects: end-of-conversation intent
    ↓
    [call.ended event]
    {
      "call_id": "uuid-123",
      "duration": 245,
      "ended_at": "2025-12-07T22:48:05Z",
      "status": "completed",
      "sentiment": "positive"
    }

1️⃣2️⃣ POST-CALL PROCESSING
    Billing Service processes:
    - Duration: 245 seconds ≈ 4.1 minutes
    - Rate: 10 rubles per minute
    - Cost: 41 ruble
    ↓
    [billing.minutes_deducted event]
    
    Analytics Service processes:
    - Call duration, sentiment, success rate
    - Updates dashboards
    - Generates reports
    
    Transcript stored in PostgreSQL
    Audio recording stored in S3
    Embeddings generated for RAG
```

### 2. Database Schema (SQL)

```sql
-- ORGANIZATIONS (Multi-tenancy)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id),
    plan VARCHAR(50) NOT NULL DEFAULT 'pro', -- 'free', 'pro', 'enterprise'
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'suspended', 'deleted'
    monthly_call_limit INT DEFAULT 10000, -- для free плана 100 звонков
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}', -- custom fields, features flags
    CONSTRAINT positive_limit CHECK (monthly_call_limit > 0)
);

-- USERS (Управление доступом)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'agent', -- 'admin', 'agent', 'viewer'
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'deleted'
    last_login TIMESTAMP,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- AGENTS (AI Voice Agents)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL, -- инструкция для LLM
    llm_model VARCHAR(100) DEFAULT 'gpt-4o-mini', -- 'gpt-4o-mini', 'claude-3-5-sonnet'
    llm_temperature FLOAT DEFAULT 0.7, -- 0-1, выше = более творческий ответ
    llm_max_tokens INT DEFAULT 500, -- максимум слов в ответе
    voice_id VARCHAR(100) DEFAULT 'alex', -- ElevenLabs voice ID
    voice_speed FLOAT DEFAULT 1.0,
    status VARCHAR(50) DEFAULT 'active', -- 'draft', 'active', 'paused'
    webhook_url VARCHAR(500), -- для внешних интеграций
    max_concurrent_calls INT DEFAULT 10,
    greeting_text TEXT, -- приветствие при ответе
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    INDEX agents_org_id (org_id),
    INDEX agents_status (status)
);

-- PHONE NUMBERS (Привязанные номера телефонов)
CREATE TABLE phone_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    number VARCHAR(20) NOT NULL, -- '+71234567890'
    sip_trunk_id VARCHAR(100), -- ID тока в MTS Exolve
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_number_per_org UNIQUE(org_id, number),
    INDEX phone_agent_id (agent_id),
    INDEX phone_status (status)
);

-- AGENT TOOLS (Many-to-Many: какие инструменты может использовать агент)
CREATE TABLE agent_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}', -- специфичные настройки для инструмента
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_agent_tool UNIQUE(agent_id, tool_id)
);

-- TOOLS (Библиотека инструментов для агентов)
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tool_type VARCHAR(50), -- 'http_api', 'database', 'n8n_workflow', 'custom_python'
    endpoint_url VARCHAR(500), -- для HTTP API
    schema_definition JSONB NOT NULL, -- JSON Schema для параметров
    timeout_seconds INT DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CALLS (Главная таблица звонков)
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    phone_id UUID REFERENCES phone_numbers(id),
    from_number VARCHAR(20) NOT NULL, -- звонящий
    to_number VARCHAR(20) NOT NULL, -- принимающий
    direction VARCHAR(20) NOT NULL, -- 'inbound', 'outbound'
    status VARCHAR(50) NOT NULL DEFAULT 'initiated', -- 'ringing', 'connected', 'ended'
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_seconds INT,
    recording_url VARCHAR(500), -- ссылка на S3
    cost_kopecks NUMERIC(10, 2) DEFAULT 0, -- стоимость в копейках
    sentiment VARCHAR(50), -- 'positive', 'neutral', 'negative'
    escalated_to VARCHAR(255), -- email оператора если escalation
    ivr_data JSONB DEFAULT '{}', -- для получения из IVR
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_duration CHECK (duration_seconds IS NULL OR duration_seconds > 0),
    INDEX calls_org_agent (org_id, agent_id),
    INDEX calls_created (created_at DESC),
    INDEX calls_status (status)
);

-- CONVERSATIONS (История разговоров для RAG)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    speaker VARCHAR(50) NOT NULL, -- 'user', 'agent'
    text TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    embedding vector(384), -- для semantic search (OpenAI text-embedding-3-small)
    tts_audio_url VARCHAR(500), -- если agent говорил, ссылка на аудио
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX conversations_call_id (call_id),
    INDEX conversations_created (created_at DESC)
);

-- BILLING TRANSACTIONS (История платежей)
CREATE TABLE billing_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    call_id UUID REFERENCES calls(id), -- nullable, т.к. может быть платеж напрямую
    amount_kopecks NUMERIC(10, 2) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'debit' (тариф), 'credit' (пополнение), 'refund'
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    yookassa_payment_id VARCHAR(255), -- ID платежа в YooKassa
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX billing_org_id (org_id),
    INDEX billing_created (created_at DESC)
);

-- BALANCES (Быстрый кэш баланса - денормализованная таблица)
CREATE TABLE balances (
    org_id UUID PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
    balance_kopecks NUMERIC(10, 2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AUDIT LOG (Для compliance)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES users(id), -- кто сделал действие
    action VARCHAR(100) NOT NULL, -- 'agent.created', 'call.started', etc
    resource_type VARCHAR(50), -- 'agent', 'call', 'user'
    resource_id UUID,
    changes JSONB, -- что изменилось
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX audit_org_created (org_id, created_at DESC)
);

-- Создание индекса для поиска по embedding (vector)
CREATE INDEX ON conversations USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Row Level Security (для multi-tenancy)
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
CREATE POLICY calls_org_isolation ON calls
    USING (org_id = current_user_org_id())
    WITH CHECK (org_id = current_user_org_id());

-- Аналогично для других таблиц
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY agents_org_isolation ON agents
    USING (org_id = current_user_org_id());
```

### 3. Agent Orchestration (Python)

```python
# agent_service/main.py
import asyncio
import json
from datetime import datetime
from typing import AsyncIterator, Optional
from dataclasses import dataclass

from livekit import agents, llm, asr, tts
from livekit.agents import JobContext, llm as llm_module
from pydantic import BaseModel
import anthropic
import openai
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class AgentConfig:
    """Конфигурация агента из БД"""
    id: str
    org_id: str
    name: str
    system_prompt: str
    llm_model: str  # 'gpt-4o-mini' или 'claude-3-5-sonnet'
    temperature: float
    max_tokens: int
    voice_id: str
    webhook_url: Optional[str] = None

@dataclass
class ConversationContext:
    """Контекст разговора в памяти"""
    call_id: str
    org_id: str
    agent_id: str
    messages: list  # [{role, content, timestamp}]
    user_sentiment: str = "neutral"
    tools_called: int = 0
    interrupts: int = 0
    start_time: datetime = None
    
    @property
    def context_window(self) -> list:
        """Последние 10 сообщений для LLM контекста"""
        return self.messages[-10:] if len(self.messages) > 10 else self.messages

class ToolCall(BaseModel):
    """Формат tool call из LLM"""
    tool_name: str
    parameters: dict
    
class ToolResult(BaseModel):
    """Результат выполнения tool'а"""
    tool_name: str
    result: dict
    error: Optional[str] = None

# ============================================================================
# AGENT ORCHESTRATION ENGINE
# ============================================================================

class VoiceAgentOrchestrator:
    """
    Основной класс для управления разговором агента.
    
    Event-driven loop:
    1. Слушаем пользователя (VAD + STT)
    2. Отправляем текст в LLM
    3. LLM возвращает ответ или tool_call
    4. Если tool_call - выполняем параллельно
    5. Агент говорит (TTS)
    6. Ждем следующего сообщения от пользователя
    """
    
    def __init__(self, ctx: JobContext, agent_config: AgentConfig):
        self.ctx = ctx
        self.config = agent_config
        self.context = ConversationContext(
            call_id=ctx.job.metadata.get('call_id'),
            org_id=agent_config.org_id,
            agent_id=agent_config.id,
            messages=[],
            start_time=datetime.now()
        )
        
        # Инициализируем сервисы
        self.asr = self._init_asr()
        self.tts = self._init_tts()
        self.llm = self._init_llm()
        self.tool_executor = ToolExecutor(org_id=agent_config.org_id)
        
        logger.info(f"[{self.context.call_id}] Агент инициализирован: {agent_config.name}")
    
    def _init_asr(self) -> asr.ASR:
        """Инициализируем Speech-to-Text (Deepgram)"""
        return asr.StreamingASR(
            language="ru",
            sample_rate=16000,
            channels=1,
            enable_interim_results=True,
            use_deepgram=True  # streaming для низкой латентности
        )
    
    def _init_tts(self) -> tts.TTS:
        """Инициализируем Text-to-Speech (ElevenLabs)"""
        return tts.ElevenLabs(
            voice=self.config.voice_id,
            model="eleven_monolingual_v1",
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            stream=True  # streaming playback
        )
    
    def _init_llm(self) -> llm.LLM:
        """Инициализируем LLM с fallback'ом"""
        if self.config.llm_model == "gpt-4o-mini":
            return self._init_openai()
        elif self.config.llm_model == "claude-3-5-sonnet":
            return self._init_claude()
        else:
            raise ValueError(f"Unknown model: {self.config.llm_model}")
    
    def _init_openai(self) -> llm.LLM:
        """OpenAI как основная модель"""
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return llm.OpenAI(
            client=client,
            model="gpt-4o-mini",
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
    
    def _init_claude(self) -> llm.LLM:
        """Claude как fallback при недоступности OpenAI"""
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return llm.Claude(
            client=client,
            model="claude-3-5-sonnet-20241022",
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
    
    async def run(self):
        """
        Главный loop разговора.
        
        Событие-ориентированная архитектура:
        - Подписываемся на user_spoke события из Kafka
        - Обрабатываем промежуточные результаты ASR
        - Отправляем в LLM
        - Обрабатываем tool calls параллельно
        - Отправляем TTS для озвучивания
        """
        try:
            logger.info(f"[{self.context.call_id}] Начинаем loop разговора")
            
            # Приветствие
            await self._greet_user()
            
            # Главный loop
            while True:
                # 1. Слушаем пользователя (streaming ASR)
                user_text, is_final = await self._listen_to_user()
                
                if user_text is None:
                    # Пользователь бросил трубку
                    break
                
                if not is_final:
                    # Промежуточный результат - пропускаем
                    continue
                
                # Публикуем событие в Kafka
                await self._publish_event("call.user_spoke", {
                    "call_id": self.context.call_id,
                    "text": user_text,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 2. Проверяем на end-of-conversation
                if self._is_end_of_conversation(user_text):
                    logger.info(f"[{self.context.call_id}] Пользователь завершил разговор")
                    await self._say("Спасибо за разговор. До свидания!")
                    break
                
                # 3. Отправляем в LLM и получаем ответ
                response_text, tool_calls = await self._process_with_llm(user_text)
                
                # 4. Если есть tool calls - выполняем параллельно
                if tool_calls:
                    tool_results = await self._execute_tools_parallel(tool_calls)
                    # Отправляем результаты в LLM для уточнения ответа
                    response_text = await self._refine_response_with_tools(
                        response_text, 
                        tool_results
                    )
                
                # 5. Говорим ответ (TTS с streaming)
                await self._say(response_text)
                
                # Добавляем в контекст
                self.context.messages.append({
                    "role": "user",
                    "content": user_text,
                    "timestamp": datetime.now().isoformat()
                })
                self.context.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"[{self.context.call_id}] Error: {e}", exc_info=True)
            await self._publish_event("agent.error", {
                "call_id": self.context.call_id,
                "error": str(e)
            })
    
    async def _listen_to_user(self, timeout: int = 30) -> tuple[Optional[str], bool]:
        """
        Слушаем пользователя с использованием streaming ASR.
        
        Возвращает:
        - (text, is_final): текст и флаг финальности
        - (None, False): если истекло время ожидания или ошибка
        """
        try:
            async for result in self.asr.stream(self.ctx.room):
                if result.is_final:
                    # Полная фраза
                    text = result.text.strip()
                    if text:
                        logger.info(f"[{self.context.call_id}] USER: {text}")
                        return text, True
                    else:
                        # Молчание - пробуем снова
                        return None, False
                else:
                    # Промежуточный результат (можно показать в UI)
                    logger.debug(f"[{self.context.call_id}] Interim: {result.text}")
        
        except asyncio.TimeoutError:
            # Пользователь молчит 30 сек
            logger.warning(f"[{self.context.call_id}] Timeout при слушании")
            return None, False
    
    async def _process_with_llm(self, user_text: str) -> tuple[str, list[ToolCall]]:
        """
        Отправляем текст в LLM и получаем ответ.
        
        LLM может вернуть:
        1. Простой текстовый ответ
        2. Tool call (для получения информации из внешних систем)
        3. Оба (ответ + tool call)
        
        Возвращает:
        - (response_text, tool_calls)
        """
        # Строим сообщение для LLM
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt()
            },
            *self.context.context_window,
            {
                "role": "user",
                "content": user_text
            }
        ]
        
        # Определяем доступные инструменты
        tools = await self._get_available_tools()
        
        logger.info(f"[{self.context.call_id}] Отправляем в LLM, {len(self.context.context_window)} сообщений в контексте")
        
        try:
            # Вызываем LLM
            response = await self.llm.chat(
                messages=messages,
                tools=tools,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # Парсим ответ
            response_text = ""
            tool_calls = []
            
            for choice in response.choices:
                if choice.message.content:
                    response_text = choice.message.content
                
                if choice.message.tool_calls:
                    for tool_call in choice.message.tool_calls:
                        tool_calls.append(ToolCall(
                            tool_name=tool_call.function.name,
                            parameters=json.loads(tool_call.function.arguments)
                        ))
            
            logger.info(f"[{self.context.call_id}] LLM ответ: {response_text[:50]}...")
            if tool_calls:
                logger.info(f"[{self.context.call_id}] LLM вызвал {len(tool_calls)} tool(s)")
            
            return response_text, tool_calls
        
        except Exception as e:
            logger.error(f"[{self.context.call_id}] LLM error: {e}")
            # Fallback к локальной модели (Llama)
            logger.info(f"[{self.context.call_id}] Trying fallback LLM")
            # ... (код для fallback)
    
    async def _execute_tools_parallel(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """
        Выполняем до 5 инструментов параллельно.
        
        Каждый tool должен завершиться за 30 сек, иначе timeout.
        """
        logger.info(f"[{self.context.call_id}] Выполняем {len(tool_calls)} инструмент(ов)")
        
        # Публикуем событие
        for tc in tool_calls:
            await self._publish_event("agent.calling_tool", {
                "call_id": self.context.call_id,
                "tool_name": tc.tool_name,
                "parameters": tc.parameters
            })
        
        # Выполняем параллельно (но максимум 5)
        tasks = [
            self.tool_executor.execute(tc, timeout=30)
            for tc in tool_calls[:5]
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработаем ошибки
        tool_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Tool {tool_calls[i].tool_name} failed: {result}")
                tool_results.append(ToolResult(
                    tool_name=tool_calls[i].tool_name,
                    result={},
                    error=str(result)
                ))
            else:
                tool_results.append(result)
        
        return tool_results
    
    async def _refine_response_with_tools(
        self,
        initial_response: str,
        tool_results: list[ToolResult]
    ) -> str:
        """
        После получения результатов от tools, отправляем их в LLM
        для уточнения ответа.
        
        Пример:
        - LLM сказал: "Сейчас проверю вашу информацию"
        - Tool вернул: {account_id: 123, balance: 5000}
        - LLM теперь может сказать: "Ваш счет активен, баланс: 5000 руб"
        """
        # Форматируем результаты для LLM
        tool_context = "\n".join([
            f"Tool '{tr.tool_name}' результат: {json.dumps(tr.result)}"
            if not tr.error else f"Tool '{tr.tool_name}' ошибка: {tr.error}"
            for tr in tool_results
        ])
        
        # Создаем уточняющий prompt
        refine_prompt = f"""
        У вас есть результаты от инструментов:
        
        {tool_context}
        
        Исходный ответ: "{initial_response}"
        
        Используя информацию из инструментов, дайте улучшенный ответ пользователю.
        Ответ должен быть на русском языке и звучать естественно для разговора.
        """
        
        response = await self.llm.chat(
            messages=[{"role": "user", "content": refine_prompt}],
            max_tokens=300
        )
        
        return response.choices[0].message.content
    
    async def _say(self, text: str):
        """
        Озвучиваем текст через TTS (ElevenLabs).
        
        Используем streaming для низкой латентности:
        - Начинаем воспроизведение пока еще генерируется аудио
        """
        logger.info(f"[{self.context.call_id}] AGENT: {text[:50]}...")
        
        try:
            # Streaming TTS - начинает проигрываться сразу
            async for audio_chunk in self.tts.stream(text):
                # Отправляем аудиочанк в LiveKit
                await self.ctx.room.publish_audio(audio_chunk)
        
        except Exception as e:
            logger.error(f"[{self.context.call_id}] TTS error: {e}")
    
    def _build_system_prompt(self) -> str:
        """Строим полный системный prompt с контекстом"""
        prompt = self.config.system_prompt
        
        # Добавляем контекст о пользователе
        prompt += f"\n\nТекущий звонок начался в {self.context.start_time.isoformat()}"
        prompt += f"\nСентимент пользователя: {self.context.user_sentiment}"
        
        return prompt
    
    async def _get_available_tools(self) -> list:
        """Получаем список доступных инструментов для этого агента из БД"""
        # Запрашиваем из PostgreSQL
        tools = await self._db_query("""
            SELECT json_build_object(
                'name', t.name,
                'description', t.description,
                'parameters', t.schema_definition
            )
            FROM agent_tools at
            JOIN tools t ON at.tool_id = t.id
            WHERE at.agent_id = %s AND at.enabled = true
        """, [self.config.id])
        
        return tools
    
    def _is_end_of_conversation(self, text: str) -> bool:
        """Проверяем, завершил ли пользователь разговор"""
        end_phrases = [
            "спасибо", "до свидания", "пока", "до встречи",
            "все", "хватит", "нет больше вопросов"
        ]
        return any(phrase in text.lower() for phrase in end_phrases)
    
    async def _greet_user(self):
        """Приветствие при ответе на звонок"""
        greeting = f"Здравствуйте! Мое имя {self.config.name}. Чем я вам помочь?"
        await self._say(greeting)
    
    async def _publish_event(self, event_type: str, data: dict):
        """Публикуем событие в Kafka"""
        from kafka import KafkaProducer
        # ... (код для публикации в Kafka)

# ============================================================================
# TOOL EXECUTOR
# ============================================================================

class ToolExecutor:
    """Выполнение инструментов (HTTP API, базы данных, n8n workflows)"""
    
    def __init__(self, org_id: str):
        self.org_id = org_id
        self.http_client = aiohttp.ClientSession()
    
    async def execute(self, tool_call: ToolCall, timeout: int = 30) -> ToolResult:
        """
        Выполняем инструмент.
        
        Типы инструментов:
        1. HTTP API - отправляем POST запрос
        2. Database - выполняем SQL query
        3. n8n workflow - триггер через webhook
        """
        try:
            # Получаем конфигурацию инструмента из БД
            tool_config = await self._get_tool_config(tool_call.tool_name)
            
            if tool_config['type'] == 'http_api':
                result = await self._execute_http(tool_config, tool_call.parameters)
            elif tool_config['type'] == 'n8n_workflow':
                result = await self._execute_n8n(tool_config, tool_call.parameters)
            else:
                raise ValueError(f"Unknown tool type: {tool_config['type']}")
            
            return ToolResult(
                tool_name=tool_call.tool_name,
                result=result
            )
        
        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=tool_call.tool_name,
                result={},
                error="Tool execution timeout"
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_call.tool_name,
                result={},
                error=str(e)
            )
    
    async def _execute_http(self, config: dict, params: dict) -> dict:
        """Выполняем HTTP API call"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {config['api_key']}"
        }
        
        async with self.http_client.post(
            config['endpoint_url'],
            json=params,
            headers=headers,
            timeout=30
        ) as resp:
            return await resp.json()
    
    async def _execute_n8n(self, config: dict, params: dict) -> dict:
        """Выполняем n8n workflow через webhook"""
        async with self.http_client.post(
            config['webhook_url'],
            json={
                'org_id': self.org_id,
                **params
            }
        ) as resp:
            return await resp.json()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def prewarm_proc(proc: JobContext):
    """Прогрев - запускается перед обработкой звонка"""
    await proc.download_files()

async def entrypoint(ctx: JobContext):
    """Main entry point для обработки звонка"""
    
    # Получаем конфигурацию агента
    agent_id = ctx.job.metadata.get('agent_id')
    agent_config = await get_agent_config(agent_id)
    
    # Создаем и запускаем оркестратор
    orchestrator = VoiceAgentOrchestrator(ctx, agent_config)
    await orchestrator.run()

# Регистрируем функции в LiveKit
agents.run_app(
    agents.ServerOptions(
        auth_token="...",
        url="...",
        ws_url="..."
    ),
    prewarm_proc=prewarm_proc,
    entrypoint=entrypoint
)
```

### 4. Call Management Service (Node.js)

```javascript
// services/call-management/src/index.ts

import express from 'express';
import { WebSocketServer } from 'ws';
import { EventEmitter } from 'events';
import { AccessToken } from 'livekit-server-sdk';
import { Kafka } from 'kafkajs';
import { createClient } from '@supabase/supabase-js';

// ============================================================================
// CALL MANAGEMENT SERVICE
// ============================================================================

class CallManagementService extends EventEmitter {
  private livekit: LiveKitClient;
  private kafka: KafkaClient;
  private db: SupabaseClient;
  private activeCalls: Map<string, CallSession> = new Map();
  private wsConnections: Map<string, WebSocket> = new Map();

  constructor() {
    super();
    this.livekit = new LiveKitClient(process.env.LIVEKIT_API_KEY);
    this.kafka = new Kafka({
      clientId: 'call-management',
      brokers: process.env.KAFKA_BROKERS.split(','),
    });
    this.db = createClient(
      process.env.DATABASE_URL,
      process.env.DATABASE_KEY
    );
  }

  /**
   * SCENARIO 1: Пользователь звонит на номер агента
   * 
   * Flow:
   * 1. SIP INVITE попадает на LiveKit через MTS Exolve trunk
   * 2. Мы создаем room в LiveKit
   * 3. Генерируем token для агента
   * 4. Отправляем агенту для подключения
   * 5. Публикуем call.initiated event
   */
  async handleIncomingCall(sipInvite: SIPInvite) {
    const callId = generateUUID();
    const phoneNumber = sipInvite.requestUri.userPart; // +71234567890

    logger.info(`📞 Incoming call to ${phoneNumber}, callId: ${callId}`);

    try {
      // 1. Получаем конфигурацию агента по номеру
      const agentConfig = await this.db
        .from('phone_numbers')
        .select('agents(*)')
        .eq('number', phoneNumber)
        .single();

      if (!agentConfig) {
        logger.warn(`No agent configured for ${phoneNumber}`);
        // Отправляем 404 или стандартный greeting
        sipInvite.reply(404, 'Not Found');
        return;
      }

      const agent = agentConfig.agents;
      const orgId = agent.org_id;

      // 2. Проверяем баланс организации
      const balance = await this.db
        .from('balances')
        .select('balance_kopecks')
        .eq('org_id', orgId)
        .single();

      if (balance.balance_kopecks <= 0) {
        logger.warn(`No balance for org ${orgId}`);
        await sipInvite.reply(486, 'Busy Here'); // Занято
        // Публикуем событие
        await this.publishEvent('billing.call_rejected', {
          call_id: callId,
          org_id: orgId,
          reason: 'no_balance',
        });
        return;
      }

      // 3. Создаем room в LiveKit
      const room = await this.livekit.createRoom({
        name: `call-${callId}`,
        maxParticipants: 2, // Пользователь + агент
        emptyTimeout: 300, // Удалить room через 5 минут если пусто
      });

      // 4. Создаем объект сессии
      const session: CallSession = {
        callId,
        orgId,
        agentId: agent.id,
        phoneNumber,
        direction: 'inbound',
        sipInvite,
        likeKitRoom: room.name,
        startTime: new Date(),
        status: 'ringing',
        transcripts: [],
        sentimentScore: 0.5, // Нейтральный в начале
      };

      this.activeCalls.set(callId, session);

      // 5. Отправляем SIP 100 Trying, потом 180 Ringing
      sipInvite.reply(100, 'Trying');
      sipInvite.reply(180, 'Ringing');

      // 6. Генерируем токены для обеих сторон
      const userToken = await this.generateLiveKitToken({
        room: room.name,
        identity: `user-${callId}`,
        grants: {
          canPublish: true,
          canPublishData: true,
          canSubscribe: true,
        },
      });

      const agentToken = await this.generateLiveKitToken({
        room: room.name,
        identity: agent.id,
        grants: {
          canPublish: true,
          canPublishData: true,
          canSubscribe: true,
        },
      });

      // 7. Публикуем событие в Kafka (все сервисы подписаны)
      await this.publishEvent('call.initiated', {
        call_id: callId,
        org_id: orgId,
        agent_id: agent.id,
        from_number: sipInvite.from.uri.user,
        to_number: phoneNumber,
        direction: 'inbound',
        livekit_room: room.name,
        agent_token, // Отправляем токен агенту
        timestamp: new Date().toISOString(),
      });

      // 8. Сохраняем в БД
      await this.db.from('calls').insert({
        id: callId,
        org_id: orgId,
        agent_id: agent.id,
        phone_id: agentConfig.phone_numbers[0].id,
        from_number: sipInvite.from.uri.user,
        to_number: phoneNumber,
        direction: 'inbound',
        status: 'ringing',
        started_at: new Date().toISOString(),
        livekit_room: room.name,
      });

      logger.info(`✅ Call ${callId} created, waiting for agent connection`);
    } catch (error) {
      logger.error(`Error handling incoming call: ${error.message}`);
      sipInvite.reply(500, 'Server Internal Error');
    }
  }

  /**
   * SCENARIO 2: Агент подключился к room (через WebSocket)
   */
  async handleAgentConnected(callId: string, agentId: string) {
    const session = this.activeCalls.get(callId);
    if (!session) {
      logger.error(`Call ${callId} not found`);
      return;
    }

    logger.info(`👤 Agent ${agentId} connected to call ${callId}`);

    // Отправляем SIP 200 OK (принимаем звонок)
    session.sipInvite.reply(200, 'OK', {
      body: `v=0\r\no=- ${Date.now()} 0 IN IP4 127.0.0.1\r\n...`, // SDP
    });

    session.status = 'connected';
    session.connectTime = new Date();

    // Публикуем событие
    await this.publishEvent('call.agent_assigned', {
      call_id: callId,
      agent_id: agentId,
      timestamp: new Date().toISOString(),
    });

    // Обновляем статус в БД
    await this.db
      .from('calls')
      .update({ status: 'connected' })
      .eq('id', callId);
  }

  /**
   * SCENARIO 3: Пользователь закончил звонок
   */
  async handleCallEnded(callId: string, durationSeconds: number) {
    const session = this.activeCalls.get(callId);
    if (!session) {
      logger.warn(`Call ${callId} already cleaned up`);
      return;
    }

    logger.info(`📵 Call ${callId} ended after ${durationSeconds}s`);

    session.status = 'ended';
    session.endTime = new Date();
    session.duration = durationSeconds;

    // Получаем запись из LiveKit
    const recordings = await this.livekit.getRoomRecordings(session.likeKitRoom);
    const recordingUrl = recordings.length > 0 ? recordings[0].storagePath : null;

    // Публикуем событие
    await this.publishEvent('call.ended', {
      call_id: callId,
      org_id: session.orgId,
      agent_id: session.agentId,
      duration: durationSeconds,
      recording_url: recordingUrl,
      sentiment: session.sentimentScore > 0.6 ? 'positive' : 'negative',
      timestamp: new Date().toISOString(),
    });

    // Обновляем БД
    await this.db.from('calls').update({
      status: 'ended',
      ended_at: new Date().toISOString(),
      duration_seconds: durationSeconds,
      recording_url: recordingUrl,
      billing_seconds: durationSeconds, // Для начисления
    }).eq('id', callId);

    // Удаляем из активных
    this.activeCalls.delete(callId);

    // Удаляем room из LiveKit
    await this.livekit.deleteRoom(session.likeKitRoom);
  }

  /**
   * SCENARIO 4: Обработка VAD (Voice Activity Detection)
   * 
   * Если пользователь молчит более 5 сек, закрываем звонок
   */
  private startVADTimer(callId: string) {
    const session = this.activeCalls.get(callId);
    if (!session) return;

    const timer = setTimeout(async () => {
      logger.warn(`VAD timeout for call ${callId}`);
      await this.handleCallEnded(callId, Math.floor((Date.now() - session.startTime.getTime()) / 1000));
    }, 5000); // 5 секунд молчания

    session.vadTimer = timer;
  }

  /**
   * SCENARIO 5: Обработка interruption
   * 
   * Если пользователь говорит во время ответа агента
   */
  async handleUserInterruption(callId: string) {
    const session = this.activeCalls.get(callId);
    if (!session) return;

    logger.info(`🔔 User interrupted agent on call ${callId}`);
    session.interruptCount = (session.interruptCount || 0) + 1;

    // Публикуем событие (агент может обработать)
    await this.publishEvent('call.interrupted', {
      call_id: callId,
      interrupt_count: session.interruptCount,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Генерируем JWT токен для LiveKit
   */
  private async generateLiveKitToken(options: TokenOptions): Promise<string> {
    const token = new AccessToken(
      process.env.LIVEKIT_API_KEY,
      process.env.LIVEKIT_API_SECRET
    );

    token.identity = options.identity;
    token.addGrant(options.grants);
    token.name = options.identity;

    return token.toJwt();
  }

  /**
   * Публикуем события в Kafka
   */
  private async publishEvent(eventType: string, data: any) {
    const producer = this.kafka.producer();
    await producer.connect();

    await producer.send({
      topic: 'call-events', // Зависит от типа события
      messages: [
        {
          key: data.org_id, // Партиция по org_id для гарантии порядка
          value: JSON.stringify({
            type: eventType,
            data,
            timestamp: new Date().toISOString(),
          }),
        },
      ],
    });

    await producer.disconnect();
  }
}

// ============================================================================
// EXPRESS API
// ============================================================================

const app = express();
const callService = new CallManagementService();

// Webhook для входящих SIP вызовов
app.post('/webhooks/incoming-call', async (req, res) => {
  const sipInvite = parseSIPInvite(req.body);
  await callService.handleIncomingCall(sipInvite);
  res.json({ ok: true });
});

// WebSocket для real-time обновлений
const wss = new WebSocketServer({ noServer: true });

wss.on('connection', async (ws, req) => {
  const callId = req.url.split('/')[2]; // /ws/{callId}
  const agentId = req.headers['x-agent-id'];

  await callService.handleAgentConnected(callId, agentId);

  ws.on('message', async (data) => {
    const msg = JSON.parse(data);

    if (msg.type === 'vad_timeout') {
      const durationSeconds = Math.floor((Date.now() - session.startTime) / 1000);
      await callService.handleCallEnded(callId, durationSeconds);
    } else if (msg.type === 'user_interrupted') {
      await callService.handleUserInterruption(callId);
    }
  });
});

app.listen(3000, () => {
  logger.info('Call Management Service started on port 3000');
});
```

### 5. Billing Service (платежи и трекинг)

```javascript
// services/billing/src/index.ts

class BillingService {
  /**
   * СЦЕНАРИЙ 1: Звонок закончился, начисляем минуты
   */
  async onCallEnded(event: CallEndedEvent) {
    const { call_id, org_id, duration } = event;

    // 1. Получаем тариф организации
    const org = await db
      .from('organizations')
      .select('plan')
      .eq('id', org_id)
      .single();

    // Тарифы (руб/минута)
    const rates = {
      free: 0, // Бесплатный, но лимит 100 мин/месяц
      pro: 10, // 10 руб/минута
      enterprise: 5, // 5 руб/минута (оптом дешевле)
    };

    const rate = rates[org.plan];
    const minutes = Math.ceil(duration / 60);
    const cost = minutes * rate * 100; // в копейках

    // 2. Проверяем месячный лимит
    const usage = await this.getMonthlyUsage(org_id);
    if (org.plan === 'free' && usage + minutes > 100) {
      // Отклоняем звонок при перевышении лимита
      await db.from('calls').update({
        status: 'rejected',
        cost_kopecks: 0,
      }).eq('id', call_id);

      await publishEvent('billing.call_rejected', {
        call_id,
        reason: 'monthly_limit_exceeded',
      });
      return;
    }

    // 3. Вычитаем из баланса
    await db
      .from('billing_transactions')
      .insert({
        org_id,
        call_id,
        amount_kopecks: cost,
        type: 'debit', // Списание за звонок
        status: 'completed',
        description: `Call ${call_id}: ${minutes} min @ ${rate} ₽/min`,
      });

    // Обновляем баланс (денормализованная таблица для скорости)
    await db.rpc('deduct_balance', {
      p_org_id: org_id,
      p_amount: cost,
    });

    // 4. Обновляем запись звонка
    await db.from('calls').update({
      cost_kopecks: cost,
    }).eq('id', call_id);

    logger.info(`💸 Deducted ${cost} kopecks from org ${org_id}`);

    // 5. Проверяем, не закончился ли баланс
    const balance = await db
      .from('balances')
      .select('balance_kopecks')
      .eq('org_id', org_id)
      .single();

    if (balance.balance_kopecks < 1000) {
      // Менее 10 рублей
      await publishEvent('billing.balance_low', {
        org_id,
        balance_kopecks: balance.balance_kopecks,
        threshold: 1000,
      });

      // Отправляем уведомление админу
      await this.notifyAdmin(org_id, `Низкий баланс: ${balance.balance_kopecks / 100} ₽`);
    }
  }

  /**
   * СЦЕНАРИЙ 2: YooKassa webhook (платеж получен)
   */
  async onPaymentReceived(yookassaEvent: YookassaEvent) {
    const { payment_id, amount, status } = yookassaEvent;

    if (status !== 'succeeded') {
      logger.warn(`Payment ${payment_id} not succeeded`);
      return;
    }

    // Найдем транзакцию
    const transaction = await db
      .from('billing_transactions')
      .select('*')
      .eq('yookassa_payment_id', payment_id)
      .single();

    if (!transaction) {
      logger.error(`Transaction not found for payment ${payment_id}`);
      return;
    }

    const org_id = transaction.org_id;
    const amount_kopecks = Math.round(amount * 100);

    // 1. Обновляем статус транзакции
    await db
      .from('billing_transactions')
      .update({
        status: 'completed',
        updated_at: new Date().toISOString(),
      })
      .eq('id', transaction.id);

    // 2. Пополняем баланс
    await db.rpc('add_balance', {
      p_org_id: org_id,
      p_amount: amount_kopecks,
    });

    logger.info(`✅ Balance added: ${amount_kopecks} kopecks to org ${org_id}`);

    // 3. Публикуем событие
    await publishEvent('billing.payment_received', {
      org_id,
      amount_kopecks,
      payment_id,
      timestamp: new Date().toISOString(),
    });

    // 4. Отправляем уведомление пользователю
    await this.notifyUserOfPayment(org_id, amount_kopecks);
  }

  /**
   * СЦЕНАРИЙ 3: Инициация платежа (создание платежа в YooKassa)
   */
  async initiatePayment(
    org_id: string,
    amount_rubles: number,
    paymentMethod: 'card' | 'sbp' | 'yandex_kassa'
  ): Promise<PaymentUrl> {
    // 1. Создаем платеж в YooKassa
    const yookassa = new YooKassa({
      shopId: process.env.YOOKASSA_SHOP_ID,
      secretKey: process.env.YOOKASSA_SECRET_KEY,
    });

    const payment = await yookassa.createPayment({
      amount: {
        value: amount_rubles.toString(),
        currency: 'RUB',
      },
      confirmation: {
        type: 'redirect',
        return_url: `https://app.voiceagent.ru/billing/success`,
      },
      metadata: {
        org_id,
        type: 'balance_topup',
      },
      description: `Balance replenishment for ${amount_rubles} RUB`,
    });

    // 2. Сохраняем транзакцию в БД (до платежа - статус pending)
    await db.from('billing_transactions').insert({
      org_id,
      amount_kopecks: Math.round(amount_rubles * 100),
      type: 'credit', // Пополнение
      status: 'pending', // Ждем подтверждения
      yookassa_payment_id: payment.id,
      description: `Payment via ${paymentMethod}`,
    });

    logger.info(`💳 Payment initiated: ${payment.id}`);

    return {
      payment_id: payment.id,
      confirmation_url: payment.confirmation.confirmation_url,
    };
  }

  /**
   * Запрос текущего использования за месяц
   */
  async getMonthlyUsage(org_id: string): Promise<number> {
    const firstDayOfMonth = new Date();
    firstDayOfMonth.setDate(1);
    firstDayOfMonth.setHours(0, 0, 0, 0);

    const result = await db
      .from('calls')
      .select('duration_seconds')
      .eq('org_id', org_id)
      .gte('created_at', firstDayOfMonth.toISOString())
      .eq('status', 'ended');

    const totalSeconds = result.data.reduce((sum, call) => sum + (call.duration_seconds || 0), 0);
    return Math.ceil(totalSeconds / 60);
  }

  /**
   * Уведомить админа о событиях
   */
  private async notifyAdmin(org_id: string, message: string) {
    const admin = await db
      .from('users')
      .select('email')
      .eq('org_id', org_id)
      .eq('role', 'admin')
      .single();

    if (admin) {
      await sendEmail({
        to: admin.email,
        subject: 'Уведомление от Voice Agent Platform',
        body: message,
      });
    }
  }
}

// Express endpoint для инициации платежа
app.post('/api/billing/create-payment', async (req, res) => {
  const { org_id, amount_rubles, payment_method } = req.body;

  const billing = new BillingService();
  const payment = await billing.initiatePayment(org_id, amount_rubles, payment_method);

  res.json(payment);
});

// Webhook от YooKassa
app.post('/webhooks/yookassa', express.text(), async (req, res) => {
  const event = JSON.parse(req.body);

  if (event.type === 'payment.succeeded') {
    await billingService.onPaymentReceived(event.object);
  }

  res.json({ ok: true });
});
```

---

## 🚀 РАЗВЕРТЫВАНИЕ

### Локальная разработка (Docker Compose)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: voice_agent
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Kafka + Zookeeper
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"

  # LiveKit
  livekit:
    image: livekit/livekit-server:latest
    ports:
      - "7880:7880"
      - "7881:7881"
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml

  # n8n (для workflows)
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      DB_TYPE: postgres
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_USER: postgres
      DB_POSTGRESDB_PASSWORD: dev_password
      DB_POSTGRESDB_DATABASE: n8n

  # Backend (Next.js)
  backend:
    build: ./apps/web
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://postgres:dev_password@postgres:5432/voice_agent
      REDIS_URL: redis://redis:6379
      KAFKA_BROKERS: kafka:29092
    depends_on:
      - postgres
      - redis
      - kafka

  # Voice Agent Service (Python)
  agent-service:
    build: ./apps/agent
    environment:
      DATABASE_URL: postgresql://postgres:dev_password@postgres:5432/voice_agent
      LIVEKIT_URL: ws://livekit:7880
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY}
    depends_on:
      - postgres
      - livekit

volumes:
  postgres_data:
```

### Production Deployment (Kubernetes)

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: voice-agent-prod

---
# kubernetes/postgres.yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: voice-agent-prod
type: Opaque
stringData:
  password: ${PROD_POSTGRES_PASSWORD}

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: voice-agent-prod
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: voice_agent
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 100Gi

---
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: voice-agent-prod
spec:
  replicas: 3 # Высокая доступность
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/voiceagent/backend:latest
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          value: redis://redis:6379

---
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: voice-agent-ingress
  namespace: voice-agent-prod
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - app.voiceagent.ru
    secretName: voice-agent-tls
  rules:
  - host: app.voiceagent.ru
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 3000
```

---

## 📊 МОНИТОРИНГ И НАБЛЮДАЕМОСТЬ

```yaml
# monitoring/prometheus.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['localhost:3000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']

  - job_name: 'kafka'
    static_configs:
      - targets: ['localhost:9092']

# Alerts
groups:
  - name: VoiceAgent
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
      for: 5m
      annotations:
        summary: "High error rate detected"

    - alert: LowBalance
      expr: balance_kopecks < 10000
      annotations:
        summary: "Organization has low balance"

    - alert: CallLatencyHigh
      expr: call_latency_ms > 500
      for: 10m
      annotations:
        summary: "Call latency is high"
```

---

## 📅 ДОРОЖНАЯ КАРТА

### Phase 0: Setup (1 неделя)
- [ ] Initialize Next.js 15 + monorepo structure
- [ ] Setup PostgreSQL (Neon.tech)
- [ ] BetterAuth integration
- [ ] Basic Docker Compose
- [ ] GitHub Actions CI/CD

### Phase 1: Foundation (2-3 недели)
- [ ] Database schema migration (Drizzle)
- [ ] API Gateway + routes
- [ ] Real-time dashboard (WebSocket)
- [ ] Landing page

### Phase 2: Voice Core (3 недели)
- [ ] Python Agent service
- [ ] LiveKit integration
- [ ] OpenAI API integration
- [ ] Deepgram STT
- [ ] ElevenLabs TTS
- [ ] MTS Exolve SIP trunk

### Phase 3: Billing (2 недели)
- [ ] YooKassa integration
- [ ] Balance tracking
- [ ] Invoice generation
- [ ] Usage analytics

### Phase 4: Production (2 недели)
- [ ] Kubernetes deployment
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Error tracking (Sentry)
- [ ] Load testing
- [ ] Security audit

---

## ✅ ИТОГ

Это **production-ready архитектура** для enterprise Voice Agent Platform. Ключевые преимущества:

✨ **Event-driven** - асинхронная коммуникация, масштабируемость  
✨ **Multi-tenant** - безопасная изоляция данных  
✨ **Low-latency** - <300ms end-to-end  
✨ **Resilient** - graceful degradation, fallbacks  
✨ **Monetizable** - интегрированная биллинговая система  
✨ **Extensible** - простое добавление новых инструментов через n8n  

Архитектура готова к развертыванию на AWS/GCP/Azure.
