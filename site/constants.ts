import { Alert, CallMetric, LatencyData, ServiceStatus, MetricPoint } from './types';

export const ALERTS: Alert[] = [
  { id: '1', severity: 'critical', service: 'SIP Trunk Provider A', message: 'Высокая потеря пакетов (>5%)', timestamp: '2 мин назад' },
  { id: '2', severity: 'warning', service: 'LiveKit Edge 03', message: 'Загрузка CPU > 85%', timestamp: '15 мин назад' },
  { id: '3', severity: 'info', service: 'Voice Agent', message: 'Версия модели обновлена до v2.4.1', timestamp: '1 час назад' },
  { id: '4', severity: 'warning', service: 'STT Service', message: 'Скачок задержки в регионе US-EAST', timestamp: '3 часа назад' },
];

export const SERVICES: ServiceStatus[] = [
  { name: 'LiveKit Server', status: 'operational', uptime: '99.99%', latency: '45ms' },
  { name: 'SIP Gateway', status: 'operational', uptime: '99.95%', latency: '12ms' },
  { name: 'LLM Orchestrator', status: 'degraded', uptime: '98.50%', latency: '850ms' },
  { name: 'Redis Cache', status: 'operational', uptime: '100%', latency: '2ms' },
  { name: 'Postgres DB', status: 'operational', uptime: '99.99%', latency: '15ms' },
];

// Generate mock data for charts
const now = new Date();
export const LATENCY_HISTORY: LatencyData[] = Array.from({ length: 24 }, (_, i) => {
  const t = new Date(now.getTime() - (23 - i) * 300000); // 5 min intervals
  const stt = 150 + Math.random() * 50;
  const llm = 600 + Math.random() * 300 + (i === 18 ? 400 : 0); // Simulated spike
  const tts = 100 + Math.random() * 30;
  return {
    time: t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    stt: Math.round(stt),
    llm: Math.round(llm),
    tts: Math.round(tts),
    total: Math.round(stt + llm + tts),
  };
});

export const CALL_VOLUME: CallMetric[] = Array.from({ length: 24 }, (_, i) => {
  const t = new Date(now.getTime() - (23 - i) * 3600000); // 1 hour intervals
  const base = i > 8 && i < 20 ? 400 : 50; // Business hours
  const active = base + Math.random() * 100;
  const fail = active * (Math.random() * 0.05);
  return {
    time: t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    activeCalls: Math.round(active),
    failures: Math.round(fail),
  };
});

export const QUALITY_METRICS: MetricPoint[] = Array.from({ length: 20 }, (_, i) => ({
  time: `${i}м`,
  value: 0.8 + Math.random() * 1.5, // TTFW in seconds
}));

export const ERROR_DISTRIBUTION = [
  { name: '486 Занято', value: 120, fill: '#94a3b8' },
  { name: '404 Не найдено', value: 45, fill: '#64748b' },
  { name: '500 Ошибка сервера', value: 23, fill: '#ef4444' },
  { name: '503 Недоступен', value: 15, fill: '#f59e0b' },
  { name: '408 Таймаут', value: 34, fill: '#f97316' },
];