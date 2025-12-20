import React from 'react';
import { AppView } from '../types';
import { BotIcon, DashboardIcon, ForumIcon, DatabaseIcon, CogIcon, BeakerIcon, TerminalIcon } from './icons';

interface SidebarProps {
  currentView: AppView;
  setCurrentView: (view: AppView) => void;
  isOpen: boolean;
  onClose: () => void;
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
      className={`flex items-center p-3 my-1 rounded-xl cursor-pointer transition-all duration-300 ${
        isActive 
          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-500/50 scale-105' 
          : 'text-gray-400 hover:bg-gray-700/50 hover:text-white hover:scale-105'
      }`}
    >
      {icon}
      <span className="mx-4 font-medium">{label}</span>
    </li>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView, isOpen, onClose }) => {
  const navItems = [
    { view: AppView.Dashboard, label: 'Dashboard', icon: <DashboardIcon className="w-6 h-6" /> },
    { view: AppView.ForumPosts, label: 'Forum Posts', icon: <ForumIcon className="w-6 h-6" /> },
    { view: AppView.RAG, label: 'RAG Management', icon: <DatabaseIcon className="w-6 h-6" /> },
    { view: AppView.SlashCommands, label: 'Slash Commands', icon: <TerminalIcon className="w-6 h-6" /> },
    { view: AppView.Playground, label: 'Playground', icon: <BeakerIcon className="w-6 h-6" /> },
    { view: AppView.Settings, label: 'Settings', icon: <CogIcon className="w-6 h-6" /> },
  ];

  const handleNavClick = (view: AppView) => {
    setCurrentView(view);
    onClose(); // Close sidebar on mobile after selection
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 flex-shrink-0 bg-gradient-to-b from-gray-800 to-gray-900 p-4 flex flex-col justify-between
        transform transition-transform duration-300 ease-in-out border-r border-gray-700
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
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
                onClick={() => handleNavClick(item.view)}
              />
            ))}
          </ul>
        </nav>
      </div>
      <div className="text-center text-xs text-gray-500">
        <p>Made by Yukon 2025</p>
      </div>
    </aside>
    </>
  );
};

export default Sidebar;