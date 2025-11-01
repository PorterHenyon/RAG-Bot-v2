
import React from 'react';
import { AppView } from '../types';

interface HeaderProps {
    currentView: AppView;
}

const Header: React.FC<HeaderProps> = ({ currentView }) => {
    return (
        <header className="bg-gray-800 shadow-md p-4">
            <h1 className="text-2xl font-semibold text-white">{currentView}</h1>
        </header>
    );
};

export default Header;