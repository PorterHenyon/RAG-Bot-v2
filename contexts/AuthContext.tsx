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

        // Request guilds and guilds.members.read scopes to check roles
        const scopes = 'identify email guilds guilds.members.read';
        const discordAuthUrl = `https://discord.com/api/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&redirect_uri=${encodeURIComponent(DISCORD_REDIRECT_URI)}&response_type=code&scope=${encodeURIComponent(scopes)}`;
        window.location.href = discordAuthUrl;
    };

    const handleDiscordCallback = async (code: string): Promise<boolean> => {
        try {
            console.log('Processing Discord OAuth callback...');
            
            // Call backend to exchange code for user info and check roles
            const response = await fetch(`/api/auth-callback?code=${code}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.message || 'Authentication failed');
                console.error('Auth failed:', errorData);
                return false;
            }

            const data = await response.json();
            const user: DiscordUser = data.user;

            setIsAuthenticated(true);
            setUser(user);
            sessionStorage.setItem('isAuthenticated', 'true');
            sessionStorage.setItem('discordUser', JSON.stringify(user));
            
            return true;
        } catch (error) {
            console.error('Discord OAuth callback failed:', error);
            alert('Authentication failed. Please try again.');
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

