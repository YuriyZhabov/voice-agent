import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, StatCard } from '../components/Common';
import { LATENCY_HISTORY } from '../constants';

export const AgentPerformance: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
        <div className="flex justify-between items-center">
            <div>
                <h1 className="text-2xl font-bold text-white">Производительность агента</h1>
                <p className="text-slate-400 text-sm">Анализ пайплайна LLM и использования инструментов</p>
            </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
             <StatCard label="Ср. задержка ответа" value="980ms" trend={5} inverseTrend />
             <StatCard label="Ходов диалога / мин" value="145" trend={12} />
             <StatCard label="Вызовы инструментов" value="34%" subValue="от всех ходов" />
             <StatCard label="Оценка Sentiment" value="8.4" subValue="/ 10" trend={2} />
        </div>

        <Card title="Стек задержек пайплайна (2ч)">
            <div className="h-[350px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={LATENCY_HISTORY} stackOffset="sign">
                        <CartesianGrid vertical={false} stroke="#334155" opacity={0.3} />
                        <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} minTickGap={30} />
                        <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} unit="ms" />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                            itemStyle={{ color: '#e2e8f0' }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} />
                        <Bar dataKey="stt" name="STT (Распознавание)" stackId="a" fill="#f59e0b" radius={[0, 0, 0, 0]} barSize={12} />
                        <Bar dataKey="llm" name="LLM (Инференс)" stackId="a" fill="#06b6d4" radius={[0, 0, 0, 0]} barSize={12} />
                        <Bar dataKey="tts" name="TTS (Синтез)" stackId="a" fill="#a855f7" radius={[4, 4, 0, 0]} barSize={12} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Использование инструментов (Топ)">
                <div className="space-y-4 mt-2">
                    {[
                        { name: 'check_order_status', count: 1245, pct: 45 },
                        { name: 'schedule_appointment', count: 832, pct: 30 },
                        { name: 'transfer_agent', count: 412, pct: 15 },
                        { name: 'knowledge_base_search', count: 276, pct: 10 },
                    ].map((tool, i) => (
                        <div key={tool.name} className="group">
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-300 font-mono">{tool.name}</span>
                                <span className="text-slate-500">{tool.count} calls</span>
                            </div>
                            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                                <div 
                                    className="h-full bg-primary-500 rounded-full transition-all duration-500 group-hover:bg-primary-400" 
                                    style={{ width: `${tool.pct}%` }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </Card>

            <Card title="Анализ тональности (Sentiment)">
                 <div className="h-[200px] flex items-center justify-center text-slate-500 text-sm">
                    {/* Placeholder for a sentiment scatter plot or similar */}
                    <div className="text-center">
                        <p>Позитивный: 65%</p>
                        <p>Нейтральный: 30%</p>
                        <p>Негативный: 5%</p>
                        <div className="mt-4 flex gap-1 h-4 w-64 rounded-full overflow-hidden">
                            <div className="w-[65%] bg-emerald-500"></div>
                            <div className="w-[30%] bg-slate-500"></div>
                            <div className="w-[5%] bg-rose-500"></div>
                        </div>
                    </div>
                 </div>
            </Card>
        </div>
    </div>
  );
};