import React, { useEffect, useState, useCallback } from 'react';
import { Card } from '../components/Common';
import { getRecentCalls, getTranscript, getToolExecutions, Call, Transcript, ToolExecution } from '../lib/supabase';
import { RefreshCw, Phone, PhoneIncoming, PhoneOutgoing, Clock, MessageSquare, Wrench, ChevronDown, ChevronUp, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const statusColors: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
  active: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: <Phone size={14} className="animate-pulse" /> },
  completed: { bg: 'bg-slate-500/20', text: 'text-slate-400', icon: <CheckCircle size={14} /> },
  failed: { bg: 'bg-rose-500/20', text: 'text-rose-400', icon: <XCircle size={14} /> },
  transferred: { bg: 'bg-amber-500/20', text: 'text-amber-400', icon: <AlertCircle size={14} /> },
};

const CallCard: React.FC<{ call: Call }> = ({ call }) => {
  const [expanded, setExpanded] = useState(false);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [tools, setTools] = useState<ToolExecution[]>([]);
  const [loading, setLoading] = useState(false);

  const loadDetails = async () => {
    if (transcripts.length > 0) return;
    setLoading(true);
    try {
      const [t, te] = await Promise.all([
        getTranscript(call.call_id),
        getToolExecutions(call.call_id),
      ]);
      setTranscripts(t);
      setTools(te);
    } catch (e) {
      console.error('Error loading call details:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleExpand = () => {
    if (!expanded) loadDetails();
    setExpanded(!expanded);
  };

  const status = statusColors[call.status] || statusColors.completed;
  const duration = call.duration_seconds 
    ? `${Math.floor(call.duration_seconds / 60)}:${String(call.duration_seconds % 60).padStart(2, '0')}`
    : '--:--';

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
      <div 
        className="p-4 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={handleExpand}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${call.direction === 'inbound' ? 'bg-cyan-500/20' : 'bg-purple-500/20'}`}>
              {call.direction === 'inbound' ? (
                <PhoneIncoming size={18} className="text-cyan-400" />
              ) : (
                <PhoneOutgoing size={18} className="text-purple-400" />
              )}
            </div>
            <div>
              <div className="font-mono text-white">{call.phone_number}</div>
              <div className="text-xs text-slate-500">
                {new Date(call.start_time).toLocaleString('ru-RU')}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-slate-400">
              <Clock size={14} />
              <span className="text-sm font-mono">{duration}</span>
            </div>
            
            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full ${status.bg}`}>
              {status.icon}
              <span className={`text-xs font-medium ${status.text}`}>{call.status}</span>
            </div>
            
            {expanded ? <ChevronUp size={18} className="text-slate-500" /> : <ChevronDown size={18} className="text-slate-500" />}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-slate-700/50 p-4 bg-slate-900/50">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw size={20} className="animate-spin text-slate-500" />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Metrics */}
              {call.metadata?.metrics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-slate-800 rounded p-2">
                    <div className="text-xs text-slate-500">Ходов диалога</div>
                    <div className="text-lg font-bold text-white">{call.metadata.metrics.turn_count || 0}</div>
                  </div>
                  <div className="bg-slate-800 rounded p-2">
                    <div className="text-xs text-slate-500">Ср. задержка</div>
                    <div className="text-lg font-bold text-white">{call.metadata.metrics.avg_latency_ms || 0}ms</div>
                  </div>
                  <div className="bg-slate-800 rounded p-2">
                    <div className="text-xs text-slate-500">LLM токены</div>
                    <div className="text-lg font-bold text-white">{call.metadata.metrics.llm_total_tokens || 0}</div>
                  </div>
                  <div className="bg-slate-800 rounded p-2">
                    <div className="text-xs text-slate-500">TTS символов</div>
                    <div className="text-lg font-bold text-white">{call.metadata.metrics.tts_chars || 0}</div>
                  </div>
                </div>
              )}

              {/* Transcript */}
              {transcripts.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                    <MessageSquare size={14} />
                    <span>Транскрипт ({transcripts.length} сообщений)</span>
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {transcripts.map((t) => (
                      <div
                        key={t.id}
                        className={`p-2 rounded-lg text-sm ${
                          t.role === 'user'
                            ? 'bg-cyan-500/10 border-l-2 border-cyan-500 ml-0 mr-8'
                            : t.role === 'assistant'
                            ? 'bg-purple-500/10 border-l-2 border-purple-500 ml-8 mr-0'
                            : 'bg-slate-700/50 text-slate-500 text-xs'
                        }`}
                      >
                        <div className="flex justify-between items-start gap-2">
                          <span className={t.role === 'user' ? 'text-cyan-300' : t.role === 'assistant' ? 'text-purple-300' : 'text-slate-400'}>
                            {t.content}
                          </span>
                          <span className="text-xs text-slate-600 whitespace-nowrap">
                            {new Date(t.timestamp).toLocaleTimeString('ru-RU')}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tool Executions */}
              {tools.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                    <Wrench size={14} />
                    <span>Вызовы инструментов ({tools.length})</span>
                  </div>
                  <div className="space-y-2">
                    {tools.map((te) => (
                      <div key={te.id} className="bg-slate-800 rounded p-2 text-sm">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${te.success ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                            <span className="font-mono text-amber-400">{te.tool_name}</span>
                          </div>
                          <span className="text-xs text-slate-500">{te.latency_ms}ms</span>
                        </div>
                        <div className="mt-1 text-xs text-slate-500">
                          <span className="text-slate-600">params:</span> {JSON.stringify(te.parameters)}
                        </div>
                        {te.result?.content && (
                          <div className="mt-1 text-xs text-slate-400 truncate">
                            → {te.result.content}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {transcripts.length === 0 && tools.length === 0 && !call.metadata?.metrics && (
                <div className="text-center text-slate-500 py-4">
                  Нет дополнительных данных
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const CallHistory: React.FC = () => {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed' | 'failed'>('all');

  const fetchCalls = useCallback(async () => {
    try {
      const data = await getRecentCalls(50);
      setCalls(data);
    } catch (e) {
      console.error('Error fetching calls:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCalls();
    const interval = setInterval(fetchCalls, 30000);
    return () => clearInterval(interval);
  }, [fetchCalls]);

  const filteredCalls = filter === 'all' ? calls : calls.filter((c) => c.status === filter);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">История звонков</h1>
          <p className="text-slate-400 text-sm">Детальная информация о каждом звонке</p>
        </div>
        <button onClick={fetchCalls} className="text-slate-400 hover:text-white transition-colors">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(['all', 'active', 'completed', 'failed'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-primary-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            {f === 'all' ? 'Все' : f === 'active' ? 'Активные' : f === 'completed' ? 'Завершённые' : 'Ошибки'}
            {f !== 'all' && (
              <span className="ml-1.5 text-xs opacity-70">
                ({calls.filter((c) => c.status === f).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Call List */}
      <div className="space-y-3">
        {filteredCalls.length > 0 ? (
          filteredCalls.map((call) => <CallCard key={call.id} call={call} />)
        ) : (
          <Card>
            <div className="text-center py-12 text-slate-500">
              {loading ? 'Загрузка...' : 'Нет звонков'}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};
