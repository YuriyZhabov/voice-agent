import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { Overview } from './views/Overview';
import { VoiceQuality } from './views/VoiceQuality';
import { AgentPerformance } from './views/AgentPerformance';
import { CallHistory } from './views/CallHistory';

// Placeholder views for unfinished sections
const PlaceholderView = ({ title }: { title: string }) => (
  <div className="flex flex-col items-center justify-center h-[50vh] text-slate-500">
    <div className="text-6xl mb-4 opacity-20">🚧</div>
    <h2 className="text-xl font-medium text-slate-400">{title}</h2>
    <p className="mt-2 text-sm">Этот раздел находится в разработке.</p>
  </div>
);

const App: React.FC = () => {
  const [activeView, setActiveView] = useState('overview');

  const renderView = () => {
    switch (activeView) {
      case 'overview':
        return <Overview />;
      case 'voice-quality':
        return <VoiceQuality />;
      case 'agent-perf':
        return <AgentPerformance />;
      case 'call-history':
        return <CallHistory />;
      case 'sip':
        return <PlaceholderView title="Детали SIP Телефонии" />;
      case 'settings':
        return <PlaceholderView title="Настройки" />;
      default:
        return <Overview />;
    }
  };

  return (
    <Layout activeView={activeView} onNavigate={setActiveView}>
      {renderView()}
    </Layout>
  );
};

export default App;