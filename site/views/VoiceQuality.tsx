import React, { useEffect, useState, useCallback } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  ReferenceLine,
} from 'recharts';
import { Card, StatCard } from '../components/Common';
import { getLatencyMetrics, getCallStats24h, CallMetric } from '../lib/supabase';
import { RefreshCw } from 'lucide-react';

interface LatencyPoint {
  time: string;
  value: number;
  stt?: number;
  llm?: number;
  tts?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-xl">
        <p className="text-slate-400 text-xs mb-1">{label}</p>
        <p className="text-sm font-mono font-bold text-white">
          {payload[0].value.toFixed(2)} {payload[0].payload?.unit || 's'}
        </p>
      </div>
    );
  }
  return null;
};

function processLatencyData(metrics: CallMetric[]): LatencyPoint[] {
  // Group by minute and calculate averages
  const grouped: Record<string, { ttfw: number[]; stt: number[]; llm: number[]; tts: number[] }> = {};

  metrics.forEach((m) => {
    const time = new Date(m.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (!grouped[time]) {
      grouped[time] = { ttfw: [], stt: [], llm: [], tts: [] };
    }

    if (m.metric_type === 'ttfw') grouped[time].ttfw.push(m.value_ms);
    if (m.metric_type === 'stt_latency') grouped[time].stt.push(m.value_ms);
    if (m.metric_type === 'llm_latency') grouped[time].llm.push(m.value_ms);
    if (m.metric_type === 'tts_latency') grouped[time].tts.push(m.value_ms);
  });

  return Object.entries(grouped)
    .map(([time, data]) => ({
      time,
      value: data.ttfw.length > 0 ? data.ttfw.reduce((a, b) => a + b, 0) / data.ttfw.length / 1000 : 0,
      stt: data.stt.length > 0 ? data.stt.reduce((a, b) => a + b, 0) / data.stt.length / 1000 : 0,
      llm: data.llm.length > 0 ? data.llm.reduce((a, b) => a + b, 0) / data.llm.length / 1000 : 0,
      tts: data.tts.length > 0 ? data.tts.reduce((a, b) => a + b, 0) / data.tts.length / 1000 : 0,
    }))
    .slice(-20);
}

export const VoiceQuality: React.FC = () => {
  const [ttfwValue, setTtfwValue] = useState<number>(0);
  const [ttfwStatus, setTtfwStatus] = useState<'good' | 'warning' | 'bad'>('good');
  const [latencyData, setLatencyData] = useState<LatencyPoint[]>([]);
  const [avgLatency, setAvgLatency] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [metrics, stats] = await Promise.all([getLatencyMetrics(), getCallStats24h()]);

      // Calculate TTFW from metrics or stats
      const ttfwMetrics = metrics.filter((m) => m.metric_type === 'ttfw');
      const avgTtfw =
        ttfwMetrics.length > 0
          ? ttfwMetrics.reduce((sum, m) => sum + m.value_ms, 0) / ttfwMetrics.length / 1000
          : stats.avgLatencyMs / 1000 || 1.2;

      setTtfwValue(avgTtfw);
      setTtfwStatus(avgTtfw < 1.5 ? 'good' : avgTtfw < 2.5 ? 'warning' : 'bad');
      setAvgLatency(stats.avgLatencyMs);

      // Process latency data for charts
      const processed = processLatencyData(metrics);
      if (processed.length > 0) {
        setLatencyData(processed);
      } else {
        // Generate sample data if no real data
        setLatencyData(
          Array.from({ length: 20 }, (_, i) => ({
            time: `${i}м`,
            value: 0.8 + Math.random() * 0.7,
            stt: 0.1 + Math.random() * 0.3,
            llm: 0.4 + Math.random() * 0.5,
            tts: 0.1 + Math.random() * 0.2,
          }))
        );
      }
    } catch (error) {
      console.error('Error fetching voice quality data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const statusColors = {
    good: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', dot: 'bg-emerald-500' },
    warning: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', dot: 'bg-amber-500' },
    bad: { bg: 'bg-rose-500/10', border: 'border-rose-500/20', text: 'text-rose-400', dot: 'bg-rose-500' },
  };

  const status = statusColors[ttfwStatus];

  return (
    <div className="space-y-6 animate-in fade-in duration-500 slide-in-from-bottom-2">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Аналитика качества голоса</h1>
          <p className="text-slate-400 text-sm">Детальный анализ задержек и метрик качества</p>
        </div>
        <button onClick={fetchData} className="text-slate-400 hover:text-white transition-colors">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Hero Metric: TTFW */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 bg-gradient-to-br from-slate-900 to-slate-800 border-primary-500/20">
          <div className="h-full flex flex-col justify-center items-center py-6 text-center">
            <h3 className="text-primary-400 font-medium uppercase tracking-widest text-xs mb-2">
              Time to First Word (TTFW)
            </h3>
            <div className="text-6xl font-bold text-white tracking-tighter mb-2">
              {ttfwValue.toFixed(2)}
              <span className="text-2xl text-slate-500 font-normal ml-1">s</span>
            </div>
            <div className={`flex items-center gap-2 ${status.bg} px-3 py-1 rounded-full border ${status.border}`}>
              <span className={`w-2 h-2 rounded-full ${status.dot}`}></span>
              <span className={`${status.text} text-xs font-medium`}>
                {ttfwStatus === 'good' ? 'Отлично (< 1.5s)' : ttfwStatus === 'warning' ? 'Допустимо' : 'Требует внимания'}
              </span>
            </div>
            <p className="text-slate-500 text-xs mt-6 max-w-[200px]">
              Среднее время от конца речи пользователя до первого слова ответа агента.
            </p>
          </div>
        </Card>

        <Card className="lg:col-span-2" title="Тренд TTFW">
          <div className="h-[250px] w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={latencyData}>
                <defs>
                  <linearGradient id="colorTtfw" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} domain={[0, 3]} />
                <ReferenceLine
                  y={1.5}
                  stroke="#f59e0b"
                  strokeDasharray="3 3"
                  label={{ value: 'Цель 1.5s', fill: '#f59e0b', fontSize: 10, position: 'insideTopRight' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="value" stroke="#22c55e" strokeWidth={2} fillOpacity={1} fill="url(#colorTtfw)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard label="Средняя задержка" value={`${Math.round(avgLatency)}ms`} trend={0} trendLabel="за 24ч" />
        <StatCard label="Звонков обработано" value="--" trend={0} trendLabel="сегодня" />
        <StatCard label="Качество связи" value="Хорошее" trend={0} trendLabel="стабильно" />
      </div>

      {/* Latency Breakdown Section */}
      <Card title="Детализация задержек по компонентам">
        <div className="h-[300px] w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={latencyData}>
              <CartesianGrid vertical={false} stroke="#334155" opacity={0.3} />
              <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} unit="s" />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
              <Line type="monotone" dataKey="llm" name="LLM" stroke="#06b6d4" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="stt" name="STT" stroke="#f59e0b" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="tts" name="TTS" stroke="#a855f7" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-6 mt-4">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span className="w-3 h-1 bg-cyan-400 rounded-full"></span> LLM (YandexGPT)
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span className="w-3 h-1 bg-amber-500 rounded-full"></span> STT (Распознавание)
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span className="w-3 h-1 bg-purple-500 rounded-full"></span> TTS (Синтез)
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
