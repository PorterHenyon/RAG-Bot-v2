import React from 'react';
import { AppView } from '../types';
import { BotIcon, DashboardIcon, ForumIcon, DatabaseIcon, CogIcon, BeakerIcon } from './icons';

interface SidebarProps {
  currentView: AppView;
  setCurrentView: (view: AppView) => void;
}

const NavItem: React.FC<{
  view: AppView;
  label: string;
  icon: React.ReactNode;
  isActive: boolean;
  onClick: () => void;
}> = ({ view, label, icon, isActive, onClick }) => {
  return (
    <li
      key={view}
      onClick={onClick}
      className={`flex items-center p-3 my-1 rounded-lg cursor-pointer transition-colors duration-200 ${
        isActive ? 'bg-primary-500 text-white' : 'text-gray-400 hover:bg-gray-700 hover:text-white'
      }`}
    >
      {icon}
      <span className="mx-4 font-medium">{label}</span>
    </li>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView }) => {
  const navItems = [
    { view: AppView.Dashboard, label: 'Dashboard', icon: <DashboardIcon className="w-6 h-6" /> },
    { view: AppView.ForumPosts, label: 'Forum Posts', icon: <ForumIcon className="w-6 h-6" /> },
    { view: AppView.RAG, label: 'RAG Management', icon: <DatabaseIcon className="w-6 h-6" /> },
    { view: AppView.Playground, label: 'Playground', icon: <BeakerIcon className="w-6 h-6" /> },
    { view: AppView.Settings, label: 'Settings', icon: <CogIcon className="w-6 h-6" /> },
  ];

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-800 p-4 flex flex-col justify-between">
      <div>
        <div className="flex items-center mb-8">
          <BotIcon className="w-10 h-10 text-primary-500" />
          <h1 className="text-xl font-bold ml-3 text-white">Support Bot</h1>
        </div>
        <nav>
          <ul>
            {navItems.map((item) => (
              <NavItem
                key={item.view}
                view={item.view}
                label={item.label}
                icon={item.icon}
                isActive={currentView === item.view}
                onClick={() => setCurrentView(item.view)}
              />
            ))}
          </ul>
        </nav>
      </div>
      <div className="text-center text-xs text-gray-500">
        <p>&copy; 2024 Support Bot Inc.</p>
        <p>Version 1.1.0</p>
      </div>
    </aside>
  );
};

export default Sidebar;
