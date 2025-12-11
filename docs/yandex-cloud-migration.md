# Миграция голосового агента в Yandex Cloud

## Обзор необходимых сервисов

Для переселения агента в Yandex Cloud нужны следующие разделы документации:

### 1. SpeechKit — Распознавание и синтез речи

**Документация:** `ru/speechkit/`

#### Ключевые разделы:

| Раздел | Путь | Назначение |
|--------|------|------------|
| **Потоковое распознавание** | `stt/streaming.md` | Real-time STT для голосового агента |
| **API v3 gRPC** | `stt-v3/api-ref/grpc/` | Современный API для распознавания |
| **Синтез речи API v3** | `tts-v3/api-ref/grpc/` | TTS для ответов агента |
| **Python SDK** | `sdk/python/` | Готовая библиотека `yandex-speechkit` |
| **Аутентификация** | `concepts/auth.md` | IAM-токены и API-ключи |
| **Интеграция телефонии** | `concepts/ivr-integration.md` | MRCP, Asterisk, Freeswitch |

#### Замена текущих сервисов:

| Текущий сервис | Yandex Cloud замена |
|----------------|---------------------|
| Deepgram STT | SpeechKit STT (API v3) |
| ElevenLabs TTS | SpeechKit TTS (API v3) |

#### Особенности SpeechKit:

- **Потоковый режим**: gRPC bidirectional streaming
- **Макс. длительность сессии**: 5 минут
- **Макс. размер данных**: 10 МБ за сессию
- **Поддержка языков**: русский, английский, и др.
- **VAD**: встроенное определение конца фразы (EOU)

### 2. YandexGPT — LLM для агента

**Документация:** `ru/foundation-models/`

#### Ключевые разделы:

| Раздел | Путь | Назначение |
|--------|------|------------|
| **Обзор YandexGPT** | `concepts/yandexgpt/` | Модели и возможности |
| **API** | `text-generation/api-ref/` | REST и gRPC API |
| **Промпты** | `operations/yandexgpt/` | Работа с промптами |
| **Embeddings** | `concepts/embeddings.md` | Для RAG в будущем |

#### Замена:

| Текущий сервис | Yandex Cloud замена |
|----------------|---------------------|
| OpenAI GPT-4o-mini | YandexGPT Pro/Lite |

#### Модели YandexGPT:

- **YandexGPT Lite** — быстрый, дешёвый
- **YandexGPT Pro** — качественнее, дороже
- **YandexGPT Pro 32k** — большой контекст

### 3. Compute Cloud — Хостинг агента

**Документация:** `ru/compute/`

#### Варианты деплоя:

| Вариант | Документация | Когда использовать |
|---------|--------------|-------------------|
| **VM** | `compute/quickstart/` | Простой деплой, полный контроль |
| **Container Registry + VM** | `container-registry/` | Docker-образы |
| **Serverless Containers** | `serverless-containers/` | Автоскейлинг, pay-per-use |

### 4. Дополнительные сервисы

| Сервис | Документация | Назначение |
|--------|--------------|------------|
| **IAM** | `ru/iam/` | Управление доступом, сервисные аккаунты |
| **VPC** | `ru/vpc/` | Сети, подсети, NAT |
| **Object Storage** | `ru/storage/` | Хранение аудио, логов |
| **Monitoring** | `ru/monitoring/` | Метрики и алерты |
| **Logging** | `ru/logging/` | Централизованные логи |

---

## Переменные окружения для Yandex Cloud

```env
# SpeechKit
YC_SPEECHKIT_API_KEY=<api-key>
# или
YC_IAM_TOKEN=<iam-token>
YC_FOLDER_ID=<folder-id>

# YandexGPT
YC_GPT_API_KEY=<api-key>
YC_GPT_MODEL_URI=gpt://<folder-id>/yandexgpt-lite

# Общие
YC_SERVICE_ACCOUNT_KEY_FILE=/path/to/key.json
```

---

## Архитектура интеграции

```
┌─────────────────────────────────────────────────────────────┐
│                     Yandex Cloud                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  SpeechKit  │    │  YandexGPT  │    │   Compute   │     │
│  │    STT      │    │    LLM      │    │     VM      │     │
│  │    TTS      │    │             │    │   (Agent)   │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                     ┌──────┴──────┐                         │
│                     │   LiveKit   │                         │
│                     │   Server    │                         │
│                     └──────┬──────┘                         │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │   МТС Exolve    │
                    │   SIP Trunk     │
                    └─────────────────┘
```

---

## План миграции

### Фаза 1: Подготовка
1. Создать аккаунт Yandex Cloud
2. Создать каталог (folder)
3. Создать сервисный аккаунт с ролями:
   - `ai.speechkit-stt.user`
   - `ai.speechkit-tts.user`
   - `ai.languageModels.user`
4. Получить API-ключи или настроить IAM

### Фаза 2: Интеграция SpeechKit
1. Установить `yandex-speechkit` SDK
2. Создать плагины для LiveKit Agents:
   - `YandexSTT` — замена Deepgram
   - `YandexTTS` — замена ElevenLabs
3. Протестировать потоковое распознавание

### Фаза 3: Интеграция YandexGPT
1. Создать адаптер для OpenAI-совместимого API
2. Или использовать нативный gRPC API
3. Настроить промпты под YandexGPT

### Фаза 4: Деплой
1. Создать Docker-образ
2. Загрузить в Container Registry
3. Развернуть на Compute VM или Serverless

---

## Ссылки на документацию

### Обязательные к изучению:
- https://yandex.cloud/ru/docs/speechkit/stt/streaming
- https://yandex.cloud/ru/docs/speechkit/sdk/python/
- https://yandex.cloud/ru/docs/foundation-models/
- https://yandex.cloud/ru/docs/iam/concepts/authorization/api-key

### GitHub репозитории:
- https://github.com/yandex-cloud/cloudapi — Proto-файлы для gRPC
- https://github.com/yandex-cloud/docs — Исходники документации
- https://pypi.org/project/yandex-speechkit/ — Python SDK

### Примеры кода:
- `ru/speechkit/stt/api/streaming-examples-v3.md`
- `ru/speechkit/stt/api/microphone-streaming.md`
- `ru/speechkit/tts/api/tts-examples-v3.md`
