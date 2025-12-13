# Monitoring Stack Specification

> Копия спецификации из `.kiro/specs/monitoring-stack/` для коммита в git

---

# Requirements Document

## Introduction

Система мониторинга для голосового агента и LiveKit инфраструктуры. Состоит из трёх компонентов:
1. **Prometheus** — сбор и хранение метрик в реальном времени
2. **Supabase** — хранение истории звонков, транскриптов, настроек
3. **VoxPulse UI** — кастомный React дашборд для визуализации

## Glossary

- **Monitoring_Stack**: Комплекс из Prometheus (метрики) + Supabase (данные) + VoxPulse (UI)
- **VoxPulse**: Кастомный React дашборд для мониторинга Voice AI (`site/`)
- **Supabase**: Backend-as-a-Service на базе PostgreSQL с REST API и Realtime
- **LiveKit_Server**: Self-hosted сервер для real-time коммуникаций на 158.160.55.228
- **Voice_Agent**: Python агент на базе LiveKit Agents SDK на 130.193.50.241
- **SIP_Service**: Компонент LiveKit для телефонии (входящие/исходящие звонки)
- **Prometheus**: Time-series база данных для хранения метрик
- **TTFW**: Time To First Word — время от конца речи пользователя до первого байта аудио от агента
- **RTT**: Round-Trip Time — время прохождения пакета туда и обратно

## Requirements Summary

| # | User Story | Key Criteria |
|---|------------|--------------|
| 1 | Сбор метрик | Prometheus scrape каждые 15s, retention 15 дней |
| 2 | LiveKit метрики | rooms, participants, packet loss, jitter, RTT |
| 3 | SIP метрики | calls total, active, success rate, duration |
| 4 | Agent метрики | STT/LLM/TTS latency, TTFW, tool calls |
| 5 | Infrastructure | CPU, RAM, Disk, Network, Docker |
| 6 | Алерты | CPU>80%, RAM>85%, Disk>80%, target down, packet loss>1% |
| 7 | Деплой | Docker Compose, Hostkey VPS, SSL |
| 8 | Безопасность | Auth required, env vars for credentials |
| 9 | Availability | Blackbox Exporter probes |
| 10 | История звонков | Supabase: calls, transcripts, tool_executions |
| 11 | Realtime | Supabase Realtime для live updates |
| 12 | VoxPulse деплой | Static build, env vars, Supabase Auth |

---

# Design Document

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VoxPulse UI (React)                            │
│                         voxpulse.agentio.pro (Vercel)                       │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│        Supabase Cloud         │   │     Hostkey VPS (Prometheus)  │
│  - PostgreSQL (calls, etc)    │   │  - Prometheus (9090)          │
│  - Realtime (WebSocket)       │   │  - Blackbox Exporter (9115)   │
│  - Auth                       │   │  - Nginx (443 HTTPS)          │
└───────────────────────────────┘   └───────────────────────────────┘
                                                    │
         ┌──────────────────────────────────────────┼────────────────┐
         │                                          │                │
         ▼                                          ▼                ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  LiveKit Server │  │   SIP Service   │  │   Voice Agent   │
│  158.160.55.228 │  │  158.160.55.228 │  │ 130.193.50.241  │
│   :7881/metrics │  │   :6789/metrics │  │   :8080/metrics │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Supabase Schema

```sql
CREATE TABLE calls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id TEXT UNIQUE NOT NULL,
  phone_number TEXT NOT NULL,
  direction TEXT CHECK (direction IN ('inbound', 'outbound')),
  status TEXT CHECK (status IN ('active', 'completed', 'failed', 'transferred')),
  start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  end_time TIMESTAMPTZ,
  duration_seconds INTEGER,
  room_name TEXT,
  agent_version TEXT
);

CREATE TABLE transcripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tool_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
  tool_name TEXT NOT NULL,
  parameters JSONB,
  result JSONB,
  success BOOLEAN DEFAULT TRUE,
  latency_ms INTEGER,
  executed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE alerts_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  severity TEXT CHECK (severity IN ('critical', 'warning', 'info')),
  service TEXT NOT NULL,
  message TEXT NOT NULL,
  triggered_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  acknowledged BOOLEAN DEFAULT FALSE
);
```

