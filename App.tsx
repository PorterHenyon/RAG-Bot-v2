import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Login from './components/Login';
import OAuthCallback from './components/OAuthCallback';
import DashboardView from './components/views/DashboardView';
import ForumPostsView from './components/views/ForumPostsView';
import RagManagementView from './components/views/RagManagementView';
import SlashCommandsView from './components/views/SlashCommandsView';
import PlaygroundView from './components/views/PlaygroundView';
import SettingsView from './components/views/SettingsView';
import { AppView } from './types';
import { useAuth } from './contexts/AuthContext';

const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentView, setCurrentView] = useState<AppView>(AppView.Dashboard);
  const [isCallback, setIsCallback] = useState(false);

  useEffect(() => {
    // Check if this is an OAuth callback
    const params = new URLSearchParams(window.location.search);
    if (params.get('code') || params.get('error')) {
      setIsCallback(true);
    }
  }, []);

  const renderView = () => {
    switch (currentView) {
      case AppView.Dashboard:
        return <DashboardView />;
      case AppView.ForumPosts:
        return <ForumPostsView />;
      case AppView.RAG:
        return <RagManagementView />;
      case AppView.SlashCommands:
        return <SlashCommandsView />;
      case AppView.Playground:
        return <PlaygroundView />;
      case AppView.Settings:
        return <SettingsView />;
      default:
        return <DashboardView />;
    }
  };

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="inline-block w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Show OAuth callback screen
  if (isCallback) {
    return <OAuthCallback />;
  }

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

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