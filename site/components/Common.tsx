import React from 'react';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

export const Card: React.FC<{ children: React.ReactNode; className?: string; title?: string; action?: React.ReactNode }> = ({ 
  children, 
  className = "", 
  title,
  action
}) => (
  <div className={`bg-slate-900/50 border border-slate-800 rounded-xl backdrop-blur-sm p-5 ${className}`}>
    {(title || action) && (
      <div className="flex justify-between items-center mb-4">
        {title && <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">{title}</h3>}
        {action && <div>{action}</div>}
      </div>
    )}
    {children}
  </div>
);

interface StatProps {
  label: string;
  value: string | number;
  trend?: number;
  trendLabel?: string;
  inverseTrend?: boolean; // If true, up is bad (e.g. latency)
  subValue?: string;
}

export const StatCard: React.FC<StatProps> = ({ label, value, trend, trendLabel, inverseTrend, subValue }) => {
  const isPositive = trend && trend > 0;
  // Determine color based on "good" direction
  let trendColor = 'text-slate-500';
  let Icon = Minus;
  
  if (trend !== undefined && trend !== 0) {
    Icon = isPositive ? ArrowUp : ArrowDown;
    if (inverseTrend) {
        trendColor = isPositive ? 'text-danger-400' : 'text-success-400';
    } else {
        trendColor = isPositive ? 'text-success-400' : 'text-danger-400';
    }
  }

  return (
    <Card>
      <div className="flex flex-col h-full justify-between">
        <span className="text-slate-400 text-sm font-medium">{label}</span>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-3xl lg:text-4xl font-bold text-slate-100 tracking-tight">{value}</span>
          {subValue && <span className="text-slate-500 text-sm">{subValue}</span>}
        </div>
        {trend !== undefined && (
          <div className={`mt-2 flex items-center text-xs font-medium ${trendColor}`}>
            <Icon size={14} className="mr-1" />
            <span>{Math.abs(trend)}%</span>
            {trendLabel && <span className="text-slate-500 ml-1 font-normal">{trendLabel}</span>}
          </div>
        )}
      </div>
    </Card>
  );
};

export const StatusBadge: React.FC<{ status: 'operational' | 'degraded' | 'down' | 'warning' }> = ({ status }) => {
  const styles = {
    operational: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    degraded: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    down: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  };

  const labels = {
    operational: 'В норме',
    degraded: 'Сбои',
    warning: 'Внимание',
    down: 'Не работает'
  };

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status]} flex items-center gap-1.5 w-fit`}>
      <span className={`w-1.5 h-1.5 rounded-full ${status === 'operational' ? 'bg-emerald-400 animate-pulse' : 'bg-current'}`} />
      {labels[status] || status}
    </span>
  );
};