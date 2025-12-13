# Промпт для Gemini — UI Design Voice AI Dashboard

Ты — senior UI/UX дизайнер, специализирующийся на дашбордах мониторинга и data visualization. 

Создай дизайн современного, минималистичного дашборда для мониторинга Voice AI платформы.

## Контекст

Это дашборд для мониторинга голосового AI-агента, который принимает телефонные звонки через SIP и отвечает с помощью LLM. Платформа состоит из:
- **LiveKit Server** — real-time коммуникации, WebRTC
- **SIP телефония** — входящие/исходящие звонки через МТС Exolve
- **Voice Agent** — STT → LLM → TTS pipeline (Yandex SpeechKit + YandexGPT)

## Ключевые метрики для отображения

### 1. Overview (главный экран)
- Статус системы (зелёный/жёлтый/красный индикаторы)
- Активные звонки сейчас (большое число)
- Звонки за сегодня / неделю / месяц (с трендом)
- Uptime % всех сервисов
- Критические алерты (badge с количеством)

### 2. Voice Quality
- **TTFW (Time To First Word)** — главная метрика UX, должна быть <1.5 сек, показать gauge
- Packet Loss % (цель <1%)
- Jitter (цель <30ms)
- RTT (цель <150ms)
- Audio bitrate (график)

### 3. Agent Performance
- STT Latency (распознавание речи) — histogram
- LLM Latency (ответ модели) — histogram
- TTS Latency (синтез речи) — histogram
- Conversation turns per minute
- Tool calls (какие инструменты вызывает агент, pie chart)

### 4. SIP Telephony
- Calls per hour (area chart)
- Success rate % (gauge)
- Average call duration
- Error codes distribution (486 Busy, 500 Error, etc.)

### 5. Infrastructure
- CPU / RAM / Disk usage для каждого сервера (progress bars)
- Network I/O (sparklines)
- Docker container status (status dots)

## Требования к дизайну

### Стиль
- **Dark theme** (основной) с возможностью light theme
- Цветовая схема:
  - Background: `#0f172a` (slate-900)
  - Cards: `#1e293b` (slate-800)
  - Accent cyan: `#06b6d4`
  - Success green: `#22c55e`
  - Warning yellow: `#eab308`
  - Error red: `#ef4444`
- Минималистичный, без лишних декораций
- Вдохновение: Linear, Vercel Dashboard, Datadog, Grafana Cloud

### Компоненты
- **Stat Cards** — большие числа с иконкой и трендом (↑↓)
- **Sparkline** графики для трендов в карточках
- **Gauge/Donut** для процентов (TTFW, Success Rate)
- **Area/Line charts** для timeline данных
- **Status indicators** — цветные точки для статуса сервисов
- **Alert badges** — красные/жёлтые badges с числом
- **Progress bars** — для CPU/RAM/Disk

### Типографика
- Шрифт: **Inter** или SF Pro
- Большие числа: 48-64px, font-weight 700
- Метки: 12-14px, font-weight 500
- Хорошая читаемость на тёмном фоне (contrast ratio >4.5:1)

### Layout
- Responsive grid (12 columns)
- **Sidebar** слева с навигацией (иконки + текст)
- **Header** с логотипом, поиском, notifications, профилем
- **Main content** — grid карточек с метриками
- Breakpoints: mobile (1 col), tablet (2 col), desktop (3-4 col)

## Навигация (Sidebar)

```
🏠 Overview
📞 Calls
🎙️ Voice Quality  
🤖 Agent
🖥️ Infrastructure
🔔 Alerts
⚙️ Settings
```

## Deliverables

1. **Wireframe** главного Overview экрана (low-fidelity)
2. **High-fidelity дизайн** 3 экранов:
   - Overview
   - Voice Quality
   - Agent Performance
3. **Component Library**:
   - Stat Card (с вариантами)
   - Chart Card
   - Status Badge
   - Alert Item
   - Navigation Item
4. **Design Tokens**:
   - Цветовая палитра
   - Типографика
   - Spacing scale
   - Border radius

## Технический контекст

UI будет реализован на:
- **React 18** + TypeScript
- **Tailwind CSS** для стилей
- **Tremor** или **Recharts** для графиков
- **Lucide Icons** для иконок

Данные приходят из Prometheus через REST API. Real-time обновления через polling каждые 15 секунд.

## Примеры данных для макетов

```
Active Calls: 3
Calls Today: 127
Success Rate: 94.2%
TTFW P95: 1.2s
Avg Call Duration: 2m 34s

Servers:
- LiveKit: 🟢 Online, CPU 45%, RAM 62%
- Agent: 🟢 Online, CPU 23%, RAM 41%
- Monitoring: 🟢 Online

Recent Alerts:
- ⚠️ High packet loss on LiveKit (2.3%) - 5 min ago
- ✅ Agent recovered from high latency - 1 hour ago
```

---

Начни с wireframe Overview экрана, затем покажи детальный high-fidelity дизайн.
