import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, ReferenceLine } from 'recharts';
import { Card, StatCard } from '../components/Common';
import { QUALITY_METRICS } from '../constants';

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-xl">
          <p className="text-slate-400 text-xs mb-1">{label}</p>
          <p className="text-sm font-mono font-bold text-white">
            {payload[0].value.toFixed(2)} {payload[0].payload?.unit || ''}
          </p>
        </div>
      );
    }
    return null;
  };

export const VoiceQuality: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-500 slide-in-from-bottom-2">
        <div className="flex justify-between items-center">
            <div>
                <h1 className="text-2xl font-bold text-white">Аналитика качества голоса</h1>
                <p className="text-slate-400 text-sm">Детальный анализ задержек, джиттера и потерь пакетов</p>
            </div>
        </div>

        {/* Hero Metric: TTFW */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-1 bg-gradient-to-br from-slate-900 to-slate-800 border-primary-500/20">
                <div className="h-full flex flex-col justify-center items-center py-6 text-center">
                    <h3 className="text-primary-400 font-medium uppercase tracking-widest text-xs mb-2">Time to First Word (TTFW)</h3>
                    <div className="text-6xl font-bold text-white tracking-tighter mb-2">
                        1.24<span className="text-2xl text-slate-500 font-normal ml-1">s</span>
                    </div>
                    <div className="flex items-center gap-2 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                         <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                         <span className="text-emerald-400 text-xs font-medium">Отлично (&lt; 1.5s)</span>
                    </div>
                    <p className="text-slate-500 text-xs mt-6 max-w-[200px]">
                        95-й процентиль. Задержка между окончанием речи пользователя и ответом агента.
                    </p>
                </div>
            </Card>

            <Card className="lg:col-span-2" title="Тренд TTFW (Последние 30 мин)">
                <div className="h-[250px] w-full mt-2">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={QUALITY_METRICS}>
                            <defs>
                                <linearGradient id="colorTtfw" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2}/>
                                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                            <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} domain={[0, 3]} />
                            <ReferenceLine y={1.5} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Цель 1.5s', fill: '#f59e0b', fontSize: 10, position: 'insideTopRight' }} />
                            <Tooltip content={<CustomTooltip />} />
                            <Area 
                                type="monotone" 
                                dataKey="value" 
                                stroke="#22c55e" 
                                strokeWidth={2}
                                fillOpacity={1} 
                                fill="url(#colorTtfw)" 
                                unit="s"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard label="Packet Loss (Потери)" value="0.2%" trend={-0.1} inverseTrend trendLabel="стабильно" />
            <StatCard label="Jitter (Джиттер)" value="12ms" trend={2} inverseTrend trendLabel="незнач. рост" />
            <StatCard label="Round Trip Time (RTT)" value="85ms" trend={-5} inverseTrend trendLabel="улучшение" />
        </div>

        {/* Latency Breakdown Section (Simulating Agent Perf Data here for flow) */}
        <Card title="Детализация задержек (Live)">
             <div className="h-[300px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={QUALITY_METRICS.map(m => ({ ...m, stt: Math.random() * 0.4, llm: Math.random() * 0.8, tts: Math.random() * 0.3 }))}>
                        <CartesianGrid vertical={false} stroke="#334155" opacity={0.3} />
                        <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} unit="s" />
                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                        <Line type="monotone" dataKey="llm" name="Генерация LLM" stroke="#06b6d4" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="stt" name="Транскрипция STT" stroke="#f59e0b" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="tts" name="Синтез TTS" stroke="#a855f7" strokeWidth={2} dot={false} />
                    </LineChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-6 mt-4">
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                        <span className="w-3 h-1 bg-cyan-400 rounded-full"></span> Генерация LLM
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                        <span className="w-3 h-1 bg-amber-500 rounded-full"></span> Транскрипция STT
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                        <span className="w-3 h-1 bg-purple-500 rounded-full"></span> Синтез TTS
                    </div>
                </div>
             </div>
        </Card>
    </div>
  );
};