import React, { useEffect, useState, useCallback } from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell 
} from 'recharts';
import { StatCard, Card, StatusBadge } from '../components/Common';
import { ERROR_DISTRIBUTION } from '../constants';
import { AlertCircle, CheckCircle2, Clock, RefreshCw } from 'lucide-react';
import { 
  getCallStats24h, 
  getActiveCalls, 
  getCallsToday, 
  subscribeToNewCalls,
  Call 
} from '../lib/supabase';
import { getTargetsHealth, formatServiceName } from '../lib/prometheus';

interface CallVolumePoint {
  time: string;
  activeCalls: number;
  failures: number;
}

interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  service: string;
  message: string;
  timestamp: string;
}

interface ServiceStatus {
  name: string;
  status: 'operational' | 'degraded' | 'down';
  latency: string;
  instance: string;
}

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

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

function generateCallVolumeData(calls: Call[]): CallVolumePoint[] {
  const now = new Date();
  const hourlyData: Record<string, { active: number; failed: number }> = {};
  
  // Initialize 24 hours
  for (let i = 23; i >= 0; i--) {
    const t = new Date(now.getTime() - i * 3600000);
    const key = t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    hourlyData[key] = { active: 0, failed: 0 };
  }
  
  // Aggregate calls by hour
  calls.forEach(call => {
    const callTime = new Date(call.start_time);
    const key = callTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (hourlyData[key]) {
      if (call.status === 'failed') {
        hourlyData[key].failed++;
      } else {
        hourlyData[key].active++;
      }
    }
  });
  
  return Object.entries(hourlyData).map(([time, data]) => ({
    time,
    activeCalls: data.active,
    failures: data.failed,
  }));
}

export const Overview: React.FC = () => {
  const [activeCalls, setActiveCalls] = useState<number>(0);
  const [totalCalls24h, setTotalCalls24h] = useState<number>(0);
  const [avgDuration, setAvgDuration] = useState<string>('0m 0s');
  const [avgLatency, setAvgLatency] = useState<string>('--');
  const [callVolumeData, setCallVolumeData] = useState<CallVolumePoint[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [systemUptime, setSystemUptime] = useState<number>(99.9);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchData = useCallback(async () => {
    try {
      const [activeCallsData, stats, todayCalls, targets] = await Promise.all([
        getActiveCalls(),
        getCallStats24h(),
        getCallsToday(),
        getTargetsHealth(),
      ]);

      setActiveCalls(activeCallsData.length);
      setTotalCalls24h(stats.totalCalls);
      setAvgDuration(formatDuration(stats.avgDurationSeconds));
      setAvgLatency(stats.avgLatencyMs > 0 ? `${(stats.avgLatencyMs / 1000).toFixed(1)}s` : '--');
      setCallVolumeData(generateCallVolumeData(todayCalls));
      
      // Process Prometheus targets into services
      const serviceList: ServiceStatus[] = targets
        .filter(t => t.job !== 'prometheus') // Skip prometheus self
        .map(t => ({
          name: formatServiceName(t.instance),
          status: t.health === 'up' ? 'operational' : 'down',
          latency: t.lastError ? 'error' : 'ok',
          instance: t.instance,
        }));
      
      // Add unique services only
      const uniqueServices = serviceList.reduce((acc, s) => {
        if (!acc.find(x => x.name === s.name)) {
          acc.push(s);
        }
        return acc;
      }, [] as ServiceStatus[]);
      
      setServices(uniqueServices.length > 0 ? uniqueServices : [
        { name: 'LiveKit Server', status: 'operational', latency: '--', instance: '' },
        { name: 'Voice Agent', status: 'operational', latency: '--', instance: '' },
        { name: 'SIP Gateway', status: 'operational', latency: '--', instance: '' },
      ]);
      
      // Calculate uptime from healthy services
      const upCount = targets.filter(t => t.health === 'up').length;
      const totalCount = targets.length || 1;
      setSystemUptime(Math.round((upCount / totalCount) * 1000) / 10);
      
      // Generate alerts from failed services and calls
      const serviceAlerts: Alert[] = targets
        .filter(t => t.health === 'down')
        .map((t, i) => ({
          id: `svc-${i}`,
          severity: 'critical' as const,
          service: formatServiceName(t.instance),
          message: t.lastError || 'Сервис недоступен',
          timestamp: new Date(t.lastScrape).toLocaleTimeString(),
        }));
      
      const callAlerts: Alert[] = todayCalls
        .filter(c => c.status === 'failed')
        .slice(0, 2)
        .map((c) => ({
          id: c.id,
          severity: 'warning' as const,
          service: 'Voice Agent',
          message: `Звонок ${c.phone_number} завершился с ошибкой`,
          timestamp: new Date(c.start_time).toLocaleTimeString(),
        }));
      
      const allAlerts = [...serviceAlerts, ...callAlerts].slice(0, 4);
      
      if (allAlerts.length === 0) {
        setAlerts([{
          id: '1',
          severity: 'info',
          service: 'Система',
          message: 'Нет активных алертов',
          timestamp: 'сейчас',
        }]);
      } else {
        setAlerts(allAlerts);
      }
      
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    
    // Poll every 10 seconds
    const interval = setInterval(fetchData, 10000);
    
    // Subscribe to realtime updates
    const subscription = subscribeToNewCalls((call) => {
      if (call.status === 'active') {
        setActiveCalls(prev => prev + 1);
      } else {
        fetchData(); // Refresh all data on call completion
      }
    });
    
    return () => {
      clearInterval(interval);
      subscription.unsubscribe();
    };
  }, [fetchData]);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Обзор системы</h1>
          <p className="text-slate-400 text-sm">Мониторинг голосовой AI платформы в реальном времени</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={fetchData}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
            title="Обновить данные"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
          <span className="text-xs text-slate-500">
            Обновлено: {lastUpdate.toLocaleTimeString()}
          </span>
          <span className="flex items-center gap-2 text-sm text-slate-400 bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-700">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            {activeCalls > 0 ? `${activeCalls} активных` : 'Все системы в норме'}
          </span>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          label="Активные звонки" 
          value={activeCalls} 
          trend={0} 
          trendLabel="сейчас" 
        />
        <StatCard 
          label="TTFW (Среднее)" 
          value={avgLatency}
          trend={0} 
          trendLabel="цель < 1.5s"
          inverseTrend
        />
        <StatCard 
          label="Всего звонков (24ч)" 
          value={totalCalls24h.toLocaleString()} 
          trend={0} 
          trendLabel="за сутки"
        />
        <StatCard 
          label="Ср. длительность" 
          value={avgDuration} 
          trend={0} 
          trendLabel="среднее"
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2" title="Объем звонков и сбои (24ч)">
          <div className="h-[300px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={callVolumeData}>
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
                  name="Звонки"
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
                  <path className="text-slate-800" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5" />
                  <path className={systemUptime >= 99 ? "text-emerald-400" : systemUptime >= 90 ? "text-amber-400" : "text-rose-400"} strokeDasharray={`${systemUptime}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="text-2xl font-bold text-white">{systemUptime}%</span>
                  <span className="text-xs text-slate-400">Сейчас</span>
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
            {services.map((s) => (
              <div key={s.name} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors">
                <div className="flex items-center gap-3">
                  {s.status === 'operational' ? <CheckCircle2 className="text-emerald-400" size={18} /> : <AlertCircle className="text-rose-400" size={18} />}
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
            {alerts.map((alert) => (
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
