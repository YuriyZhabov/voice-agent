import React, { useEffect, useState, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, StatCard } from '../components/Common';
import { getToolStats, getLatencyMetrics, getCallStats24h, CallMetric } from '../lib/supabase';
import { RefreshCw } from 'lucide-react';

interface ToolStat {
  name: string;
  count: number;
  successRate: number;
  avgLatency: number;
}

interface LatencyStackPoint {
  time: string;
  stt: number;
  llm: number;
  tts: number;
}

function processLatencyStack(metrics: CallMetric[]): LatencyStackPoint[] {
  const grouped: Record<string, { stt: number[]; llm: number[]; tts: number[] }> = {};

  metrics.forEach((m) => {
    const time = new Date(m.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (!grouped[time]) {
      grouped[time] = { stt: [], llm: [], tts: [] };
    }
    if (m.metric_type === 'stt_latency') grouped[time].stt.push(m.value_ms);
    if (m.metric_type === 'llm_latency') grouped[time].llm.push(m.value_ms);
    if (m.metric_type === 'tts_latency') grouped[time].tts.push(m.value_ms);
  });

  return Object.entries(grouped)
    .map(([time, data]) => ({
      time,
      stt: data.stt.length > 0 ? Math.round(data.stt.reduce((a, b) => a + b, 0) / data.stt.length) : 0,
      llm: data.llm.length > 0 ? Math.round(data.llm.reduce((a, b) => a + b, 0) / data.llm.length) : 0,
      tts: data.tts.length > 0 ? Math.round(data.tts.reduce((a, b) => a + b, 0) / data.tts.length) : 0,
    }))
    .slice(-24);
}

export const AgentPerformance: React.FC = () => {
  const [toolStats, setToolStats] = useState<ToolStat[]>([]);
  const [latencyStack, setLatencyStack] = useState<LatencyStackPoint[]>([]);
  const [avgLatency, setAvgLatency] = useState(0);
  const [totalToolCalls, setTotalToolCalls] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [tools, metrics, stats] = await Promise.all([
        getToolStats(),
        getLatencyMetrics(),
        getCallStats24h(),
      ]);

      // Tool stats
      const sortedTools = tools.sort((a, b) => b.count - a.count).slice(0, 5);
      setToolStats(sortedTools);
      setTotalToolCalls(tools.reduce((sum, t) => sum + t.count, 0));

      // Latency
      setAvgLatency(stats.avgLatencyMs);

      // Latency stack chart
      const stackData = processLatencyStack(metrics);
      if (stackData.length > 0) {
        setLatencyStack(stackData);
      } else {
        // Sample data if no real data
        setLatencyStack(
          Array.from({ length: 12 }, (_, i) => ({
            time: `${String(i * 2).padStart(2, '0')}:00`,
            stt: 100 + Math.random() * 150,
            llm: 400 + Math.random() * 300,
            tts: 80 + Math.random() * 120,
          }))
        );
      }
    } catch (error) {
      console.error('Error fetching agent performance data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const maxToolCount = toolStats.length > 0 ? Math.max(...toolStats.map((t) => t.count)) : 1;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Производительность агента</h1>
          <p className="text-slate-400 text-sm">Анализ пайплайна LLM и использования инструментов</p>
        </div>
        <button onClick={fetchData} className="text-slate-400 hover:text-white transition-colors">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Ср. задержка ответа"
          value={avgLatency > 0 ? `${avgLatency}ms` : '--'}
          trend={0}
          inverseTrend
        />
        <StatCard label="Вызовов инструментов" value={totalToolCalls.toString()} trend={0} />
        <StatCard
          label="Уникальных tools"
          value={toolStats.length.toString()}
          subValue="активных"
        />
        <StatCard
          label="Успешность tools"
          value={
            toolStats.length > 0
              ? `${Math.round(toolStats.reduce((s, t) => s + t.successRate, 0) / toolStats.length)}%`
              : '--'
          }
          trend={0}
        />
      </div>

      <Card title="Стек задержек пайплайна (по времени)">
        <div className="h-[350px] w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={latencyStack} stackOffset="sign">
              <CartesianGrid vertical={false} stroke="#334155" opacity={0.3} />
              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                minTickGap={30}
              />
              <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} unit="ms" />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                itemStyle={{ color: '#e2e8f0' }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Bar
                dataKey="stt"
                name="STT (Распознавание)"
                stackId="a"
                fill="#f59e0b"
                radius={[0, 0, 0, 0]}
                barSize={12}
              />
              <Bar
                dataKey="llm"
                name="LLM (YandexGPT)"
                stackId="a"
                fill="#06b6d4"
                radius={[0, 0, 0, 0]}
                barSize={12}
              />
              <Bar
                dataKey="tts"
                name="TTS (Синтез)"
                stackId="a"
                fill="#a855f7"
                radius={[4, 4, 0, 0]}
                barSize={12}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Использование инструментов (Топ-5)">
          <div className="space-y-4 mt-2">
            {toolStats.length > 0 ? (
              toolStats.map((tool) => (
                <div key={tool.name} className="group">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300 font-mono truncate max-w-[200px]">{tool.name}</span>
                    <span className="text-slate-500">
                      {tool.count} calls • {Math.round(tool.successRate)}% ok
                    </span>
                  </div>
                  <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full transition-all duration-500 group-hover:bg-primary-400"
                      style={{ width: `${(tool.count / maxToolCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="text-slate-500 text-sm text-center py-8">
                Нет данных о вызовах инструментов
              </div>
            )}
          </div>
        </Card>

        <Card title="Средняя задержка по tools">
          <div className="space-y-4 mt-2">
            {toolStats.length > 0 ? (
              toolStats.map((tool) => (
                <div key={tool.name} className="flex justify-between items-center">
                  <span className="text-slate-300 font-mono text-sm truncate max-w-[180px]">
                    {tool.name}
                  </span>
                  <div className="flex items-center gap-2">
                    <div
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        tool.avgLatency < 500
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : tool.avgLatency < 1000
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {tool.avgLatency}ms
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-slate-500 text-sm text-center py-8">
                Нет данных о задержках
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
