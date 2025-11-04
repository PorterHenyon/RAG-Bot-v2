import React, { createContext, useContext, useState, useEffect } from 'react';
import { isUserAllowed, getAccessDeniedMessage } from '../config/accessControl';

interface DiscordUser {
    id: string;
    username: string;
    discriminator: string;
    avatar: string | null;
    email?: string;
}

interface AuthContextType {
    isAuthenticated: boolean;
    user: DiscordUser | null;
    loginWithDiscord: () => void;
    handleDiscordCallback: (code: string) => Promise<boolean>;
    logout: () => void;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DISCORD_CLIENT_ID = import.meta.env.VITE_DISCORD_CLIENT_ID;
const DISCORD_REDIRECT_URI = import.meta.env.VITE_DISCORD_REDIRECT_URI || window.location.origin + '/callback';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState<DiscordUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check if user is already logged in (from sessionStorage)
    useEffect(() => {
        const storedAuth = sessionStorage.getItem('isAuthenticated');
        const storedUser = sessionStorage.getItem('discordUser');
        
        if (storedAuth === 'true' && storedUser) {
            try {
                const userData = JSON.parse(storedUser);
                setIsAuthenticated(true);
                setUser(userData);
            } catch (error) {
                console.error('Failed to parse stored user data:', error);
                sessionStorage.removeItem('isAuthenticated');
                sessionStorage.removeItem('discordUser');
            }
        }
        setIsLoading(false);
    }, []);

    const loginWithDiscord = () => {
        if (!DISCORD_CLIENT_ID) {
            console.error('Discord Client ID is not configured. Please set VITE_DISCORD_CLIENT_ID in your .env file');
            alert('Discord OAuth is not configured. Please contact the administrator.');
            return;
        }

        const discordAuthUrl = `https://discord.com/api/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&redirect_uri=${encodeURIComponent(DISCORD_REDIRECT_URI)}&response_type=code&scope=identify%20email`;
        window.location.href = discordAuthUrl;
    };

    const handleDiscordCallback = async (code: string): Promise<boolean> => {
        try {
            // In a real application, this should be done on the backend to keep the client secret secure
            // For now, we'll exchange the code for user info directly
            
            // This is a simplified version - in production, you need a backend endpoint
            // that exchanges the code for an access token using your client secret
            console.log('Received Discord code:', code);
            
            // For demonstration, we'll create a mock user
            // In production, replace this with actual Discord API calls through your backend
            const mockUser: DiscordUser = {
                id: 'demo-' + Date.now(),
                username: 'DiscordUser',
                discriminator: '0000',
                avatar: null,
                email: 'user@discord.com'
            };

            // Check if user is allowed to access the dashboard
            if (!isUserAllowed(mockUser.id)) {
                alert(getAccessDeniedMessage());
                console.warn('Access denied for user:', mockUser.id);
                return false;
            }

            setIsAuthenticated(true);
            setUser(mockUser);
            sessionStorage.setItem('isAuthenticated', 'true');
            sessionStorage.setItem('discordUser', JSON.stringify(mockUser));
            
            return true;
        } catch (error) {
            console.error('Discord OAuth callback failed:', error);
            return false;
        }
    };

    const logout = () => {
        setIsAuthenticated(false);
        setUser(null);
        sessionStorage.removeItem('isAuthenticated');
        sessionStorage.removeItem('discordUser');
        sessionStorage.removeItem('discord_access_token');
    };

    return (
        <AuthContext.Provider value={{ 
            isAuthenticated, 
            user, 
            loginWithDiscord, 
            handleDiscordCallback,
            logout,
            isLoading 
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

