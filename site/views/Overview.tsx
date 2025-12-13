import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell 
} from 'recharts';
import { StatCard, Card, StatusBadge } from '../components/Common';
import { ALERTS, SERVICES, CALL_VOLUME, ERROR_DISTRIBUTION } from '../constants';
import { AlertCircle, CheckCircle2, Clock, Activity } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 p-3 rounded shadow-xl">
        <p className="text-slate-300 text-xs mb-1">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }} className="text-sm font-bold">
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const Overview: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Обзор системы</h1>
          <p className="text-slate-400 text-sm">Мониторинг голосовой AI платформы в реальном времени</p>
        </div>
        <div className="flex items-center gap-3">
            <span className="flex items-center gap-2 text-sm text-slate-400 bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-700">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                Все системы в норме
            </span>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          label="Активные звонки" 
          value={342} 
          trend={12} 
          trendLabel="к прошлому часу" 
        />
        <StatCard 
          label="TTFW (Среднее)" 
          value="1.2s" 
          trend={-5} 
          trendLabel="улучшение"
          inverseTrend
          subValue="цель &lt; 1.5s"
        />
        <StatCard 
          label="Всего звонков (24ч)" 
          value="12,450" 
          trend={8.5} 
          trendLabel="за вчера"
        />
        <StatCard 
          label="Ср. длительность" 
          value="4m 12s" 
          trend={-2} 
          trendLabel="стабильно"
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2" title="Объем звонков и сбои (24ч)">
          <div className="h-[300px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={CALL_VOLUME}>
                <defs>
                  <linearGradient id="colorCalls" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFailures" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} minTickGap={30} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                    type="monotone" 
                    dataKey="activeCalls" 
                    name="Активные"
                    stroke="#06b6d4" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorCalls)" 
                />
                <Area 
                    type="monotone" 
                    dataKey="failures" 
                    name="Сбои"
                    stroke="#ef4444" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorFailures)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <div className="grid grid-rows-2 gap-6">
            <Card title="Распределение SIP ошибок">
                <div className="h-[140px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={ERROR_DISTRIBUTION} layout="vertical" barSize={12}>
                            <XAxis type="number" hide />
                            <YAxis dataKey="name" type="category" width={100} tick={{fill: '#94a3b8', fontSize: 11}} axisLine={false} tickLine={false} />
                            <Tooltip cursor={{fill: 'transparent'}} content={<CustomTooltip />} />
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                {ERROR_DISTRIBUTION.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </Card>

             <Card title="Аптайм (Система)">
                 <div className="flex items-center justify-center h-full pb-4">
                    <div className="relative h-32 w-32 flex items-center justify-center">
                        <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
                            {/* Background Circle */}
                            <path className="text-slate-800" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5" />
                            {/* Value Circle */}
                            <path className="text-primary-400" strokeDasharray="99.9, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
                        </svg>
                        <div className="absolute flex flex-col items-center">
                            <span className="text-2xl font-bold text-white">99.9%</span>
                            <span className="text-xs text-slate-400">В среднем</span>
                        </div>
                    </div>
                 </div>
             </Card>
        </div>
      </div>

      {/* Bottom Row: Status & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Статус сервисов">
          <div className="space-y-4">
            {SERVICES.map((s) => (
              <div key={s.name} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors">
                <div className="flex items-center gap-3">
                  {s.status === 'operational' ? <CheckCircle2 className="text-emerald-400" size={18} /> : <AlertCircle className="text-amber-400" size={18} />}
                  <span className="font-medium text-slate-200">{s.name}</span>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-xs text-slate-500 font-mono">{s.latency}</span>
                    <StatusBadge status={s.status} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Недавние алерты">
          <div className="space-y-4">
            {ALERTS.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 p-3 rounded-lg border border-slate-800/50 bg-slate-800/20">
                <div className={`mt-1 h-2 w-2 rounded-full flex-shrink-0 ${
                    alert.severity === 'critical' ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]' : 
                    alert.severity === 'warning' ? 'bg-amber-500' : 'bg-blue-400'
                }`} />
                <div className="flex-1">
                    <div className="flex justify-between items-start">
                        <h4 className="text-sm font-medium text-slate-200">{alert.service}</h4>
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                            <Clock size={10} /> {alert.timestamp}
                        </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{alert.message}</p>
                </div>
              </div>
            ))}
            <button className="w-full text-center text-xs text-primary-400 hover:text-primary-300 py-2">
                Смотреть все алерты
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};