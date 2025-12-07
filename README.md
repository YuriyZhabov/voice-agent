# Voice Agent MVP

Голосовой AI-агент на базе LiveKit Agents SDK для обработки входящих телефонных звонков.

## Возможности

- Приём входящих звонков через SIP (МТС Exolve)
- Распознавание речи (Deepgram Nova-3)
- Генерация ответов (OpenAI GPT-4o-mini через CometAPI)
- Синтез речи (ElevenLabs)
- Определение голосовой активности (Silero VAD)
- Автоматическое завершение при тишине
- Обработка прерываний пользователем

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Заполните .env своими API ключами
```

### 3. Проверка API

```bash
python -m agent.api_health
```

### 4. Запуск агента

```bash
python -m agent.main dev
```

## Переменные окружения

### LiveKit (обязательно)
| Переменная | Описание |
|------------|----------|
| `LIVEKIT_URL` | WebSocket URL проекта LiveKit |
| `LIVEKIT_API_KEY` | API ключ LiveKit |
| `LIVEKIT_API_SECRET` | API секрет LiveKit |

### STT - Deepgram (обязательно)
| Переменная | Описание |
|------------|----------|
| `DEEPGRAM_API_KEY` | API ключ Deepgram |

### LLM - OpenAI (обязательно)
| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OPENAI_API_KEY` | API ключ OpenAI/CometAPI | - |
| `OPENAI_BASE_URL` | Base URL API | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Модель LLM | `gpt-4o-mini` |

### TTS - ElevenLabs (обязательно)
| Переменная | Описание |
|------------|----------|
| `ELEVEN_API_KEY` | API ключ ElevenLabs |
| `ELEVENLABS_VOICE_ID` | ID голоса |

### SIP Телефония (опционально)
| Переменная | Описание |
|------------|----------|
| `SIP_TRUNK_ID` | ID SIP trunk в LiveKit |
| `SIP_PHONE_NUMBER` | Номер телефона |
| `AGENT_NAME` | Имя агента для dispatch |

### МТС Exolve (опционально)
| Переменная | Описание |
|------------|----------|
| `EXOLVE_API_KEY` | API ключ Exolve |
| `EXOLVE_SIP_RESOURCE_ID` | ID SIP ресурса |
| `EXOLVE_PHONE_NUMBER` | Номер телефона |
| `EXOLVE_SIP_USERNAME` | SIP username |
| `EXOLVE_SIP_DOMAIN` | SIP домен |

### Таймауты
| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SILENCE_TIMEOUT_SECONDS` | Таймаут тишины | `60` |
| `TOOL_TIMEOUT_SECONDS` | Таймаут инструментов | `30` |

## Настройка SIP телефонии

### LiveKit SIP

1. Получите SIP URI в настройках проекта LiveKit Cloud
2. Создайте Inbound Trunk:
   ```bash
   python -m agent.sip_setup --create-trunk "MTS Exolve" "+79587401087"
   ```
3. Создайте Dispatch Rule:
   ```bash
   python -m agent.sip_setup --create-rule "voice-agent-mvp"
   ```
4. Проверьте конфигурацию:
   ```bash
   python -m agent.sip_setup --list
   ```

### МТС Exolve

1. Зарегистрируйтесь на https://dev.exolve.ru
2. Получите API ключ
3. **Важно**: Для переадресации на внешний SIP требуется подписание договора
4. После подписания договора настройте переадресацию на LiveKit SIP URI

## Тестирование

### Запуск unit-тестов

```bash
pytest tests/ -v
```

### Тестирование голосового агента

#### Вариант 1: Исходящий звонок (SIP Outbound)

1. Создайте Outbound Trunk (если ещё не создан):
   ```bash
   python -m agent.sip_setup --create-outbound --name "MTS Exolve Outbound" \
     --address "sip.exolve.ru" --number "+79587401087" \
     --username "883140776944348" --password "YOUR_PASSWORD"
   ```

2. Запустите агента в первом терминале:
   ```bash
   python -m agent.main dev
   ```

3. Сделайте тестовый звонок во втором терминале:
   ```bash
   python -m agent.test_call +79001234567
   ```

#### Вариант 2: LiveKit Playground

1. Запустите агента:
   ```bash
   python -m agent.main dev
   ```

2. Откройте [LiveKit Playground](https://cloud.livekit.io)
3. Подключитесь к комнате с именем `call-test`
4. Агент автоматически подключится и начнёт разговор

## Архитектура

```
agent/
├── main.py          # Точка входа, LiveKit Agent
├── config.py        # Конфигурация (Pydantic)
├── context.py       # Управление контекстом разговора
├── logger.py        # Структурированное логирование
├── api_health.py    # Проверка доступности API
├── sip_setup.py     # Утилиты настройки SIP
└── exolve_setup.py  # Утилиты настройки Exolve
```

## Лицензия

MIT
