import React, { useState } from 'react';
import { 
  Activity, 
  BarChart3, 
  Server, 
  PhoneCall, 
  Settings, 
  Bell, 
  Search,
  User,
  Menu,
  X,
  Mic
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeView: string;
  onNavigate: (view: string) => void;
}

const SidebarItem = ({ 
  icon: Icon, 
  label, 
  active, 
  onClick 
}: { 
  icon: React.ElementType, 
  label: string, 
  active: boolean, 
  onClick: () => void 
}) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
      active 
        ? 'bg-primary-500/10 text-primary-400 border-r-2 border-primary-400' 
        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
    }`}
  >
    <Icon size={20} className={active ? 'text-primary-400' : 'group-hover:text-slate-100'} />
    <span className="font-medium">{label}</span>
  </button>
);

export const Layout: React.FC<LayoutProps> = ({ children, activeView, onNavigate }) => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex font-sans overflow-hidden">
      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-slate-950 border-r border-slate-800 
        transform transition-transform duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <Activity className="text-primary-400 mr-3" size={24} />
          <span className="text-xl font-bold tracking-tight">VoxPulse</span>
        </div>

        <nav className="p-4 space-y-2">
          <SidebarItem 
            icon={BarChart3} 
            label="Обзор системы" 
            active={activeView === 'overview'} 
            onClick={() => { onNavigate('overview'); setSidebarOpen(false); }}
          />
          <SidebarItem 
            icon={Mic} 
            label="Качество голоса" 
            active={activeView === 'voice-quality'} 
            onClick={() => { onNavigate('voice-quality'); setSidebarOpen(false); }}
          />
          <SidebarItem 
            icon={Server} 
            label="Производительность" 
            active={activeView === 'agent-perf'} 
            onClick={() => { onNavigate('agent-perf'); setSidebarOpen(false); }}
          />
          <SidebarItem 
            icon={PhoneCall} 
            label="SIP Телефония" 
            active={activeView === 'sip'} 
            onClick={() => { onNavigate('sip'); setSidebarOpen(false); }}
          />
        </nav>

        <div className="absolute bottom-0 w-full p-4 border-t border-slate-800">
          <SidebarItem 
            icon={Settings} 
            label="Настройки" 
            active={activeView === 'settings'} 
            onClick={() => onNavigate('settings')}
          />
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-4 lg:px-8 z-30 sticky top-0">
          <div className="flex items-center gap-4">
            <button 
              className="lg:hidden text-slate-400 hover:text-white"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={24} />
            </button>
            <div className="relative hidden md:block group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary-400 transition-colors" size={16} />
              <input 
                type="text" 
                placeholder="Поиск метрик, логов, ID звонка..." 
                className="bg-slate-800/50 border border-slate-700 rounded-full pl-10 pr-4 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-all w-64 lg:w-96 placeholder:text-slate-600"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger-400 rounded-full animate-pulse" />
            </button>
            <div className="flex items-center gap-3 pl-4 border-l border-slate-800">
              <div className="text-right hidden sm:block">
                <div className="text-sm font-medium text-slate-200">Администратор</div>
                <div className="text-xs text-slate-500">DevOps Инженер</div>
              </div>
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary-500 to-indigo-500 flex items-center justify-center text-white font-bold text-xs">
                AU
              </div>
            </div>
          </div>
        </header>

        {/* Scrollable Page Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-8 scroll-smooth">
          <div className="max-w-7xl mx-auto w-full">
             {children}
          </div>
        </main>
      </div>
    </div>
  );
};