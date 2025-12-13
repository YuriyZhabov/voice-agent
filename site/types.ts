export interface MetricPoint {
  time: string;
  value: number;
  secondaryValue?: number;
  unit?: string;
}

export interface LatencyData {
  time: string;
  stt: number;
  llm: number;
  tts: number;
  total: number;
}

export interface CallMetric {
  time: string;
  activeCalls: number;
  failures: number;
}

export interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  service: string;
  message: string;
  timestamp: string;
}

export interface ServiceStatus {
  name: string;
  status: 'operational' | 'degraded' | 'down';
  uptime: string;
  latency: string;
}

export enum TimeRange {
  Hour = '1H',
  Day = '24H',
  Week = '7D',
}

export interface SystemHealth {
  cpu: number;
  memory: number;
  disk: number;
  networkIn: number;
  networkOut: number;
}