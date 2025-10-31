
import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardView from './components/views/DashboardView';
import TicketsView from './components/views/TicketsView';
import RagManagementView from './components/views/RagManagementView';
import SettingsView from './components/views/SettingsView';
import { AppView } from './types';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>(AppView.Dashboard);

  const renderView = () => {
    switch (currentView) {
      case AppView.Dashboard:
        return <DashboardView />;
      case AppView.Tickets:
        return <TicketsView />;
      case AppView.RAG:
        return <RagManagementView />;
      case AppView.Settings:
        return <SettingsView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header currentView={currentView} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-900 p-4 sm:p-6 lg:p-8">
          {renderView()}
        </main>
      </div>
    </div>
  );
};

export default App;
   