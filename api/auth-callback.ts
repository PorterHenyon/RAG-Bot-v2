import type { VercelRequest, VercelResponse } from '@vercel/node';

const DISCORD_CLIENT_ID = process.env.VITE_DISCORD_CLIENT_ID;
const DISCORD_CLIENT_SECRET = process.env.DISCORD_CLIENT_SECRET;
const DISCORD_REDIRECT_URI = process.env.VITE_DISCORD_REDIRECT_URI;

// Allowed role IDs - users with ANY of these roles can access the dashboard
const ALLOWED_ROLE_IDS = [
    '1422106035337826315', // Staff role
    '1405246916760961125', // Additional authorized role
];

export default async function handler(req: VercelRequest, res: VercelResponse) {
    const { code } = req.query;

    if (!code || typeof code !== 'string') {
        return res.status(400).json({ error: 'No authorization code provided' });
    }

    // If environment variables aren't set, allow access (development mode)
    if (!DISCORD_CLIENT_SECRET || !DISCORD_CLIENT_ID) {
        console.warn('⚠️ DISCORD_CLIENT_SECRET not configured - running in development mode');
        console.warn('⚠️ Add environment variables for production security');
        
        // Return a mock successful response for development
        return res.status(200).json({
            user: {
                id: 'dev-user',
                username: 'DevUser',
                discriminator: '0000',
                avatar: null,
            },
        });
    }

    try {
        // Exchange code for access token
        const tokenResponse = await fetch('https://discord.com/api/oauth2/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                client_id: DISCORD_CLIENT_ID!,
                client_secret: DISCORD_CLIENT_SECRET!,
                grant_type: 'authorization_code',
                code: code,
                redirect_uri: DISCORD_REDIRECT_URI!,
            }),
        });

        if (!tokenResponse.ok) {
            throw new Error('Failed to exchange code for token');
        }

        const tokens = await tokenResponse.json();

        // Get user info
        const userResponse = await fetch('https://discord.com/api/users/@me', {
            headers: {
                Authorization: `Bearer ${tokens.access_token}`,
            },
        });

        if (!userResponse.ok) {
            throw new Error('Failed to fetch user data');
        }

        const user = await userResponse.json();

        // Get user's guild member info (to check roles)
        const guildId = process.env.DISCORD_SERVER_ID;
        if (guildId) {
            const memberResponse = await fetch(
                `https://discord.com/api/users/@me/guilds/${guildId}/member`,
                {
                    headers: {
                        Authorization: `Bearer ${tokens.access_token}`,
                    },
                }
            );

            if (memberResponse.ok) {
                const member = await memberResponse.json();
                
                // Check if user has ANY of the allowed roles
                const hasAllowedRole = member.roles.some((roleId: string) => 
                    ALLOWED_ROLE_IDS.includes(roleId)
                );
                
                if (!hasAllowedRole) {
                    return res.status(403).json({
                        error: 'Access denied',
                        message: 'You must have the Staff role or an authorized role to access this dashboard.',
                    });
                }
            } else {
                return res.status(403).json({
                    error: 'Not a server member',
                    message: 'You must be a member of the Discord server to access this dashboard.',
                });
            }
        }

        // Return user data if authorized
        return res.status(200).json({
            user: {
                id: user.id,
                username: user.username,
                discriminator: user.discriminator,
                avatar: user.avatar,
                email: user.email,
            },
        });

    } catch (error) {
        console.error('Auth callback error:', error);
        return res.status(500).json({ error: 'Authentication failed' });
    }
}