## UI Data Mapping

### Overview.tsx

| UI Элемент | Источник | Query |
|------------|----------|-------|
| Активные звонки | Prometheus | `livekit_sip_calls_active` |
| TTFW (Среднее) | Prometheus | `histogram_quantile(0.5, voice_agent_ttfw_seconds_bucket)` |
| Всего звонков (24ч) | Supabase | `SELECT COUNT(*) FROM calls WHERE start_time > NOW() - INTERVAL '24 hours'` |
| Ср. длительность | Supabase | `SELECT AVG(duration_seconds) FROM calls ...` |
| Объём звонков (график) | Prometheus | `livekit_sip_calls_total[24h]` |
| SIP ошибки | Prometheus | `sum by (code) (livekit_sip_errors_total)` |
| Статус сервисов | Prometheus | `up{job="..."}` + `probe_success` |
| Алерты | Supabase | `SELECT * FROM alerts_history ORDER BY triggered_at DESC` |

### VoiceQuality.tsx

| UI Элемент | Источник | Query |
|------------|----------|-------|
| TTFW (Hero) | Prometheus | `histogram_quantile(0.95, voice_agent_ttfw_seconds_bucket)` |
| Тренд TTFW | Prometheus | query_range, step=1m |
| Packet Loss | Prometheus | `avg(livekit_packet_loss_ratio) * 100` |
| Jitter | Prometheus | `avg(livekit_jitter_ms)` |
| RTT | Prometheus | `avg(livekit_rtt_ms)` |
| Детализация задержек | Prometheus | STT/LLM/TTS latency histograms |

### AgentPerformance.tsx

| UI Элемент | Источник | Query |
|------------|----------|-------|
| Ср. задержка | Prometheus | TTFW * 1000 (ms) |
| Ходов/мин | Prometheus | `rate(voice_agent_turns_total[5m]) * 60` |
| Tool calls % | Supabase | COUNT tool_executions / COUNT transcripts |
| Стек задержек | Prometheus | STT + LLM + TTS stacked |
| Top tools | Supabase | `SELECT tool_name, COUNT(*) ... GROUP BY tool_name` |

### Realtime Subscriptions

| Событие | Таблица | Действие |
|---------|---------|----------|
| Новый звонок | calls INSERT | Добавить в активные |
| Звонок завершён | calls UPDATE | Переместить в историю |
| Новый алерт | alerts_history INSERT | Toast notification |

### Polling Intervals

| Метрика | Интервал |
|---------|----------|
| Активные звонки | 5s |
| TTFW, Latency | 15s |
| Графики | 60s |

---

# Implementation Plan

## Серверы
- **Hostkey VPS**: Panel key `594862a1006eab7b-9439932ee9b3d751`
- **LiveKit**: 158.160.55.228
- **Agent**: 130.193.50.241
- **Supabase**: Cloud

## Tasks

1. **Настроить Supabase** — проект, схема, auth, realtime
2. **Подготовка Hostkey VPS** — SSH, Docker, DNS
3. **Создать deploy/monitoring** — docker-compose, prometheus.yml, blackbox.yml
4. **Node Exporter** — на LiveKit и Agent серверах
5. **Метрики в агенте** — prometheus_client, Supabase logging
6. **Checkpoint**
7. **VoxPulse UI** — Supabase client, Prometheus API, Auth, Realtime
8. **Деплой Prometheus** — на Hostkey VPS
9. **Деплой VoxPulse** — Vercel или Hostkey
10. **Checkpoint**
11. **Финальная настройка** — Alertmanager, проверка данных
12. **Final Checkpoint**

---

## Environment Variables

```bash
# VoxPulse
VITE_PROMETHEUS_URL=https://prometheus.agentio.pro
VITE_SUPABASE_URL=https://[project-id].supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...

# Agent
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```
